"""
Adapter contract tests (FIX-P11-08 / FIX-P11-21).

Run from apps/api:
  pytest tests/test_adapters_contract.py -q
"""
from datetime import date, timedelta

import pytest

from app.adapters.base import BaseAdapter
from app.adapters.registry import AdapterRegistry
from app.core.inventory_errors import InventoryRevalidateError
from app.schemas.inventory import (
    InventoryType,
    PassengerQuery,
    SearchQuery,
)


@pytest.fixture
def adapter() -> BaseAdapter:
    return AdapterRegistry.get_adapter("mock_supplier")


def _flight_query() -> SearchQuery:
    return SearchQuery(
        type=InventoryType.FLIGHT,
        origin="DEL",
        destination="BOM",
        departure_date=date.today() + timedelta(days=7),
        passengers=PassengerQuery(adults=1),
    )


def _hotel_query() -> SearchQuery:
    return SearchQuery(
        type=InventoryType.HOTEL,
        origin="DEL",
        destination="GOI",
        departure_date=date.today() + timedelta(days=14),
        passengers=PassengerQuery(adults=2),
    )


@pytest.mark.asyncio
async def test_registry_resolves_mock(adapter: BaseAdapter):
    assert adapter.supplier_code == "mock_supplier"
    assert adapter.capabilities.can_book is True
    assert adapter.capabilities.can_revalidate is True


@pytest.mark.asyncio
async def test_flight_search_returns_four_offers(adapter: BaseAdapter):
    offers = await adapter.search(_flight_query())
    assert len(offers) == 4
    assert all(o.type == InventoryType.FLIGHT for o in offers)
    assert all(o.currency == "INR" for o in offers)
    refs = {o.supplier_reference for o in offers}
    assert "MOCK-FLIGHT-FARE-CHG" in refs
    assert "MOCK-FLIGHT-SOLD-OUT" in refs


@pytest.mark.asyncio
async def test_hotel_search(adapter: BaseAdapter):
    offers = await adapter.search(_hotel_query())
    assert len(offers) == 2
    assert all(o.type == InventoryType.HOTEL for o in offers)
    refs = {o.supplier_reference for o in offers}
    assert "MOCK-HOTEL-SOLD-OUT" in refs

@pytest.mark.asyncio
async def test_revalidate_happy_path(adapter: BaseAdapter):
    offers = await adapter.search(_flight_query())
    happy = next(o for o in offers if "FARE-CHG" not in o.supplier_reference and "SOLD-OUT" not in o.supplier_reference)
    assert happy.is_revalidated is False
    result = await adapter.revalidate(happy)
    assert result.is_revalidated is True


@pytest.mark.asyncio
async def test_revalidate_fare_changed(adapter: BaseAdapter):
    offers = await adapter.search(_flight_query())
    fare_chg = next(o for o in offers if "FARE-CHG" in o.supplier_reference)
    with pytest.raises(InventoryRevalidateError) as exc:
        await adapter.revalidate(fare_chg)
    assert exc.value.error_code == "fare_changed"


@pytest.mark.asyncio
async def test_revalidate_sold_out(adapter: BaseAdapter):
    offers = await adapter.search(_flight_query())
    sold = next(o for o in offers if "SOLD-OUT" in o.supplier_reference)
    with pytest.raises(InventoryRevalidateError) as exc:
        await adapter.revalidate(sold)
    assert exc.value.error_code == "sold_out"


@pytest.mark.asyncio
async def test_book_cancel_status(adapter: BaseAdapter):
    offers = await adapter.search(_flight_query())
    offer = offers[0]
    await adapter.revalidate(offer)
    pnr = await adapter.book(offer, [{"first_name": "Test", "last_name": "User"}])
    assert pnr.startswith("MOCK-PNR-")
    assert await adapter.cancel(pnr) is True
    st = await adapter.status(pnr)
    assert st["status"] == "confirmed"
    assert st["supplier_ref"] == pnr


def test_map_error_passthrough(adapter: BaseAdapter):
    err = InventoryRevalidateError("sold_out", "gone")
    assert adapter.map_error(err) is err


def test_map_error_wraps_generic(adapter: BaseAdapter):
    mapped = adapter.map_error(RuntimeError("vendor boom"))
    assert isinstance(mapped, InventoryRevalidateError)
    assert mapped.error_code == "supplier_error"
    assert "vendor boom" in mapped.message
