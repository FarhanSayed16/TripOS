"""
TripOS outbox worker (Phase 20).

Local:
  cd apps/api
  python worker.py

Render: Background Worker start command:
  python worker.py
  (root directory = apps/api, same DATABASE_URL as the API service)

Requires Postgres. Uses FOR UPDATE SKIP LOCKED so multiple workers
do not claim the same job. Polls jobs_outbox and expires stale quotes.
"""
import asyncio
import uuid
import traceback
import structlog
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import sentry_sdk

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.commercial import JobOutbox
from app.models.enums import JobStatus
from app.services.jobs import (
    handle_booking_confirm,
    handle_manual_refund_review,
    expire_stale_quotes,
    mark_booking_confirm_exhausted,
)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        environment="production" if settings.is_production else "development"
    )

logger = structlog.get_logger("worker")

MAX_RETRIES = 3
# FIX-P21-04: plan backoff 30s → 2min → 10min (indexed by attempts after increment: 1,2,3)
BACKOFF_SCHEDULE = [
    timedelta(seconds=30),
    timedelta(minutes=2),
    timedelta(minutes=10),
]
EXPIRE_EVERY_N_LOOPS = 12  # ~60s if idle sleep is 5s
POLL_IDLE_SECONDS = 5
STALE_RUNNING_MINUTES = 15

HANDLERS = {
    "booking_confirm": handle_booking_confirm,
    "manual_refund_review": handle_manual_refund_review,
}


def _supports_skip_locked() -> bool:
    return settings.DATABASE_URL.startswith("postgresql")


async def reclaim_stale_running(db: AsyncSession) -> int:
    """
    AUDIT-011: If a worker crashes after claiming a job, status stays `running`
    forever. Requeue jobs whose updated_at is older than the lease window.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STALE_RUNNING_MINUTES)
    stmt = select(JobOutbox).where(
        JobOutbox.status == JobStatus.running,
        JobOutbox.updated_at < cutoff,
    )
    if _supports_skip_locked():
        stmt = stmt.with_for_update(skip_locked=True)

    jobs = (await db.execute(stmt)).scalars().all()
    reclaimed = 0
    for job in jobs:
        job.status = JobStatus.pending
        job.error_details = (
            (job.error_details or "")
            + f"\n[reclaimed_stale_running after {STALE_RUNNING_MINUTES}m]"
        )
        job.run_at = datetime.now(timezone.utc)
        reclaimed += 1
        logger.warning("job_reclaimed_stale_running", job_id=str(job.id), type=job.type)
    return reclaimed


async def process_job(db: AsyncSession, job: JobOutbox):
    handler = HANDLERS.get(job.type)
    if not handler:
        logger.error("job_handler_not_found", job_type=job.type, job_id=str(job.id))
        job.status = JobStatus.dead
        job.error_details = "Handler not found"
        return

    try:
        logger.info("job_starting", job_id=str(job.id), type=job.type)
        await handler(job.payload, db)
        job.status = JobStatus.done
        logger.info("job_done", job_id=str(job.id))
    except Exception as e:
        error_msg = str(e)
        error_tb = traceback.format_exc()
        logger.error("job_failed", job_id=str(job.id), error=error_msg)

        job.attempts += 1
        job.error_details = error_tb

        if job.attempts >= MAX_RETRIES:
            job.status = JobStatus.dead
            logger.error("job_dead", job_id=str(job.id))
            if settings.SENTRY_DSN:
                sentry_sdk.capture_message(
                    f"job_dead:{job.type}",
                    level="error",
                )
            if job.type == "booking_confirm":
                quote_id = (job.payload or {}).get("quote_id")
                if quote_id:
                    try:
                        await mark_booking_confirm_exhausted(db, quote_id)
                    except Exception as mark_err:
                        logger.error(
                            "booking_exhaust_mark_failed",
                            job_id=str(job.id),
                            error=str(mark_err),
                        )
        else:
            job.status = JobStatus.pending
            delay = BACKOFF_SCHEDULE[min(job.attempts - 1, len(BACKOFF_SCHEDULE) - 1)]
            job.run_at = datetime.now(timezone.utc) + delay
            logger.info("job_retrying", job_id=str(job.id), next_run=job.run_at, delay=str(delay))


async def poll_outbox(db: AsyncSession) -> bool:
    """Claim one pending job with SKIP LOCKED (Postgres) and process it."""
    now = datetime.now(timezone.utc)

    stmt = (
        select(JobOutbox)
        .where(
            JobOutbox.status == JobStatus.pending,
            JobOutbox.run_at <= now,
        )
        .order_by(JobOutbox.run_at.asc())
        .limit(1)
    )
    if _supports_skip_locked():
        stmt = stmt.with_for_update(skip_locked=True)

    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        return False

    job.status = JobStatus.running
    await db.commit()

    try:
        await process_job(db, job)
    finally:
        await db.commit()

    return True


async def check_unpaid_followups(db: AsyncSession) -> int:
    """
    Phase 34.1: Query quotes where status IN (sent, ready) AND created_at < now - 24h
    AND no followup sent in last 24h. Creates followup_reminder JobOutbox entries.
    """
    from app.models.commercial import Quote, FollowUp
    from app.models.enums import QuoteStatus
    from sqlalchemy import and_, or_, not_, select

    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_48h = now - timedelta(hours=48)
    
    stmt = select(Quote).where(
        Quote.status.in_([QuoteStatus.ready, QuoteStatus.sent]),
        Quote.created_at <= cutoff_24h
    ).options(selectinload(Quote.follow_ups))
    
    quotes = (await db.execute(stmt)).scalars().all()
    jobs_created = 0
    
    for quote in quotes:
        # Check existing followups
        has_24h = any(f.type == "auto_24h" for f in quote.follow_ups)
        has_48h = any(f.type == "auto_48h" for f in quote.follow_ups)
        
        hours_unpaid = 0
        f_type = None
        
        if quote.created_at <= cutoff_48h and not has_48h:
            hours_unpaid = 48
            f_type = "auto_48h"
        elif quote.created_at <= cutoff_24h and not has_24h and quote.created_at > cutoff_48h:
            hours_unpaid = 24
            f_type = "auto_24h"
            
        if f_type:
            # Create FollowUp record
            f_record = FollowUp(
                quote_id=quote.id,
                organization_id=quote.organization_id,
                type=f_type,
                status="pending"
            )
            db.add(f_record)
            
            # Create JobOutbox to actually send it or notify (though Phase 34 says "agent can send reminder")
            # Wait, the task says: "For each, create a JobOutbox entry with type = 'followup_reminder'"
            job = JobOutbox(
                type="followup_reminder",
                payload={"quote_id": str(quote.id), "hours_unpaid": hours_unpaid},
                status=JobStatus.pending,
                run_at=now
            )
            db.add(job)
            jobs_created += 1
            
    return jobs_created

async def check_dead_letter_spike(db: AsyncSession):
    """Phase 39: Alert if > 5 dead jobs in the last 1 hour."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)
    
    stmt = select(JobOutbox).where(
        JobOutbox.status == JobStatus.dead,
        JobOutbox.updated_at >= cutoff
    )
    dead_jobs = (await db.execute(stmt)).scalars().all()
    
    if len(dead_jobs) > 5:
        logger.error("dead_letter_spike", count=len(dead_jobs), timeframe="1h")
        if settings.SENTRY_DSN:
            sentry_sdk.capture_message(f"Dead letter spike: {len(dead_jobs)} jobs failed in last 1 hour", level="error")

import os

def touch_health_file():
    """Simple file touch for health check."""
    try:
        with open("worker_health.tmp", "w") as f:
            f.write(datetime.now(timezone.utc).isoformat())
    except Exception as e:
        logger.error("health_file_touch_failed", error=str(e))

async def worker_loop():
    poll_idle_seconds = getattr(settings, 'WORKER_POLL_INTERVAL_SECONDS', 5)
    
    logger.info(
        "worker_started",
        skip_locked=_supports_skip_locked(),
        payments_mode=settings.PAYMENTS_MODE,
        stale_running_minutes=STALE_RUNNING_MINUTES,
        poll_interval=poll_idle_seconds
    )
    loop_count = 0
    while True:
        try:
            touch_health_file()
            async with AsyncSessionLocal() as db:
                loop_count += 1
                if loop_count % EXPIRE_EVERY_N_LOOPS == 1:
                    await expire_stale_quotes(db)
                    
                    # Phase 34: Check unpaid followups
                    followups_created = await check_unpaid_followups(db)
                    if followups_created:
                        logger.info("unpaid_followups_created", count=followups_created)
                        
                    reclaimed = await reclaim_stale_running(db)
                    if reclaimed:
                        logger.info("stale_running_reclaimed", count=reclaimed)
                        
                    # Phase 39: Check dead letters
                    await check_dead_letter_spike(db)
                        
                    await db.commit()

                job_processed = await poll_outbox(db)
                if not job_processed:
                    await asyncio.sleep(poll_idle_seconds)
        except Exception as e:
            logger.error("worker_loop_error", error=str(e))
            await asyncio.sleep(poll_idle_seconds)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("worker_stopped")
