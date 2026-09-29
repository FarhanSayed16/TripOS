"""FC Phase 6 — fare families, ancillaries, seat extras."""
from __future__ import annotations

import pytest

from app.adapters.mock_adapter import MockAdapter
from app.schemas.inventory import (
    InventoryType,
    NormalizedOffer,
    PassengerQuery,
    SearchQuery,
)
from app.services.ancillaries import (
    attach_extras_to_offer,
    clear_seat_extras,
    extras_total_paise,
)
from app.services.offer_aggregation import fingerprint
from datetime import date


def test_fingerprint_keeps_fare_families_distinct():
    def make(**kwargs):
        data = dict(
            id="1",
            supplier_code="mock_supplier",
            supplier_reference="a",
            type=InventoryType.FLIGHT,
            total_amount=1000,
            base_amount=800,
            tax_amount=200,
            title="MockAir Flight",
            airline_code="MK",
            duration_minutes=150,
            stops=0,
            depart_time="08:00",
            family_group_id="g1",
            raw_data={"flight_number": "MK101"},
        )
        data.update(kwargs)
        return NormalizedOffer(**data)

    basic = make(fare_family="Basic", fare_family_code="BASIC")
    flex = make(id="2", fare_family="Flex", fare_family_code="FLEX")
    assert fingerprint(basic) != fingerprint(flex)


def test_clear_seat_extras_keeps_baggage():
    extras = [
        {"type": "baggage", "code": "BAG_5KG", "label": "Bag", "amount_paise": 75000},
        {"type": "seat", "code": "12A", "label": "Seat 12A", "amount_paise": 45000},
        {"type": "meal", "code": "MEAL_VEG", "label": "Veg", "amount_paise": 35000},
    ]
    cleared = clear_seat_extras(extras)
    assert len(cleared) == 2
    assert all(e["type"] != "seat" for e in cleared)
    assert extras_total_paise(cleared) == 110000


def test_attach_extras_to_offer_raw():
    offer = NormalizedOffer(
        id="1",
        supplier_code="mock_supplier",
        supplier_reference="x",
        type=InventoryType.FLIGHT,
        total_amount=1000,
        base_amount=800,
        tax_amount=200,
        title="t",
        raw_data={},
    )
    out = attach_extras_to_offer(
        offer,
        [{"type": "seat", "code": "10A", "label": "Seat 10A", "amount_paise": 80000}],
    )
    assert offer.raw_data == {}  # original untouched
    assert out.raw_data["selected_extras"][0]["code"] == "10A"


@pytest.mark.asyncio
async def test_mock_search_returns_fare_families():
    adapter = MockAdapter()
    offers = await adapter.search(
        SearchQuery(
            type=InventoryType.FLIGHT,
            origin="DEL",
            destination="BOM",
            departure_date=date(2026, 10, 1),
            passengers=PassengerQuery(adults=1),
        )
    )
    families = {o.fare_family for o in offers if o.fare_family}
    assert "Basic" in families
    assert "Flex" in families
    assert "Premium" in families
    grouped = [o for o in offers if o.family_group_id]
    assert len(grouped) >= 3
    assert len({o.family_group_id for o in grouped}) >= 1


@pytest.mark.asyncio
async def test_mock_ancillaries_and_seat_map():
    adapter = MockAdapter()
    offers = await adapter.search(
        SearchQuery(
            type=InventoryType.FLIGHT,
            origin="DEL",
            destination="BOM",
            departure_date=date(2026, 10, 1),
            passengers=PassengerQuery(adults=1),
        )
    )
    flex = next(o for o in offers if o.fare_family == "Flex")
    cat = await adapter.get_ancillaries(flex)
    assert cat.supported
    assert any(i.type == "baggage" for i in cat.items)
    assert any(i.type == "ssr" for i in cat.items)
    sm = await adapter.get_seat_map(flex)
    assert sm.supported
    assert len(sm.rows) > 0
    assert any(c.available for r in sm.rows for c in r.seats)
