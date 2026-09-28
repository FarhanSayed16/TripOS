from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid

from app.schemas.quotes import (
    QuoteCreate, 
    QuoteResponse, 
    QuotePassengerUpdate,
    WhatsAppPreviewResponse,
    QuoteSendRequest
)
from app.schemas.payments import PaymentResponse
from app.api.deps import require_active_org, get_db
from app.models.tenancy import User
from app.models.commercial import Quote, QuoteItem, QuotePassenger, Message, Booking
from app.services.quotes import create_quote, update_quote_passengers, mark_quote_ready
from app.services.messaging import generate_whatsapp_preview, send_quote_message
from app.services.payments import create_payment_for_quote
from app.services.inventory import cancel_booking
from app.core.config import settings

router = APIRouter(prefix="/quotes", tags=["quotes"])

@router.post("", response_model=QuoteResponse)
async def api_create_quote(
    quote_in: QuoteCreate,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Create a new quote from inventory snapshots."""
    quote = await create_quote(quote_in, current_user, db)
    from app.services.fx import enrich_quote_items_money

    data = QuoteResponse.model_validate(quote)
    data.items = enrich_quote_items_money(quote)
    return data


@router.get("")
async def api_list_quotes(
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """List quotes for the active organization (paginated). ISSUE-08."""
    from sqlalchemy import func as sqlfunc
    
    filters = [Quote.organization_id == current_user.active_organization_id]
    if status:
        filters.append(Quote.status == status)

    total = (await db.execute(
        select(sqlfunc.count()).select_from(Quote).where(*filters)
    )).scalar_one()

    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.booking),
            selectinload(Quote.items),
            selectinload(Quote.passengers),
        )
        .where(*filters)
        .order_by(Quote.created_at.desc())
        .offset(offset)
        .limit(min(limit, 100))  # Cap at 100 per page
    )
    quotes = (await db.execute(stmt)).scalars().all()
    
    return {"items": quotes, "total": total, "limit": limit, "offset": offset}


@router.get("/{quote_id}", response_model=QuoteResponse)
async def api_get_quote(
    quote_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a full quote by ID (for agents only)."""
    stmt = select(Quote).options(
        selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot),
        selectinload(Quote.passengers),
        selectinload(Quote.booking),
    ).where(
        Quote.id == quote_id,
        Quote.organization_id == current_user.active_organization_id
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    from app.services.fx import enrich_quote_items_money

    data = QuoteResponse.model_validate(quote)
    data.items = enrich_quote_items_money(quote)
    return data


@router.put("/{quote_id}/passengers", response_model=QuoteResponse)
async def api_update_passengers(
    quote_id: str,
    passengers_in: List[QuotePassengerUpdate],
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Update passengers for a quote."""
    return await update_quote_passengers(quote_id, passengers_in, current_user, db)


@router.post("/{quote_id}/ready", response_model=QuoteResponse)
async def api_mark_ready(
    quote_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Mark quote as ready. Will enforce pax gates."""
    return await mark_quote_ready(quote_id, current_user, db)


@router.get("/{quote_id}/whatsapp-preview", response_model=WhatsAppPreviewResponse)
async def api_whatsapp_preview(
    quote_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Generates a WhatsApp preview template for the quote."""
    frontend_url = settings.FRONTEND_URL or (
        settings.BACKEND_CORS_ORIGINS[0] if settings.BACKEND_CORS_ORIGINS else "http://localhost:3000"
    )
    return await generate_whatsapp_preview(quote_id, current_user, db, frontend_url)


@router.post("/{quote_id}/send", response_model=QuoteResponse)
async def api_send_quote(
    quote_id: str,
    payload: QuoteSendRequest,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Logs the message and marks the quote as sent."""
    return await send_quote_message(quote_id, payload.content, payload.channel, current_user, db)


@router.post("/{quote_id}/payment", response_model=PaymentResponse)
async def api_generate_payment(
    quote_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Generates a payment link for the quote via Razorpay."""
    return await create_payment_for_quote(quote_id, current_user, db)

@router.post("/{quote_id}/refresh", response_model=QuoteResponse)
async def api_refresh_quote(
    quote_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Refreshes an expired quote, cloning pax to a new quote with fresh fares."""
    from app.services.quotes import refresh_quote
    return await refresh_quote(quote_id, current_user, db)

@router.post("/{quote_id}/mark-paid-offline", response_model=QuoteResponse)
async def api_mark_quote_paid_offline(
    quote_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Mark a quote as paid via offline methods (NEFT, Cash) bypassing Razorpay."""
    from app.services.payments import mark_quote_paid_offline
    return await mark_quote_paid_offline(quote_id, current_user, db)


@router.post("/{quote_id}/cancel", response_model=QuoteResponse)
async def api_cancel_quote(
    quote_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancels the quote. If booked, attempts to cancel via supplier adapter.
    FIX-P21-02: org-scoped — never cancel another agency's quote.
    """
    from sqlalchemy.orm import selectinload
    from app.models.enums import QuoteStatus, BookingStatus
    from app.services.audit import write_audit
    from app.services.inventory import cancel_booking

    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.booking),
            selectinload(Quote.payment),
            selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot),
        )
        .where(
            Quote.id == quote_id,
            Quote.organization_id == current_user.active_organization_id,
        )
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.status == QuoteStatus.cancelled:
        return quote
        
    if quote.booking and quote.booking.status == BookingStatus.confirmed:
        if quote.items and quote.items[0].offer_snapshot:
            raw_data = quote.items[0].offer_snapshot.offer_data or {}
            supplier_code = raw_data.get("supplier_code", "mock_supplier")
            
            success = await cancel_booking(supplier_code, quote.booking.supplier_pnr)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to cancel supplier booking")
                
        quote.booking.status = BookingStatus.cancelled

    quote.status = QuoteStatus.cancelled

    await write_audit(
        db,
        organization_id=quote.organization_id,
        actor_user_id=current_user.id,
        action="cancel.requested",
        entity_type="quote",
        entity_id=str(quote.id),
        metadata={},
    )

    # FC Phase 2 — if payment was captured, open refund request for ops
    from app.services.refunds import maybe_request_refund_on_cancel

    refund = await maybe_request_refund_on_cancel(
        db, quote, requested_by_user_id=current_user.id
    )

    await db.commit()
    await db.refresh(quote)
    return quote


@router.get("/{quote_id}/fare-rules")
async def api_quote_fare_rules(
    quote_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """FC Phase 2 — fare rules for the first offer on the quote."""
    from sqlalchemy.orm import selectinload
    from app.schemas.inventory import NormalizedOffer
    from app.services.fare_rules import get_fare_rules_for_offer

    stmt = (
        select(Quote)
        .options(selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot))
        .where(
            Quote.id == quote_id,
            Quote.organization_id == current_user.active_organization_id,
        )
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if not quote.items or not quote.items[0].offer_snapshot:
        raise HTTPException(status_code=404, detail="No offer on quote")
    offer = NormalizedOffer.model_validate(quote.items[0].offer_snapshot.offer_data)
    return await get_fare_rules_for_offer(offer)


@router.put("/{quote_id}/items/{item_id}/extras", response_model=QuoteResponse)
async def api_update_item_extras(
    quote_id: str,
    item_id: str,
    body: dict,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """FC Phase 6 — set baggage/meal/seat/SSR lines on a quote item."""
    from app.schemas.ancillaries import QuoteItemExtrasUpdate
    from app.services.ancillaries import update_quote_item_extras
    from app.services.fx import enrich_quote_items_money

    parsed = QuoteItemExtrasUpdate.model_validate(body)
    quote = await update_quote_item_extras(
        quote_id, item_id, parsed, current_user, db
    )
    data = QuoteResponse.model_validate(quote)
    data.items = enrich_quote_items_money(quote)
    return data


@router.get("/{quote_id}/refunds")
async def api_quote_refunds(
    quote_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """FC Phase 2 — refund records for this quote's payment."""
    from app.services.refunds import refunds_for_quote
    from app.schemas.refunds import RefundResponse

    owned = (
        await db.execute(
            select(Quote.id).where(
                Quote.id == quote_id,
                Quote.organization_id == current_user.active_organization_id,
            )
        )
    ).scalar_one_or_none()
    if not owned:
        raise HTTPException(status_code=404, detail="Quote not found")
    rows = await refunds_for_quote(db, quote_id)
    out = []
    for r in rows:
        payload = RefundResponse.model_validate(r).model_dump()
        payload["quote_id"] = quote_id
        out.append(payload)
    return out


@router.get("/{quote_id}/audit")
async def api_get_quote_audit_events(
    quote_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Get audit events for a quote (FIX-P21-01: entity_* columns)."""
    from app.models.commercial import AuditEvent

    # Ensure quote belongs to org (404 if not)
    owned = (
        await db.execute(
            select(Quote.id).where(
                Quote.id == quote_id,
                Quote.organization_id == current_user.active_organization_id,
            )
        )
    ).scalar_one_or_none()
    if not owned:
        raise HTTPException(status_code=404, detail="Quote not found")

    stmt = (
        select(AuditEvent)
        .where(
            AuditEvent.entity_id == str(quote_id),
            AuditEvent.entity_type == "quote",
            AuditEvent.organization_id == current_user.active_organization_id,
        )
        .order_by(AuditEvent.created_at.asc())
    )
    
    events = (await db.execute(stmt)).scalars().all()
    return events
