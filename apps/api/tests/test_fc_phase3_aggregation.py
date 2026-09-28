"""FC Phase 3 — offer aggregation, dedupe, ranking."""
from __future__ import annotations

from app.schemas.inventory import InventoryType, NormalizedOffer
from app.services.offer_aggregation import (
    SortKey,
    aggregate_offers,
    dedupe_offers,
    enrich_offer_fields,
    filter_offers,
    fingerprint,
    sort_offers,
)


def _flight(price, *, supplier="tbo", airline="6E", flight="302", duration=120, stops=0, title=None):
    return NormalizedOffer(
        id=f"{supplier}-{flight}-{price}",
        supplier_code=supplier,
        supplier_reference=f"ref-{supplier}-{flight}",
        type=InventoryType.FLIGHT,
        total_amount=float(price),
        base_amount=float(price) * 0.8,
        tax_amount=float(price) * 0.2,
        title=title or f"IndiGo Flight {flight}",
        airline_code=airline,
        airline_name="IndiGo",
        duration_minutes=duration,
        stops=stops,
        depart_time="08:00",
        source_type="agg" if supplier == "tbo" else "mock",
        raw_data={
            "Segments": [
                [
                    {
                        "Airline": {"AirlineCode": airline, "AirlineName": "IndiGo"},
                        "FlightNumber": flight,
                        "Duration": duration,
                    }
                ]
            ]
        },
    )


def test_fingerprint_same_flight_different_suppliers():
    a = _flight(5000, supplier="tbo")
    b = _flight(4800, supplier="mock_supplier")
    assert fingerprint(a) == fingerprint(b)


def test_dedupe_keeps_cheapest():
    offers = [
        _flight(5000, supplier="tbo"),
        _flight(4800, supplier="mock_supplier"),
        _flight(9000, supplier="tbo", flight="999", title="SpiceJet Flight 999"),
    ]
    out = dedupe_offers(offers)
    assert len(out) == 2
    cheap = next(o for o in out if "302" in (o.raw_data.get("Segments")[0][0]["FlightNumber"]))
    assert cheap.total_amount == 4800
    assert cheap.supplier_code == "mock_supplier"


def test_dedupe_prefers_tbo_on_tie():
    offers = [
        _flight(5000, supplier="mock_supplier"),
        _flight(5000, supplier="tbo"),
    ]
    out = dedupe_offers(offers)
    assert len(out) == 1
    assert out[0].supplier_code == "tbo"


def test_sort_by_duration():
    offers = [
        _flight(4000, duration=300, flight="1"),
        _flight(5000, duration=100, flight="2"),
    ]
    sorted_o = sort_offers(offers, SortKey.duration)
    assert sorted_o[0].duration_minutes == 100


def test_filter_max_stops_and_price():
    offers = [
        _flight(4000, stops=0, flight="1"),
        _flight(4500, stops=1, flight="2"),
        _flight(9000, stops=0, flight="3"),
    ]
    out = filter_offers(offers, max_stops=0, max_price=5000)
    assert len(out) == 1
    assert out[0].raw_data["Segments"][0][0]["FlightNumber"] == "1"


def test_aggregate_pipeline_meta():
    offers = [
        _flight(5000, supplier="tbo"),
        _flight(4800, supplier="mock_supplier"),
        _flight(7000, supplier="tbo", flight="888", stops=2, duration=400),
    ]
    out, meta = aggregate_offers(
        offers, sort=SortKey.price, max_stops=1, limit=50, dedupe=True
    )
    assert meta["deduped_away"] == 1
    assert meta["before_dedupe"] == 3
    assert all(o.stops is None or o.stops <= 1 for o in out)
    assert "tbo" in meta["supplier_counts"] or "mock_supplier" in meta["supplier_counts"]


def test_enrich_from_description():
    o = NormalizedOffer(
        id="x",
        supplier_code="mock_supplier",
        supplier_reference="r",
        type=InventoryType.FLIGHT,
        total_amount=1000,
        base_amount=800,
        tax_amount=200,
        title="MockAir Flight 1",
        description="Non-stop, 2h 30m. Includes bag.",
    )
    e = enrich_offer_fields(o)
    assert e.stops == 0
    assert e.duration_minutes == 150
