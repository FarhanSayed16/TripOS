import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from app.schemas.quotes import QuoteCreate, QuotePassengerUpdate
from app.models.commercial import Quote, QuoteItem, QuotePassenger
from app.models.inventory import OfferSnapshot, Supplier, SearchRequest
from app.models.enums import QuoteStatus
from app.models.tenancy import User
from app.schemas.inventory import InventoryType
from app.core.exceptions import AppError
from app.core.config import settings

logger = structlog.get_logger()


async def get_supplier_by_code(code: str, db: AsyncSession) -> Supplier:
    stmt = select(Supplier).where(Supplier.code == code)
    supplier = (await db.execute(stmt)).scalar_one_or_none()
    if not supplier:
        raise ValueError(f"Supplier with code {code} not found in DB")
    return supplier


def _offer_type_from_quote(quote: Quote) -> str | None:
    for item in quote.items:
        if item.offer_snapshot and item.offer_snapshot.offer_data:
            return item.offer_snapshot.offer_data.get("type")
    return None


async def _required_pax_count(quote: Quote, db: AsyncSession) -> tuple[str, int]:
    """
    Returns (product_type, minimum_passengers).
    Flights: adults+children+infants from original search (fallback 1).
    Hotels: guest minimum = 1.
    """
    product_type = _offer_type_from_quote(quote) or InventoryType.FLIGHT.value

    if product_type == InventoryType.HOTEL.value:
        return product_type, 1

    # Flight: prefer search request passenger counts
    search_id = None
    for item in quote.items:
        if item.offer_snapshot:
            search_id = item.offer_snapshot.search_request_id
            break

    min_pax = 1
    if search_id:
        search_req = (
            await db.execute(select(SearchRequest).where(SearchRequest.id == search_id))
        ).scalar_one_or_none()
        if search_req and isinstance(search_req.payload, dict):
            pax = search_req.payload.get("passengers") or {}
            adults = int(pax.get("adults") or 0)
            children = int(pax.get("children") or 0)
            infants = int(pax.get("infants") or 0)
            total = adults + children + infants
            if total > 0:
                min_pax = total

    return product_type, min_pax


async def assert_pax_gate(quote: Quote, db: AsyncSession) -> None:
    """Shared pax gate for mark-ready and create-payment."""
    if not quote.items:
        raise AppError("Quote has no items", status_code=400, error_code="NO_ITEMS")

    product_type, min_pax = await _required_pax_count(quote, db)

    if not quote.passengers:
        raise AppError(
            "Pax Gate: Cannot proceed without passenger/guest details.",
            status_code=400,
            error_code="PAX_REQUIRED",
        )

    if len(quote.passengers) < min_pax:
        label = "guests" if product_type == InventoryType.HOTEL.value else "passengers"
        raise AppError(
            f"Pax Gate: Need at least {min_pax} {label} (got {len(quote.passengers)}).",
            status_code=400,
            error_code="PAX_INCOMPLETE",
        )

    for pax in quote.passengers:
        if not pax.first_name or not pax.last_name:
            raise AppError(
                "Pax Gate: All passengers must have a first and last name.",
                status_code=400,
                error_code="PAX_NAME_REQUIRED",
            )


async def create_quote(quote_in: QuoteCreate, current_user: User, db: AsyncSession) -> Quote:
    from app.models.crm import Customer

    product_types = {item.offer.type for item in quote_in.items}
    if len(product_types) > 1:
        raise AppError(
            "V1 Rule: A quote can only contain one product type (flights only or hotels only).",
            status_code=400,
            error_code="MIXED_PRODUCT_TYPE",
        )
    quote_type = product_types.pop()

    # AUDIT-005: customer must belong to the caller's organization
    customer = (
        await db.execute(
            select(Customer).where(
                Customer.id == quote_in.customer_id,
                Customer.organization_id == current_user.active_organization_id,
                Customer.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not customer:
        raise AppError("Customer not found", status_code=404, error_code="NOT_FOUND")

    now = datetime.now(timezone.utc)
    valid_until = (
        now + timedelta(hours=4)
        if quote_type == InventoryType.FLIGHT
        else now + timedelta(hours=12)
    )

    quote = Quote(
        organization_id=current_user.active_organization_id,
        customer_id=customer.id,
        created_by_user_id=current_user.id,
        public_token=secrets.token_urlsafe(32),
        status=QuoteStatus.draft,
        valid_until=valid_until,
    )
    db.add(quote)
    await db.flush()

    for item_in in quote_in.items:
        try:
            supplier = await get_supplier_by_code(item_in.offer.supplier_code, db)
        except ValueError:
            raise AppError(
                f"Invalid supplier code: {item_in.offer.supplier_code}",
                status_code=400,
                error_code="INVALID_SUPPLIER",
            )

        snapshot = OfferSnapshot(
            search_request_id=uuid.UUID(item_in.search_request_id),
            supplier_id=supplier.id,
            supplier_offer_id=item_in.offer.supplier_reference,
            offer_data=item_in.offer.model_dump(mode="json"),
        )
        db.add(snapshot)
        await db.flush()

        supplier_cost = int(item_in.offer.total_amount * 100)
        agent_markup = item_in.agent_markup
        platform_fee = int(settings.PLATFORM_FEE_PAISE or 0)
        customer_total = supplier_cost + agent_markup + platform_fee

        db.add(
            QuoteItem(
                quote_id=quote.id,
                offer_snapshot_id=snapshot.id,
                supplier_cost=supplier_cost,
                agent_markup=agent_markup,
                platform_fee=platform_fee,
                customer_total=customer_total,
            )
        )

    await db.commit()
    await db.refresh(quote, ["items", "passengers", "booking"])
    return quote


async def update_quote_passengers(
    quote_id: str,
    passengers_in: List[QuotePassengerUpdate],
    current_user: User,
    db: AsyncSession,
) -> Quote:
    # AUDIT-002: org-scoped — never mutate another agency's quote
    stmt = (
        select(Quote)
        .options(selectinload(Quote.passengers), selectinload(Quote.booking))
        .where(
            Quote.id == quote_id,
            Quote.organization_id == current_user.active_organization_id,
        )
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()

    if not quote:
        raise AppError("Quote not found", status_code=404, error_code="NOT_FOUND")

    for p in quote.passengers:
        await db.delete(p)

    await db.flush()

    for p_in in passengers_in:
        db.add(
            QuotePassenger(
                quote_id=quote.id,
                first_name=p_in.first_name,
                last_name=p_in.last_name,
                date_of_birth=p_in.date_of_birth,
                passport_number=p_in.passport_number,
            )
        )

    await db.commit()
    await db.refresh(quote, ["items", "passengers", "booking"])
    return quote


async def mark_quote_ready(quote_id: str, current_user: User, db: AsyncSession) -> Quote:
    # AUDIT-002: org-scoped — never mark another agency's quote ready
    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.passengers),
            selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot),
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

    if quote.status != QuoteStatus.draft:
        raise AppError(
            "Only draft quotes can be marked ready",
            status_code=400,
            error_code="INVALID_STATUS",
        )

    await assert_pax_gate(quote, db)

    quote.status = QuoteStatus.ready
    await db.commit()
    await db.refresh(quote, ["items", "passengers", "booking"])
    return quote


async def refresh_quote(quote_id: str, current_user: User, db: AsyncSession) -> Quote:
    """
    Refresh an expired/stale quote: revalidate offers → new draft quote with
    cloned passengers. Old quote is marked `expired` (no `superseded` status).
    FIX-P30-01: align with real Quote / QuoteItem / OfferSnapshot columns.
    """
    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.passengers),
            selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot),
        )
        .where(
            Quote.id == quote_id,
            Quote.organization_id == current_user.active_organization_id,
        )
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()

    if not quote:
        raise AppError("Quote not found", status_code=404, error_code="NOT_FOUND")

    if quote.status == QuoteStatus.paid:
        raise AppError(
            "Cannot refresh a paid quote",
            status_code=400,
            error_code="INVALID_STATUS",
        )

    if not quote.items:
        raise AppError("Quote has no items to refresh", status_code=400, error_code="NO_ITEMS")

    from app.services.inventory import revalidate_normalized_offer
    from app.schemas.inventory import NormalizedOffer

    new_item_rows: list[dict] = []
    product_type = InventoryType.FLIGHT.value

    for item in quote.items:
        snap = item.offer_snapshot
        if not snap or not snap.offer_data:
            continue

        offer_model = NormalizedOffer.model_validate(snap.offer_data)
        product_type = (
            offer_model.type.value
            if hasattr(offer_model.type, "value")
            else str(offer_model.type)
        )

        try:
            refreshed = await revalidate_normalized_offer(offer_model)
        except AppError:
            raise
        except Exception as e:
            logger.warning(
                "refresh_quote_revalidation_failed",
                error=str(e),
                quote_id=str(quote.id),
            )
            raise AppError(
                "Inventory is no longer available or price cannot be refreshed.",
                status_code=400,
                error_code="INVENTORY_UNAVAILABLE",
            ) from e

        new_snap = OfferSnapshot(
            search_request_id=snap.search_request_id,
            supplier_id=snap.supplier_id,
            supplier_offer_id=refreshed.supplier_reference or snap.supplier_offer_id,
            offer_data=refreshed.model_dump(mode="json"),
        )
        db.add(new_snap)
        await db.flush()

        supplier_cost = int(refreshed.total_amount * 100)
        agent_markup = item.agent_markup
        platform_fee = int(settings.PLATFORM_FEE_PAISE or 0)
        customer_total = supplier_cost + agent_markup + platform_fee

        new_item_rows.append(
            {
                "offer_snapshot_id": new_snap.id,
                "supplier_cost": supplier_cost,
                "agent_markup": agent_markup,
                "platform_fee": platform_fee,
                "customer_total": customer_total,
            }
        )

    if not new_item_rows:
        raise AppError(
            "No refreshable offer snapshots on this quote",
            status_code=400,
            error_code="NO_SNAPSHOTS",
        )

    now = datetime.now(timezone.utc)
    valid_until = (
        now + timedelta(hours=4)
        if product_type == InventoryType.FLIGHT.value
        else now + timedelta(hours=12)
    )

    new_quote = Quote(
        organization_id=quote.organization_id,
        customer_id=quote.customer_id,
        created_by_user_id=current_user.id,
        status=QuoteStatus.draft,
        public_token=secrets.token_urlsafe(32),
        valid_until=valid_until,
    )
    db.add(new_quote)
    await db.flush()

    for item_data in new_item_rows:
        db.add(QuoteItem(quote_id=new_quote.id, **item_data))

    for p in quote.passengers:
        db.add(
            QuotePassenger(
                quote_id=new_quote.id,
                first_name=p.first_name,
                last_name=p.last_name,
                date_of_birth=p.date_of_birth,
                passport_number=p.passport_number,
            )
        )

    # ISSUE-06: Use `superseded` to distinguish refreshed quotes from naturally expired ones
    quote.status = QuoteStatus.superseded

    await db.commit()
    await db.refresh(new_quote, ["items", "passengers"])
    return new_quote
