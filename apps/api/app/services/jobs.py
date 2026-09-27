"""
TripOS outbox job handlers (Phase 20–21).

Booking confirm: revalidate → adapter.book → persist Booking + audit.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from app.models.commercial import Quote, Booking, JobOutbox, QuoteItem
from app.models.enums import QuoteStatus, BookingStatus, JobStatus, BookingFailureReason
from app.services.audit import write_audit

logger = structlog.get_logger()


def _map_failure_reason(code: str) -> BookingFailureReason:
    """Map adapter/error codes onto BookingFailureReason enum."""
    normalized = (code or "").lower().strip()
    if normalized == "timeout":
        normalized = "supplier_timeout"
    try:
        return BookingFailureReason(normalized)
    except ValueError:
        return BookingFailureReason.unknown


async def _upsert_failed_booking(
    db: AsyncSession,
    quote: Quote,
    reason: BookingFailureReason,
) -> Booking:
    supplier_code = None
    for item in getattr(quote, "items", []) or []:
        if item.offer_snapshot and item.offer_snapshot.offer_data:
            supplier_code = item.offer_snapshot.offer_data.get("supplier_code")
            if supplier_code:
                break

    if quote.booking:
        quote.booking.status = BookingStatus.failed
        quote.booking.failure_reason = reason
        quote.booking.supplier_pnr = None
        quote.booking.organization_id = quote.organization_id
        if supplier_code:
            quote.booking.supplier_code = supplier_code
        return quote.booking
    booking = Booking(
        quote_id=quote.id,
        organization_id=quote.organization_id,
        status=BookingStatus.failed,
        failure_reason=reason,
        supplier_code=supplier_code,
    )
    db.add(booking)
    quote.booking = booking
    return booking


async def _enqueue_manual_review(
    db: AsyncSession,
    quote: Quote,
    reason: str,
) -> None:
    db.add(
        JobOutbox(
            type="manual_refund_review",
            payload={
                "quote_id": str(quote.id),
                "payment_id": str(quote.payment.id) if quote.payment else None,
                "reason": reason,
                "needs_manual_support": True,
            },
            status=JobStatus.pending,
            run_at=datetime.now(timezone.utc),
        )
    )


async def mark_booking_confirm_exhausted(
    db: AsyncSession,
    quote_id: str,
) -> None:
    """
    Called when booking_confirm job hits MAX_RETRIES (FIX-P21-04).
    Sets booking failed + supplier_timeout + manual review + audit.
    """
    stmt = (
        select(Quote)
        .options(selectinload(Quote.booking), selectinload(Quote.payment))
        .where(Quote.id == quote_id)
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()
    if not quote:
        return
    if quote.booking and quote.booking.status == BookingStatus.confirmed:
        return

    await _upsert_failed_booking(db, quote, BookingFailureReason.supplier_timeout)
    await _enqueue_manual_review(db, quote, "booking_failed_supplier_timeout")
    await write_audit(
        db,
        organization_id=quote.organization_id,
        action="booking.failed_supplier_timeout",
        entity_type="quote",
        entity_id=str(quote.id),
        metadata={"needs_manual_support": True, "reason": "supplier_timeout"},
    )
    logger.error("booking_confirm_exhausted", quote_id=quote_id)


async def handle_booking_confirm(payload: dict, db: AsyncSession):
    """
    After payment: revalidate → adapter.book → Booking confirmed (or failed_*).

    Raises on transient supplier errors so the worker can retry with backoff.
    Commercial failures (fare_changed, sold_out, missing_pax) complete the job
    as done with a failed Booking row (no retry).
    """
    quote_id = payload.get("quote_id")
    if not quote_id:
        raise ValueError("Missing quote_id in payload")

    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.booking),
            selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot),
            selectinload(Quote.passengers),
            selectinload(Quote.payment),
        )
        .where(Quote.id == quote_id)
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()

    if not quote:
        logger.error("booking_confirm_quote_not_found", quote_id=quote_id)
        return

    if quote.booking and quote.booking.status == BookingStatus.confirmed:
        logger.info("booking_confirm_idempotent_skip", quote_id=quote_id)
        return

    if not quote.passengers:
        logger.error("booking_failed_missing_pax", quote_id=quote_id)
        await _upsert_failed_booking(db, quote, BookingFailureReason.missing_pax)
        await _enqueue_manual_review(db, quote, "booking_failed_missing_pax")
        await write_audit(
            db,
            organization_id=quote.organization_id,
            action="booking.failed_missing_pax",
            entity_type="quote",
            entity_id=str(quote.id),
            metadata={"needs_manual_support": True, "reason": "missing_pax"},
        )
        return

    from app.services.inventory import revalidate_normalized_offer, book_offer
    from app.core.inventory_errors import InventoryRevalidateError
    from app.schemas.inventory import NormalizedOffer

    passenger_dicts = [
        {
            "first_name": p.first_name,
            "last_name": p.last_name,
            "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
            "passport_number": p.passport_number,
        }
        for p in quote.passengers
    ]

    pnr_list: list[str] = []

    # V1: typically one item per quote; sequential book without compensate cancel
    try:
        for item in quote.items:
            if not item.offer_snapshot or not item.offer_snapshot.offer_data:
                continue

            offer_obj = NormalizedOffer.model_validate(item.offer_snapshot.offer_data)

            try:
                await revalidate_normalized_offer(
                    offer_obj,
                    db=db,
                    usage_source="confirm_revalidate",
                    org_id=quote.organization_id,
                )
            except InventoryRevalidateError as e:
                reason_enum = _map_failure_reason(e.error_code)
                logger.error(
                    "booking_failed_revalidate",
                    quote_id=quote_id,
                    reason=reason_enum.value,
                )
                await _upsert_failed_booking(db, quote, reason_enum)
                await _enqueue_manual_review(
                    db, quote, f"booking_failed_{reason_enum.value}"
                )
                await write_audit(
                    db,
                    organization_id=quote.organization_id,
                    action=f"booking.failed_{reason_enum.value}",
                    entity_type="quote",
                    entity_id=str(quote.id),
                    metadata={
                        "needs_manual_support": True,
                        "reason": reason_enum.value,
                        "message": e.message,
                    },
                )
                return

            logger.info("booking_item", quote_id=quote_id, item_id=str(item.id))
            supplier_pnr = await book_offer(
                offer_obj,
                passenger_dicts,
                db=db,
                usage_source="confirm_book",
                org_id=quote.organization_id,
            )
            pnr_list.append(supplier_pnr)

    except InventoryRevalidateError:
        raise
    except Exception as e:
        logger.error("booking_exception", quote_id=quote_id, error=str(e))
        raise

    if not pnr_list:
        await _upsert_failed_booking(db, quote, BookingFailureReason.unknown)
        await _enqueue_manual_review(db, quote, "booking_failed_unknown")
        await write_audit(
            db,
            organization_id=quote.organization_id,
            action="booking.failed_unknown",
            entity_type="quote",
            entity_id=str(quote.id),
            metadata={"needs_manual_support": True, "reason": "no_items_booked"},
        )
        return

    primary_pnr = pnr_list[0]
    # Prefer supplier from first booked offer
    first_offer_code = None
    for item in quote.items:
        if item.offer_snapshot and item.offer_snapshot.offer_data:
            first_offer_code = item.offer_snapshot.offer_data.get("supplier_code")
            if first_offer_code:
                break

    if quote.booking:
        quote.booking.status = BookingStatus.confirmed
        quote.booking.supplier_pnr = primary_pnr
        quote.booking.failure_reason = None
        quote.booking.organization_id = quote.organization_id
        if first_offer_code:
            quote.booking.supplier_code = first_offer_code
        booking_obj = quote.booking
    else:
        booking_obj = Booking(
            quote_id=quote.id,
            organization_id=quote.organization_id,
            status=BookingStatus.confirmed,
            supplier_pnr=primary_pnr,
            supplier_code=first_offer_code,
        )
        db.add(booking_obj)
        quote.booking = booking_obj

    # Create Commission Entry
    from app.services.commissions import create_commission_entry
    from app.services.supplier_usage import record_live_call

    await db.flush() # Ensure booking has ID if newly created
    await create_commission_entry(booking_obj, db)

    if first_offer_code:
        await record_live_call(
            db,
            first_offer_code,
            "confirmed",
            "booking_confirmed",
            org_id=quote.organization_id,
        )

    await write_audit(
        db,
        organization_id=quote.organization_id,
        action="booking.confirmed",
        entity_type="quote",
        entity_id=str(quote.id),
        metadata={"supplier_pnr": primary_pnr, "all_pnrs": pnr_list},
    )
    logger.info("booking_confirm_done", quote_id=quote_id, pnr=primary_pnr)


async def handle_manual_refund_review(payload: dict, db: AsyncSession):
    """Durable ops signal — writes audit_events for operators."""
    quote_id = payload.get("quote_id")
    payment_id = payload.get("payment_id")
    reason = payload.get("reason")

    logger.warning(
        "manual_refund_review_required",
        quote_id=quote_id,
        payment_id=payment_id,
        reason=reason,
    )

    org_id = None
    if quote_id:
        quote = (
            await db.execute(select(Quote).where(Quote.id == quote_id))
        ).scalar_one_or_none()
        if quote:
            org_id = quote.organization_id

    if org_id:
        await write_audit(
            db,
            organization_id=org_id,
            action="payment.manual_refund_review",
            entity_type="payment",
            entity_id=str(payment_id or quote_id or ""),
            metadata={
                "quote_id": quote_id,
                "payment_id": payment_id,
                "reason": reason,
                "needs_manual_support": True,
            },
        )
        await db.flush()
        logger.info("manual_refund_review_audit_written", quote_id=quote_id)


async def handle_followup_reminder(payload: dict, db: AsyncSession):
    """
    Phase 34: System generated followup reminder.
    Currently just a placeholder that logs the action (emails would go here).
    """
    quote_id = payload.get("quote_id")
    hours = payload.get("hours_unpaid")
    logger.info("followup_reminder_processed", quote_id=quote_id, hours_unpaid=hours)


async def expire_stale_quotes(db: AsyncSession):
    """Expire ready/sent quotes past valid_until."""
    stmt = select(Quote).where(
        Quote.status.in_([QuoteStatus.ready, QuoteStatus.sent]),
        Quote.valid_until < datetime.now(timezone.utc),
    )
    stale_quotes = (await db.execute(stmt)).scalars().all()

    expired_count = 0
    for quote in stale_quotes:
        quote.status = QuoteStatus.expired
        expired_count += 1

    if expired_count > 0:
        logger.info("expired_stale_quotes", count=expired_count)
