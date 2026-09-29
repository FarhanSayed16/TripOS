"""FC Phase 7 — reissue / exchange (mock + manual SOP fallback)."""
from __future__ import annotations

import uuid
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.commercial import Booking, Quote
from app.models.enums import BookingStatus
from app.models.servicing import BookingChangeRequest
from app.models.tenancy import User
from app.schemas.servicing import BookingChangeResponse, ReissueConfirmRequest, ReissueQuoteRequest

logger = structlog.get_logger()

MANUAL_SOP_HINT = (
    "Automated reissue is unavailable for this supplier/path. "
    "Use supplier portal / desk SOP: quote change fare → collect difference → "
    "reissue ticket → update PNR notes in TripOS."
)

MOCK_REISSUE_HINT = (
    "Mock reissue only — TripOS records the change request and fee estimate. "
    "It does not update supplier PNR, ticket numbers, or quote totals until a "
    "live reissue API is contracted (Phase 0 matrix)."
)

# Mock supplier price delta for date/route changes (INR paise)
_MOCK_DIFF_BY_TYPE = {
    "date": 150000,  # ₹1,500
    "route": 350000,  # ₹3,500
    "name": 50000,  # ₹500
    "other": 100000,
}


def _to_response(row: BookingChangeRequest) -> BookingChangeResponse:
    if row.manual_sop:
        sop = MANUAL_SOP_HINT
    elif row.status in ("quoted", "awaiting_payment", "confirmed"):
        sop = MOCK_REISSUE_HINT
    else:
        sop = None
    return BookingChangeResponse(
        id=row.id,
        booking_id=row.booking_id,
        organization_id=row.organization_id,
        change_type=row.change_type,
        status=row.status,
        request_payload=row.request_payload or {},
        supplier_diff_paise=row.supplier_diff_paise,
        new_total_paise=row.new_total_paise,
        currency=row.currency or "INR",
        notes=row.notes,
        manual_sop=row.manual_sop,
        created_at=row.created_at,
        updated_at=row.updated_at,
        sop_hint=sop,
    )


async def _load_org_booking(
    booking_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession
) -> Booking:
    stmt = (
        select(Booking)
        .join(Quote)
        .options(selectinload(Booking.quote).selectinload(Quote.items))
        .where(
            Booking.id == booking_id,
            Quote.organization_id == org_id,
        )
    )
    booking = (await db.execute(stmt)).scalar_one_or_none()
    if not booking:
        raise AppError("Booking not found", status_code=404, error_code="BOOKING_NOT_FOUND")
    if booking.status != BookingStatus.confirmed:
        raise AppError(
            "Only confirmed bookings can be changed",
            status_code=400,
            error_code="BOOKING_NOT_CONFIRMED",
        )
    return booking


def _current_total_paise(booking: Booking) -> int:
    quote = booking.quote
    if not quote or not quote.items:
        return 0
    return int(sum(item.customer_total for item in quote.items))


async def quote_reissue(
    booking_id: uuid.UUID,
    payload: ReissueQuoteRequest,
    current_user: User,
    db: AsyncSession,
) -> BookingChangeResponse:
    org_id = current_user.active_organization_id
    if not org_id:
        raise AppError("No active organization", status_code=403)
    booking = await _load_org_booking(booking_id, org_id, db)

    change_type = (payload.change_type or "other").strip().lower()
    if change_type not in _MOCK_DIFF_BY_TYPE:
        change_type = "other"

    # Live reissue only when flag on; otherwise still create manual SOP row
    automated = bool(settings.FC_REISSUE_ENABLED)
    current = _current_total_paise(booking)
    diff = _MOCK_DIFF_BY_TYPE[change_type] if automated else None
    new_total = (current + diff) if (automated and diff is not None) else None

    notes = payload.notes
    if not automated:
        notes = (notes or "") + ("\n" if notes else "") + "FC_REISSUE_ENABLED=false — manual SOP"

    row = BookingChangeRequest(
        id=uuid.uuid4(),
        booking_id=booking.id,
        organization_id=org_id,
        requested_by_user_id=current_user.id,
        change_type=change_type,
        status="manual_sop" if not automated else "quoted",
        request_payload=payload.request_payload or {},
        supplier_diff_paise=diff if automated else None,
        new_total_paise=new_total,
        currency="INR",
        notes=notes,
        manual_sop=not automated,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    logger.info(
        "reissue_quoted",
        booking_id=str(booking_id),
        change_id=str(row.id),
        automated=automated,
        diff_paise=diff,
    )
    return _to_response(row)


async def confirm_reissue(
    change_id: uuid.UUID,
    payload: ReissueConfirmRequest,
    current_user: User,
    db: AsyncSession,
) -> BookingChangeResponse:
    org_id = current_user.active_organization_id
    if not org_id:
        raise AppError("No active organization", status_code=403)

    row = (
        await db.execute(
            select(BookingChangeRequest).where(
                BookingChangeRequest.id == change_id,
                BookingChangeRequest.organization_id == org_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise AppError("Change request not found", status_code=404)

    if payload.force_manual_sop or row.manual_sop:
        row.status = "manual_sop"
        row.manual_sop = True
        await db.commit()
        await db.refresh(row)
        return _to_response(row)

    if row.status not in ("quoted", "awaiting_payment"):
        raise AppError(
            f"Cannot confirm change in status {row.status}",
            status_code=400,
            error_code="INVALID_CHANGE_STATUS",
        )

    diff = int(row.supplier_diff_paise or 0)
    if diff > 0 and not payload.payment_collected:
        row.status = "awaiting_payment"
        await db.commit()
        await db.refresh(row)
        return _to_response(row)

    # Mock confirm — mark confirmed; live adapters would call supplier reissue here
    row.status = "confirmed"
    await db.commit()
    await db.refresh(row)
    logger.info("reissue_confirmed", change_id=str(change_id), booking_id=str(row.booking_id))
    return _to_response(row)


async def list_booking_changes(
    booking_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> list[BookingChangeResponse]:
    org_id = current_user.active_organization_id
    if not org_id:
        raise AppError("No active organization", status_code=403)
    await _load_org_booking(booking_id, org_id, db)
    rows = (
        await db.execute(
            select(BookingChangeRequest)
            .where(
                BookingChangeRequest.booking_id == booking_id,
                BookingChangeRequest.organization_id == org_id,
            )
            .order_by(BookingChangeRequest.created_at.desc())
        )
    ).scalars().all()
    return [_to_response(r) for r in rows]
