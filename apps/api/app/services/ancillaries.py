"""FC Phase 6 — ancillary catalog + seat map + quote extras."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.adapters.registry import AdapterRegistry
from app.core.config import settings
from app.core.exceptions import AppError
from app.models.commercial import Quote, QuoteItem
from app.models.enums import QuoteStatus
from app.models.tenancy import User
from app.schemas.ancillaries import (
    AncillaryCatalog,
    OfferExtrasRequest,
    QuoteExtraLine,
    QuoteItemExtrasUpdate,
    SeatMapResponse,
)
from app.schemas.inventory import NormalizedOffer


def feature_ancillaries_enabled() -> bool:
    return bool(settings.FC_ANCILLARIES_ENABLED)


def feature_seat_map_enabled() -> bool:
    return bool(settings.FC_SEAT_MAP_ENABLED)


async def fetch_ancillaries(offer: NormalizedOffer) -> AncillaryCatalog:
    if not feature_ancillaries_enabled():
        return AncillaryCatalog(
            supported=False,
            currency=offer.currency or "INR",
            message="Ancillaries feature is disabled",
        )
    try:
        adapter = AdapterRegistry.get_adapter(offer.supplier_code)
    except ValueError as e:
        raise AppError(str(e), status_code=400, error_code="INVALID_SUPPLIER") from e
    if not adapter.capabilities.can_ancillaries:
        return AncillaryCatalog(
            supported=False,
            currency=offer.currency or "INR",
            message="Supplier does not support ancillaries",
        )
    return await adapter.get_ancillaries(offer)


async def fetch_seat_map(offer: NormalizedOffer) -> SeatMapResponse:
    if not feature_seat_map_enabled():
        return SeatMapResponse(
            supported=False,
            currency=offer.currency or "INR",
            message="Seat map feature is disabled",
        )
    try:
        adapter = AdapterRegistry.get_adapter(offer.supplier_code)
    except ValueError as e:
        raise AppError(str(e), status_code=400, error_code="INVALID_SUPPLIER") from e
    if not adapter.capabilities.can_seat_map:
        return SeatMapResponse(
            supported=False,
            currency=offer.currency or "INR",
            message="Supplier does not support seat maps",
        )
    return await adapter.get_seat_map(offer)


def extras_total_paise(extras: List[Dict[str, Any]] | List[QuoteExtraLine]) -> int:
    total = 0
    for e in extras or []:
        if isinstance(e, QuoteExtraLine):
            total += int(e.amount_paise or 0)
        else:
            total += int(e.get("amount_paise") or 0)
    return total


def extras_as_dicts(extras: List[QuoteExtraLine]) -> List[Dict[str, Any]]:
    return [e.model_dump(mode="json") for e in extras]


def clear_seat_extras(extras: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """On fare_changed revalidate, drop seat holds (stale). Keep baggage/meal/ssr."""
    out = []
    for e in extras or []:
        if (e.get("type") or "").lower() == "seat":
            continue
        out.append(e)
    return out


def attach_extras_to_offer(
    offer: NormalizedOffer, extras: Optional[List[Dict[str, Any]]]
) -> NormalizedOffer:
    """Copy offer with selected_extras in raw_data for book payload."""
    refreshed = offer.model_copy(deep=True)
    raw = dict(refreshed.raw_data or {})
    raw["selected_extras"] = list(extras or [])
    refreshed.raw_data = raw
    return refreshed


async def update_quote_item_extras(
    quote_id: str,
    item_id: str,
    body: QuoteItemExtrasUpdate,
    current_user: User,
    db: AsyncSession,
) -> Quote:
    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot),
            selectinload(Quote.passengers),
            selectinload(Quote.booking),
        )
        .where(
            Quote.id == quote_id,
            Quote.organization_id == current_user.active_organization_id,
        )
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()
    if not quote:
        raise AppError("Quote not found", status_code=404, error_code="NOT_FOUND")
    if quote.status not in (QuoteStatus.draft, QuoteStatus.ready):
        raise AppError(
            "Extras can only be edited on draft/ready quotes",
            status_code=400,
            error_code="INVALID_STATUS",
        )

    item = next((i for i in quote.items if str(i.id) == str(item_id)), None)
    if not item:
        raise AppError("Quote item not found", status_code=404, error_code="NOT_FOUND")

    extras_list = extras_as_dicts(body.extras)
    extras_sum = extras_total_paise(body.extras)
    item.extras = extras_list
    item.extras_total = extras_sum
    item.customer_total = (
        int(item.supplier_cost)
        + int(item.agent_markup)
        + int(item.platform_fee)
        + extras_sum
    )

    # Freeze extras onto offer snapshot for book honesty
    if item.offer_snapshot and item.offer_snapshot.offer_data:
        data = dict(item.offer_snapshot.offer_data)
        raw = dict(data.get("raw_data") or {})
        raw["selected_extras"] = extras_list
        data["raw_data"] = raw
        item.offer_snapshot.offer_data = data

    await db.commit()
    await db.refresh(quote, ["items", "passengers", "booking"])
    return quote
