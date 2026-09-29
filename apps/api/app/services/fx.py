"""Currency conversion helpers (FC Phase 4) — display only; never invent fares."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any, Dict, List, Optional  # noqa: F401 — Any used by resolve helpers

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.fx import FxRate

TWOPLACES = Decimal("0.01")
EIGHTPLACES = Decimal("0.00000001")


@dataclass
class FxQuote:
    base_currency: str
    quote_currency: str
    rate: Decimal
    as_of: datetime
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_currency": self.base_currency,
            "quote_currency": self.quote_currency,
            "rate": float(self.rate),
            "as_of": self.as_of.isoformat() if self.as_of else None,
            "source": self.source,
        }


def normalize_currency(code: Optional[str]) -> str:
    c = (code or settings.CHARGE_CURRENCY or "INR").strip().upper()
    if len(c) != 3 or not c.isalpha():
        raise ValueError(f"Invalid currency code: {code}")
    return c


def round_money(amount: Decimal) -> Decimal:
    """Commercial rounding to 2 decimal places (ROUND_HALF_UP)."""
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def convert_major(
    amount: float | Decimal,
    *,
    rate: Decimal,
) -> Decimal:
    """Convert major units using rate (quote per 1 base)."""
    try:
        major = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        major = Decimal("0")
    return round_money(major * rate)


def convert_paise_to_display_major(paise: int, *, rate: Decimal) -> Decimal:
    """INR paise (or charge minor units) → display major units."""
    major = Decimal(paise) / Decimal(100)
    return convert_major(major, rate=rate)


async def get_fx_quote(
    db: AsyncSession,
    *,
    base: str,
    quote: str,
) -> FxQuote:
    base_c = normalize_currency(base)
    quote_c = normalize_currency(quote)
    if base_c == quote_c:
        return FxQuote(
            base_currency=base_c,
            quote_currency=quote_c,
            rate=Decimal("1"),
            as_of=datetime.now(timezone.utc),
            source="identity",
        )

    row = (
        await db.execute(
            select(FxRate).where(
                FxRate.base_currency == base_c,
                FxRate.quote_currency == quote_c,
                FxRate.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if row:
        return FxQuote(
            base_currency=base_c,
            quote_currency=quote_c,
            rate=Decimal(row.rate),
            as_of=row.as_of,
            source=row.source,
        )

    # Try inverse: if we have quote→base, invert
    inv = (
        await db.execute(
            select(FxRate).where(
                FxRate.base_currency == quote_c,
                FxRate.quote_currency == base_c,
                FxRate.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if inv and Decimal(inv.rate) != 0:
        rate = (Decimal("1") / Decimal(inv.rate)).quantize(
            EIGHTPLACES, rounding=ROUND_HALF_UP
        )
        return FxQuote(
            base_currency=base_c,
            quote_currency=quote_c,
            rate=rate,
            as_of=inv.as_of,
            source=f"inverse:{inv.source}",
        )

    raise ValueError(f"No FX rate for {base_c}/{quote_c}")


def money_display_dict(
    *,
    currency: str,
    amount_major: float | Decimal,
    fx: Optional[FxQuote],
    display_currency: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build Phase 4 money envelope. Supplier/charge amounts stay untouched;
    display_* are derived.
    """
    cur = normalize_currency(currency)
    amt = round_money(Decimal(str(amount_major)))
    out: Dict[str, Any] = {
        "currency": cur,
        "amount": float(amt),
        "display_currency": cur,
        "display_amount": float(amt),
        "fx_rate": 1.0,
        "fx_as_of": None,
        "fx_source": "identity",
    }
    if fx and normalize_currency(display_currency or fx.quote_currency) != cur:
        disp = convert_major(amt, rate=fx.rate)
        out.update(
            {
                "display_currency": fx.quote_currency,
                "display_amount": float(disp),
                "fx_rate": float(fx.rate),
                "fx_as_of": fx.as_of.isoformat() if fx.as_of else None,
                "fx_source": fx.source,
            }
        )
    elif fx:
        out["fx_as_of"] = fx.as_of.isoformat() if fx.as_of else None
        out["fx_source"] = fx.source
    return out


async def list_fx_rates(db: AsyncSession, *, active_only: bool = True) -> List[FxRate]:
    stmt = select(FxRate).order_by(FxRate.base_currency, FxRate.quote_currency)
    if active_only:
        stmt = stmt.where(FxRate.is_active.is_(True))
    return list((await db.execute(stmt)).scalars().all())


async def upsert_fx_rate(
    db: AsyncSession,
    *,
    base_currency: str,
    quote_currency: str,
    rate: float | Decimal,
    source: str = "manual",
    as_of: Optional[datetime] = None,
    is_active: bool = True,
) -> FxRate:
    base_c = normalize_currency(base_currency)
    quote_c = normalize_currency(quote_currency)
    if base_c == quote_c:
        raise ValueError("base and quote currency must differ")
    rate_d = Decimal(str(rate))
    if rate_d <= 0:
        raise ValueError("rate must be positive")

    row = (
        await db.execute(
            select(FxRate).where(
                FxRate.base_currency == base_c,
                FxRate.quote_currency == quote_c,
            )
        )
    ).scalar_one_or_none()
    when = as_of or datetime.now(timezone.utc)
    if row:
        row.rate = rate_d
        row.as_of = when
        row.source = source
        row.is_active = is_active
        return row

    row = FxRate(
        base_currency=base_c,
        quote_currency=quote_c,
        rate=rate_d,
        as_of=when,
        source=source,
        is_active=is_active,
    )
    db.add(row)
    await db.flush()
    return row


async def seed_default_fx_rates(db: AsyncSession) -> List[FxRate]:
    """Bootstrap approximate manual rates vs INR for staging demos."""
    # Rough illustrative rates — ops must replace with real desk rates
    defaults = [
        ("INR", "USD", "0.01200000"),
        ("INR", "AED", "0.04400000"),
        ("INR", "EUR", "0.01100000"),
        ("INR", "GBP", "0.00950000"),
    ]
    out = []
    for base, quote, rate in defaults:
        out.append(
            await upsert_fx_rate(
                db,
                base_currency=base,
                quote_currency=quote,
                rate=rate,
                source="seed",
            )
        )
    return out


async def resolve_display_currency(
    db: AsyncSession,
    *,
    user: Optional[Any] = None,
    organization_id=None,
) -> str:
    """User override → org preferred → charge currency."""
    from app.models.tenancy import Organization

    if user is not None:
        pref = getattr(user, "preferred_currency", None)
        if pref:
            return normalize_currency(pref)
        organization_id = organization_id or getattr(user, "active_organization_id", None)

    if organization_id:
        org = await db.get(Organization, organization_id)
        if org and getattr(org, "preferred_currency", None):
            return normalize_currency(org.preferred_currency)

    return normalize_currency(settings.CHARGE_CURRENCY)


async def attach_offer_money(
    offers: List[Any],
    *,
    fx: Optional[FxQuote],
    display_currency: str,
) -> None:
    """Mutate offer.money in place; never touch total_amount/currency."""
    for offer in offers:
        cur = getattr(offer, "currency", None) or settings.CHARGE_CURRENCY
        amt = float(getattr(offer, "total_amount", 0) or 0)
        use_fx = (
            fx
            if fx and normalize_currency(display_currency) != normalize_currency(cur)
            else None
        )
        offer.money = money_display_dict(
            currency=cur,
            amount_major=amt,
            fx=use_fx,
            display_currency=display_currency,
        )


def paise_money_display(
    paise: int,
    *,
    charge_currency: str,
    fx: Optional[FxQuote],
    display_currency: str,
) -> Dict[str, Any]:
    major = Decimal(paise) / Decimal(100)
    if fx and normalize_currency(display_currency) != normalize_currency(charge_currency):
        return money_display_dict(
            currency=charge_currency,
            amount_major=major,
            fx=fx,
            display_currency=display_currency,
        )
    return money_display_dict(
        currency=charge_currency,
        amount_major=major,
        fx=None,
        display_currency=charge_currency,
    )


def fx_quote_from_quote_row(quote) -> Optional[FxQuote]:
    """Rebuild FxQuote from snapshot columns on Quote."""
    rate = getattr(quote, "fx_rate", None)
    display = getattr(quote, "display_currency", None) or settings.CHARGE_CURRENCY
    charge = getattr(quote, "charge_currency", None) or settings.CHARGE_CURRENCY
    if not rate or normalize_currency(display) == normalize_currency(charge):
        return None
    as_of = getattr(quote, "fx_as_of", None) or datetime.now(timezone.utc)
    return FxQuote(
        base_currency=normalize_currency(charge),
        quote_currency=normalize_currency(display),
        rate=Decimal(str(rate)),
        as_of=as_of,
        source=getattr(quote, "fx_source", None) or "snapshot",
    )


def enrich_quote_items_money(quote) -> list:
    """Build item dicts with money envelopes for API responses."""
    fx = fx_quote_from_quote_row(quote)
    charge = getattr(quote, "charge_currency", None) or settings.CHARGE_CURRENCY
    display = getattr(quote, "display_currency", None) or charge
    out = []
    for item in quote.items or []:
        offer_data = None
        if getattr(item, "offer_snapshot", None) and item.offer_snapshot.offer_data:
            offer_data = item.offer_snapshot.offer_data
        out.append(
            {
                "id": item.id,
                "offer_snapshot_id": item.offer_snapshot_id,
                "supplier_cost": item.supplier_cost,
                "agent_markup": item.agent_markup,
                "platform_fee": item.platform_fee,
                "customer_total": item.customer_total,
                "extras": list(getattr(item, "extras", None) or []),
                "extras_total": int(getattr(item, "extras_total", 0) or 0),
                "offer": offer_data,
                "money": paise_money_display(
                    item.customer_total,
                    charge_currency=charge,
                    fx=fx,
                    display_currency=display,
                ),
            }
        )
    return out
