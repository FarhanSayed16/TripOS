import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
import structlog
from urllib.parse import quote_plus
from datetime import datetime

from app.models.commercial import Quote, Message
from app.models.enums import QuoteStatus
from app.models.tenancy import User
from app.services.messaging_provider import get_messaging_provider
from app.services.audit import write_audit

logger = structlog.get_logger()

# Validate E.164: strictly a '+' followed by 10 to 15 digits
E164_REGEX = re.compile(r"^\+[1-9]\d{9,14}$")

async def generate_whatsapp_preview(quote_id: str, current_user: User, db: AsyncSession, frontend_url: str):
    """
    Generates the initial message template and validates the customer phone.
    """
    stmt = select(Quote).options(
        selectinload(Quote.customer),
        selectinload(Quote.items)
    ).where(
        Quote.id == quote_id,
        Quote.organization_id == current_user.active_organization_id
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.status not in (QuoteStatus.ready, QuoteStatus.sent):
        raise HTTPException(status_code=400, detail="Only 'ready' or 'sent' quotes can be shared")

    customer = quote.customer
    phone = customer.phone_e164

    if not E164_REGEX.match(phone):
        raise HTTPException(
            status_code=400, 
            detail=f"Customer phone '{phone}' is not a valid E.164 format. Ensure it starts with '+' and country code."
        )

    # Note: Frontend URL comes from config, defaulting here to typical local for now, 
    # but ideally it should be injected via settings.
    public_url = f"{frontend_url}/q/{quote.public_token}"
    charge = getattr(quote, "charge_currency", None) or "INR"
    display = getattr(quote, "display_currency", None) or charge
    total_paise = sum(item.customer_total for item in quote.items)
    total_charge = total_paise / 100

    from app.services.fx import fx_quote_from_quote_row, paise_money_display
    from app.services.i18n import resolve_locale
    from app.services.message_templates import (
        amount_line_for_locale,
        whatsapp_quote_template,
    )

    locale = await resolve_locale(user=current_user, db=db)
    if locale == "hi":
        valid_until = quote.valid_until.strftime("%d/%m/%Y %I:%M %p")
    else:
        valid_until = quote.valid_until.strftime("%B %d, %Y %I:%M %p")

    fx = fx_quote_from_quote_row(quote)
    money = paise_money_display(
        total_paise,
        charge_currency=charge,
        fx=fx,
        display_currency=display,
    )
    display_amt = money["display_amount"]
    display_cur = money["display_currency"]
    fx_as_of_str = (
        quote.fx_as_of.strftime("%Y-%m-%d %H:%M UTC") if quote.fx_as_of else None
    )

    amount_line = amount_line_for_locale(
        locale=locale,
        display_cur=display_cur,
        display_amt=display_amt,
        charge=charge,
        total_charge=total_charge,
        fx_as_of_str=fx_as_of_str,
    )
    message_template = whatsapp_quote_template(
        locale=locale,
        first_name=customer.first_name,
        amount_line=amount_line,
        public_url=public_url,
        valid_until=valid_until,
    )


    provider = get_messaging_provider("whatsapp")
    wa_me_url = provider.build_outbound_url(phone, message_template)

    return {
        "phone_e164": phone,
        "message_template": message_template,
        "wa_me_url": wa_me_url,
    }


async def send_quote_message(quote_id: str, content: str, channel: str, current_user: User, db: AsyncSession):
    """
    Logs the message and transitions the quote to 'sent'.
    """
    stmt = select(Quote).where(
        Quote.id == quote_id,
        Quote.organization_id == current_user.active_organization_id
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote.status == QuoteStatus.draft:
        raise HTTPException(status_code=400, detail="Cannot send a draft quote.")

    # 1. Log the message
    msg = Message(
        quote_id=quote.id,
        sender_user_id=current_user.id,
        channel=channel,
        content=content
    )
    db.add(msg)

    # 2. Transition status if it was just ready
    if quote.status == QuoteStatus.ready:
        quote.status = QuoteStatus.sent

    # 3. Emit Audit Event
    await write_audit(
        db,
        organization_id=quote.organization_id,
        actor_user_id=current_user.id,
        action="quote.sent",
        entity_type="quote",
        entity_id=str(quote.id),
        metadata={"channel": channel},
    )

    await db.commit()
    await db.refresh(quote, ["items", "passengers", "booking"])
    return quote
