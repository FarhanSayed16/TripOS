from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
import uuid

from app.db.session import get_db
from app.models.tenancy import User
from app.api.deps import require_active_org
from app.models.commercial import Booking, Quote
from app.models.enums import BookingStatus
from app.schemas.bookings import (
    BookingResponse,
    BookingQuoteSummary,
    failure_label,
)
from app.schemas.servicing import (
    BookingChangeResponse,
    ReissueQuoteRequest,
    ReissueConfirmRequest,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _to_booking_response(booking: Booking) -> BookingResponse:
    quote = booking.quote
    customer_name = "Unknown Customer"
    total_price = None
    quote_status = None
    if quote:
        quote_status = quote.status.value if hasattr(quote.status, "value") else str(quote.status)
        if quote.customer:
            customer_name = (
                f"{quote.customer.first_name} {quote.customer.last_name}".strip()
                or customer_name
            )
        if quote.items:
            total_price = sum(item.customer_total for item in quote.items)

    reason = booking.failure_reason.value if booking.failure_reason else None
    needs_support = booking.status == BookingStatus.failed

    return BookingResponse(
        id=booking.id,
        quote_id=booking.quote_id,
        status=booking.status,
        supplier_pnr=booking.supplier_pnr,
        failure_reason=reason,
        failure_label=failure_label(reason),
        needs_manual_support=needs_support,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        quote=BookingQuoteSummary(
            id=quote.id if quote else booking.quote_id,
            customer_name=customer_name,
            total_price=total_price,
            currency="INR",
            status=quote_status,
        ),
    )


@router.get("/export/csv")
async def api_export_bookings_csv(
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Export all bookings for the active organization as CSV."""
    from app.services.bookings import export_bookings_csv

    return await export_bookings_csv(current_user, db)


@router.get("", response_model=List[BookingResponse])
async def list_bookings(
    status: Optional[BookingStatus] = None,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """List bookings for the organization (with customer summary for list UI)."""
    stmt = (
        select(Booking)
        .join(Quote)
        .options(
            selectinload(Booking.quote).selectinload(Quote.customer),
            selectinload(Booking.quote).selectinload(Quote.items),
        )
        .where(Quote.organization_id == current_user.active_organization_id)
        .order_by(desc(Booking.created_at))
    )

    if status:
        stmt = stmt.where(Booking.status == status)

    bookings = (await db.execute(stmt)).scalars().all()
    return [_to_booking_response(b) for b in bookings]


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Booking)
        .join(Quote)
        .options(
            selectinload(Booking.quote).selectinload(Quote.customer),
            selectinload(Booking.quote).selectinload(Quote.items),
        )
        .where(
            Booking.id == booking_id,
            Quote.organization_id == current_user.active_organization_id,
        )
    )
    booking = (await db.execute(stmt)).scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return _to_booking_response(booking)


@router.post("/{booking_id}/changes/quote", response_model=BookingChangeResponse)
async def api_quote_reissue(
    booking_id: uuid.UUID,
    payload: ReissueQuoteRequest,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """FC Phase 7 — quote a post-booking change (reissue/exchange)."""
    from app.services.reissue import quote_reissue

    return await quote_reissue(booking_id, payload, current_user, db)


@router.post("/changes/{change_id}/confirm", response_model=BookingChangeResponse)
async def api_confirm_reissue(
    change_id: uuid.UUID,
    payload: ReissueConfirmRequest,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """FC Phase 7 — confirm a quoted change (or mark manual SOP)."""
    from app.services.reissue import confirm_reissue

    return await confirm_reissue(change_id, payload, current_user, db)


@router.get("/{booking_id}/changes", response_model=List[BookingChangeResponse])
async def api_list_booking_changes(
    booking_id: uuid.UUID,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    from app.services.reissue import list_booking_changes

    return await list_booking_changes(booking_id, current_user, db)
