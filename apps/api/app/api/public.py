from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.schemas.quotes import PublicQuoteResponse
from app.api.deps import get_db
from app.models.commercial import Quote, QuoteItem
from app.models.enums import PaymentStatus
from app.core.config import settings

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/quotes/{token}", response_model=PublicQuoteResponse)
async def api_get_public_quote(
    token: str,
    locale: str | None = None,
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

    from app.services.fx import fx_quote_from_quote_row, paise_money_display
    from app.services.i18n import normalize_locale, resolve_locale

    charge = quote.charge_currency or settings.CHARGE_CURRENCY or "INR"
    display = quote.display_currency or charge
    fx = fx_quote_from_quote_row(quote)

    resolved_locale = await resolve_locale(
        query_locale=locale,
        organization=quote.organization,
    )

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
            "money": paise_money_display(
                item.customer_total,
                charge_currency=charge,
                fx=fx,
                display_currency=display,
            ),
        })

    payment_link = None
    if quote.payment is not None and quote.payment.status == PaymentStatus.pending:
        payment_link = quote.payment.payment_link_url

    charge_note = None
    if display.upper() != charge.upper():
        if resolved_locale == "hi":
            charge_note = (
                f"राशि {display} में दिखाई गई है। भुगतान {charge} में लिया जाता है। "
                f"दर दिनांक: "
                f"{quote.fx_as_of.isoformat() if quote.fx_as_of else 'कोट निर्माण'}।"
            )
        else:
            charge_note = (
                f"Amounts shown in {display}. Payment is collected in {charge} "
                f"(settle currency). Rate as of "
                f"{quote.fx_as_of.isoformat() if quote.fx_as_of else 'quote creation'}."
            )

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
        charge_currency=charge,
        display_currency=display,
        fx_rate=float(quote.fx_rate) if quote.fx_rate is not None else None,
        fx_as_of=quote.fx_as_of,
        fx_source=quote.fx_source,
        charge_note=charge_note,
        locale=normalize_locale(resolved_locale),
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
