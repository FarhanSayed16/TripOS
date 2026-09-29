"""FC Phase 8 — Partner / B2C-facing API (API-key auth, no agent JWT)."""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.rate_limit import partner_rate_limiter
from app.models.commercial import Booking, Quote, QuoteItem
from app.models.partner import PartnerApp
from app.models.tenancy import User
from app.schemas.crm import CustomerResponse
from app.schemas.inventory import (
    NormalizedOffer,
    RevalidateRequest,
    SearchQuery,
    SearchResponse,
    InventoryType,
)
from app.schemas.partner import (
    PartnerCustomerCreate,
    PartnerPayLinkResponse,
    PartnerBookingStatus,
)
from app.schemas.quotes import (
    QuoteCreate,
    QuotePassengerUpdate,
    QuoteResponse,
)
from app.services.partner_auth import (
    authenticate_api_key,
    load_partner_service_user,
    require_scope,
)

router = APIRouter(prefix="/partner", tags=["partner"])


async def get_partner_app(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
) -> PartnerApp:
    raw = x_api_key
    if not raw and authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            raw = parts[1].strip()
        elif authorization.startswith("tp_"):
            raw = authorization.strip()
    if not raw:
        raise AppError(
            "Missing API key (X-API-Key or Bearer)",
            status_code=401,
            error_code="PARTNER_UNAUTHORIZED",
        )
    from app.core.rate_limit import client_ip_from_request

    client_ip = client_ip_from_request(request)
    app = await authenticate_api_key(raw, db, client_ip=client_ip)
    await partner_rate_limiter.check(app.id, app.rate_limit_per_minute)
    return app


async def _actor(app: PartnerApp, db: AsyncSession) -> User:
    return await load_partner_service_user(app, db)


@router.get("/me")
async def partner_me(app: PartnerApp = Depends(get_partner_app)):
    """Identity probe for sandbox / Postman."""
    return {
        "partner_app_id": str(app.id),
        "name": app.name,
        "organization_id": str(app.organization_id),
        "env": app.env,
        "scopes": app.scopes,
        "rate_limit_per_minute": app.rate_limit_per_minute,
    }


@router.post("/search/flights", response_model=SearchResponse)
async def partner_search_flights(
    query: SearchQuery,
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "search")
    if query.type != InventoryType.FLIGHT:
        raise AppError("type must be flight", status_code=400)
    from app.services.inventory import search_inventory

    user = await _actor(app, db)
    return await search_inventory(query, user, db, usage_source="partner_search")


@router.post("/search/hotels", response_model=SearchResponse)
async def partner_search_hotels(
    query: SearchQuery,
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "search")
    if query.type != InventoryType.HOTEL:
        raise AppError("type must be hotel", status_code=400)
    from app.services.inventory import search_inventory

    user = await _actor(app, db)
    return await search_inventory(query, user, db, usage_source="partner_search")


@router.post("/revalidate", response_model=NormalizedOffer)
async def partner_revalidate(
    request: RevalidateRequest,
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "search")
    from app.services.inventory import revalidate_offer

    return await revalidate_offer(
        request,
        db=db,
        usage_source="partner_revalidate",
        org_id=app.organization_id,
    )


@router.post("/customers", response_model=CustomerResponse, status_code=201)
async def partner_create_customer(
    data: PartnerCustomerCreate,
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "quote")
    from app.api.customers import normalize_phone
    from app.models.crm import Customer

    user = await _actor(app, db)
    phone_e164 = normalize_phone(data.phone)
    existing = (
        await db.execute(
            select(Customer).where(
                Customer.phone_e164 == phone_e164,
                Customer.organization_id == app.organization_id,
                Customer.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    customer = Customer(
        organization_id=app.organization_id,
        first_name=data.first_name,
        last_name=data.last_name,
        phone_e164=phone_e164,
        email=data.email,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.post("/quotes", response_model=QuoteResponse)
async def partner_create_quote(
    quote_in: QuoteCreate,
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "quote")
    from app.services.quotes import create_quote
    from app.services.fx import enrich_quote_items_money

    user = await _actor(app, db)
    quote = await create_quote(quote_in, user, db)
    data = QuoteResponse.model_validate(quote)
    data.items = enrich_quote_items_money(quote)
    return data


@router.post("/quotes/{quote_id}/passengers", response_model=QuoteResponse)
async def partner_set_passengers(
    quote_id: uuid.UUID,
    passengers: List[QuotePassengerUpdate],
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "quote")
    from app.services.quotes import update_quote_passengers
    from app.services.fx import enrich_quote_items_money

    user = await _actor(app, db)
    quote = await update_quote_passengers(str(quote_id), passengers, user, db)
    data = QuoteResponse.model_validate(quote)
    data.items = enrich_quote_items_money(quote)
    return data


@router.post("/quotes/{quote_id}/ready", response_model=QuoteResponse)
async def partner_mark_ready(
    quote_id: uuid.UUID,
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "quote")
    from app.services.quotes import mark_quote_ready
    from app.services.fx import enrich_quote_items_money

    user = await _actor(app, db)
    quote = await mark_quote_ready(str(quote_id), user, db)
    data = QuoteResponse.model_validate(quote)
    data.items = enrich_quote_items_money(quote)
    return data


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def partner_get_quote(
    quote_id: uuid.UUID,
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "quote")
    from app.services.fx import enrich_quote_items_money

    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot),
            selectinload(Quote.passengers),
            selectinload(Quote.booking),
        )
        .where(
            Quote.id == quote_id,
            Quote.organization_id == app.organization_id,
        )
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()
    if not quote:
        raise AppError("Quote not found", status_code=404, error_code="NOT_FOUND")
    data = QuoteResponse.model_validate(quote)
    data.items = enrich_quote_items_money(quote)
    return data


@router.post("/quotes/{quote_id}/pay-link", response_model=PartnerPayLinkResponse)
async def partner_pay_link(
    quote_id: uuid.UUID,
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "pay")
    from app.services.payments import create_payment_for_quote

    user = await _actor(app, db)
    payment = await create_payment_for_quote(str(quote_id), user, db)
    public_url = None
    quote = await db.get(Quote, quote_id)
    if quote and quote.public_token:
        base = settings.FRONTEND_URL.rstrip("/")
        public_url = f"{base}/q/{quote.public_token}"
    charge = (quote.charge_currency if quote else None) or settings.CHARGE_CURRENCY or "INR"
    return PartnerPayLinkResponse(
        quote_id=quote_id,
        payment_id=payment.id,
        status=payment.status.value if hasattr(payment.status, "value") else str(payment.status),
        amount_paise=payment.amount,
        currency=charge,
        payment_link_url=payment.payment_link_url,
        public_quote_url=public_url,
    )


@router.get("/quotes/{quote_id}/booking", response_model=PartnerBookingStatus)
async def partner_booking_status(
    quote_id: uuid.UUID,
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "booking")
    stmt = (
        select(Quote)
        .options(selectinload(Quote.booking), selectinload(Quote.payment))
        .where(
            Quote.id == quote_id,
            Quote.organization_id == app.organization_id,
        )
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()
    if not quote:
        raise AppError("Quote not found", status_code=404)
    booking = quote.booking
    pay_status = None
    if quote.payment:
        pay_status = (
            quote.payment.status.value
            if hasattr(quote.payment.status, "value")
            else str(quote.payment.status)
        )
    return PartnerBookingStatus(
        quote_id=quote.id,
        booking_id=booking.id if booking else None,
        status=booking.status.value if booking else None,
        supplier_pnr=booking.supplier_pnr if booking else None,
        failure_reason=(
            booking.failure_reason.value
            if booking and booking.failure_reason
            else None
        ),
        payment_status=pay_status,
    )


@router.post("/quotes/{quote_id}/cancel", response_model=QuoteResponse)
async def partner_cancel_quote(
    quote_id: uuid.UUID,
    app: PartnerApp = Depends(get_partner_app),
    db: AsyncSession = Depends(get_db),
):
    require_scope(app, "booking")
    from app.services.booking_cancel import cancel_quote_with_soft_supplier
    from app.services.fx import enrich_quote_items_money
    from app.services.partner_webhooks import dispatch_partner_event

    user = await _actor(app, db)
    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.booking),
            selectinload(Quote.payment),
            selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot),
            selectinload(Quote.passengers),
        )
        .where(
            Quote.id == quote_id,
            Quote.organization_id == app.organization_id,
        )
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()
    if not quote:
        raise AppError("Quote not found", status_code=404)

    result = await cancel_quote_with_soft_supplier(
        db,
        quote,
        actor_user_id=user.id,
        metadata={"source": "partner_api", "partner_app_id": str(app.id)},
    )
    if not result.get("already_cancelled"):
        await db.commit()
        await db.refresh(quote, ["items", "passengers", "booking"])
        await dispatch_partner_event(
            db,
            app.organization_id,
            "booking.cancelled",
            {
                "quote_id": str(quote.id),
                "booking_id": str(quote.booking.id) if quote.booking else None,
                "status": "cancelled",
                "supplier_cancel_ok": result.get("supplier_cancel_ok"),
                "needs_manual_supplier_cancel": bool(
                    result.get("supplier_cancel_ok") is False
                ),
            },
        )

    data = QuoteResponse.model_validate(quote)
    data.items = enrich_quote_items_money(quote)
    return data
