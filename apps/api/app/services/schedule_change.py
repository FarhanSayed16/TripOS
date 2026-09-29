"""FC Phase 7 — schedule-change ingest + agent notify."""
from __future__ import annotations

import uuid
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.commercial import Booking, Quote
from app.models.servicing import ScheduleChangeEvent
from app.models.tenancy import OrganizationMember, User
from app.schemas.servicing import ScheduleChangeIngest
from app.services.email import send_booking_status_email

logger = structlog.get_logger()


async def ingest_schedule_change(
    payload: ScheduleChangeIngest,
    db: AsyncSession,
) -> ScheduleChangeEvent:
    booking: Optional[Booking] = None
    org_id = payload.organization_id

    if payload.booking_id:
        booking = await db.get(Booking, payload.booking_id)
    elif payload.supplier_pnr:
        stmt = (
            select(Booking)
            .options(selectinload(Booking.quote))
            .where(Booking.supplier_pnr == payload.supplier_pnr)
            .limit(1)
        )
        booking = (await db.execute(stmt)).scalar_one_or_none()

    if booking and booking.quote_id and not org_id:
        quote = booking.quote or await db.get(Quote, booking.quote_id)
        if quote:
            org_id = quote.organization_id

    event = ScheduleChangeEvent(
        id=uuid.uuid4(),
        organization_id=org_id,
        booking_id=booking.id if booking else None,
        supplier_code=payload.supplier_code,
        supplier_pnr=payload.supplier_pnr or (booking.supplier_pnr if booking else None),
        payload={
            "changes": payload.changes or {},
            "message": payload.message,
        },
        notified=False,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    notified = await _notify_org_agents(event, db)
    if notified:
        event.notified = True
        await db.commit()
        await db.refresh(event)

    logger.info(
        "schedule_change_ingested",
        event_id=str(event.id),
        booking_id=str(event.booking_id) if event.booking_id else None,
        notified=event.notified,
    )
    return event


async def _notify_org_agents(event: ScheduleChangeEvent, db: AsyncSession) -> bool:
    if not event.organization_id:
        return False
    stmt = (
        select(User)
        .join(OrganizationMember, OrganizationMember.user_id == User.id)
        .where(OrganizationMember.organization_id == event.organization_id)
        .limit(5)
    )
    users = (await db.execute(stmt)).scalars().all()
    if not users:
        return False

    pnr = event.supplier_pnr or "unknown"
    msg = (event.payload or {}).get("message") or "Schedule change received from supplier."
    subject = f"TripOS schedule change — PNR {pnr}"
    text = (
        f"Schedule change for PNR {pnr}.\n{msg}\n"
        f"Booking: {event.booking_id}\nEvent: {event.id}"
    )
    html = (
        f"<p>Schedule change for PNR <strong>{pnr}</strong>.</p>"
        f"<p>{msg}</p>"
        f"<p>Booking: {event.booking_id}</p>"
    )
    ok = False
    for u in users:
        if u.email:
            sent = await send_booking_status_email(
                u.email, subject=subject, body_html=html, body_text=text
            )
            ok = ok or sent
    return ok
