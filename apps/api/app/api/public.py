from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.schemas.quotes import PublicQuoteResponse
from app.api.deps import get_db
from app.models.commercial import Quote, QuoteItem
from app.models.enums import PaymentStatus

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/quotes/{token}", response_model=PublicQuoteResponse)
async def api_get_public_quote(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Sanitized quote by public token — no auth. Never exposes agent cost."""
    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot),
            selectinload(Quote.payment),
            selectinload(Quote.organization),
            selectinload(Quote.booking),
        )
        .where(Quote.public_token == token)
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    # ISSUE-07: Build response explicitly instead of mutating ORM objects
    sanitized_items = []
    for item in quote.items:
        sanitized_offer = {}
        if item.offer_snapshot and item.offer_snapshot.offer_data:
            raw = item.offer_snapshot.offer_data
            sanitized_offer = {
                "title": raw.get("title", ""),
                "description": raw.get("description", ""),
                "type": raw.get("type", ""),
                "currency": raw.get("currency", ""),
            }
        sanitized_items.append({
            "id": item.id,
            "customer_total": item.customer_total,
            "sanitized_offer_data": sanitized_offer,
        })

    payment_link = None
    if quote.payment is not None and quote.payment.status == PaymentStatus.pending:
        payment_link = quote.payment.payment_link_url

    return PublicQuoteResponse(
        id=quote.id,
        status=quote.status,
        valid_until=quote.valid_until,
        items=sanitized_items,
        payment_link_url=payment_link,
        agency_name=quote.organization.brand_name if quote.organization else "TripOS",
        agency_logo_url=quote.organization.logo_url if quote.organization else None,
        payment_status=quote.payment.status.value if quote.payment else None,
        booking_status=quote.booking.status.value if quote.booking else None,
    )

from app.models.tenancy import OrganizationDomain

@router.get("/theme/{domain}")
async def get_theme(
    domain: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(OrganizationDomain)
        .options(selectinload(OrganizationDomain.organization))
        .where(OrganizationDomain.domain == domain, OrganizationDomain.is_verified == True)
    )
    domain_record = (await db.execute(stmt)).scalar_one_or_none()
    
    if not domain_record or not domain_record.organization:
        raise HTTPException(status_code=404, detail="Domain not found or verified")
        
    org = domain_record.organization
    return {
        "brand_name": org.brand_name,
        "primary_color": org.primary_color,
        "logo_url": org.logo_url
    }
