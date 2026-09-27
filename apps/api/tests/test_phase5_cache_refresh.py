"""Live-inventory Phase 5 — background hot-route cache refresh."""
from __future__ import annotations

import py_compile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.schemas.inventory import InventoryType, NormalizedOffer
from app.services.cache_refresh import refresh_hot_routes
from app.services.search_popularity import PopularRoute


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def test_phase5_settings_defaults():
    s = Settings(_env_file=None)
    assert s.SEARCH_CACHE_REFRESH_ENABLED is False
    assert s.SEARCH_CACHE_REFRESH_INTERVAL_SECONDS == 60
    assert s.SEARCH_CACHE_HOT_TTL_SECONDS == 90
    assert s.SEARCH_CACHE_WARM_TTL_SECONDS == 600
    assert s.SEARCH_CACHE_TOP_N == 50
    assert s.SEARCH_CACHE_HOT_TOP_N == 10


def test_popular_route_to_search_query():
    route = PopularRoute(
        inv_type="flight",
        origin="del",
        destination="bom",
        departure_date=(date.today() + timedelta(days=10)).isoformat(),
        return_date=None,
        adults=1,
        children=0,
        infants=0,
        hits=42,
    )
    q = route.to_search_query()
    assert q.type == InventoryType.FLIGHT
    assert q.origin == "del" or q.origin.upper() == "DEL"
    # PopularRoute stores uppercased origin in get_popular_routes; dataclass may be mixed
    assert q.destination.upper() == "BOM"
    assert q.passengers.adults == 1


@pytest.mark.asyncio
async def test_refresh_skipped_when_disabled():
    db = AsyncMock()
    with patch("app.services.cache_refresh.settings") as mock_s:
        mock_s.SEARCH_CACHE_ENABLED = True
        mock_s.SEARCH_CACHE_REFRESH_ENABLED = False
        result = await refresh_hot_routes(db)
        assert result["skipped"] is True
        assert result["reason"] == "refresh_disabled"


@pytest.mark.asyncio
async def test_refresh_skipped_when_cache_off():
    db = AsyncMock()
    with patch("app.services.cache_refresh.settings") as mock_s:
        mock_s.SEARCH_CACHE_ENABLED = False
        mock_s.SEARCH_CACHE_REFRESH_ENABLED = True
        result = await refresh_hot_routes(db)
        assert result["skipped"] is True
        assert result["reason"] == "cache_disabled"


@pytest.mark.asyncio
async def test_refresh_hot_routes_calls_adapter_and_cache():
    db = AsyncMock()
    db.commit = AsyncMock()
    route = PopularRoute(
        inv_type="flight",
        origin="DEL",
        destination="BOM",
        departure_date=(date.today() + timedelta(days=14)).isoformat(),
        return_date=None,
        adults=1,
        children=0,
        infants=0,
        hits=10,
    )
    offer = NormalizedOffer(
        id="o1",
        supplier_code="mock_supplier",
        supplier_reference="MOCK-1",
        type=InventoryType.FLIGHT,
        title="DEL-BOM",
        total_amount=5000.0,
        base_amount=4000.0,
        tax_amount=1000.0,
        currency="INR",
    )

    class FakeAdapter:
        supplier_code = "mock_supplier"
        calls = 0

        async def search(self, q):
            FakeAdapter.calls += 1
            return [offer]

    FakeAdapter.calls = 0

    with (
        patch("app.services.cache_refresh.settings") as mock_s,
        patch(
            "app.services.cache_refresh.get_popular_routes",
            new_callable=AsyncMock,
            return_value=[route],
        ),
        patch("app.services.cache_refresh.AdapterRegistry") as MockReg,
        patch("app.services.cache_refresh.circuit_breaker") as mock_cb,
        patch(
            "app.services.cache_refresh.search_cache.set_offers",
            new_callable=AsyncMock,
        ) as mock_set,
        patch(
            "app.services.cache_refresh.search_cache.acquire_singleflight",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "app.services.cache_refresh.search_cache.release_singleflight",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.cache_refresh.record_live_call",
            new_callable=AsyncMock,
        ) as mock_rec,
    ):
        mock_s.SEARCH_CACHE_ENABLED = True
        mock_s.SEARCH_CACHE_REFRESH_ENABLED = True
        mock_s.SEARCH_CACHE_TOP_N = 50
        mock_s.SEARCH_CACHE_HOT_TOP_N = 10
        mock_s.inventory_supplier_codes = ["mock_supplier"]
        MockReg.get_adapter.return_value = FakeAdapter()
        mock_cb.is_open.return_value = False

        result = await refresh_hot_routes(db)

    assert result["skipped"] is False
    assert result["refreshed"] == 1
    assert FakeAdapter.calls == 1
    mock_set.assert_awaited()
    assert mock_set.await_args.kwargs.get("band") == "hot"
    mock_rec.assert_awaited()
    assert mock_rec.await_args.args[3] == "cache_refresh"


@pytest.mark.asyncio
async def test_refresh_skips_open_circuit():
    db = AsyncMock()
    db.commit = AsyncMock()
    route = PopularRoute(
        inv_type="flight",
        origin="DEL",
        destination="BOM",
        departure_date=(date.today() + timedelta(days=14)).isoformat(),
        return_date=None,
        adults=1,
        children=0,
        infants=0,
        hits=10,
    )
    with (
        patch("app.services.cache_refresh.settings") as mock_s,
        patch(
            "app.services.cache_refresh.get_popular_routes",
            new_callable=AsyncMock,
            return_value=[route],
        ),
        patch("app.services.cache_refresh.circuit_breaker") as mock_cb,
        patch(
            "app.services.cache_refresh.search_cache.set_offers",
            new_callable=AsyncMock,
        ) as mock_set,
    ):
        mock_s.SEARCH_CACHE_ENABLED = True
        mock_s.SEARCH_CACHE_REFRESH_ENABLED = True
        mock_s.SEARCH_CACHE_TOP_N = 50
        mock_s.SEARCH_CACHE_HOT_TOP_N = 10
        mock_s.inventory_supplier_codes = ["mock_supplier"]
        mock_cb.is_open.return_value = True

        result = await refresh_hot_routes(db)

    assert result["refreshed"] == 0
    assert result["skipped_circuit"] >= 1
    mock_set.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_offers_hot_band_ttl():
    from app.services import search_cache
    from app.schemas.inventory import PassengerQuery, SearchQuery

    q = SearchQuery(
        type=InventoryType.FLIGHT,
        origin="DEL",
        destination="BOM",
        departure_date=date.today() + timedelta(days=7),
        passengers=PassengerQuery(adults=1),
    )
    offer = NormalizedOffer(
        id="o1",
        supplier_code="mock_supplier",
        supplier_reference="M1",
        type=InventoryType.FLIGHT,
        title="x",
        total_amount=1.0,
        base_amount=1.0,
        tax_amount=0.0,
        currency="INR",
    )
    with (
        patch("app.services.search_cache.settings") as mock_s,
        patch(
            "app.services.search_cache.redis_client.set_json",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_set,
    ):
        mock_s.SEARCH_CACHE_ENABLED = True
        mock_s.SEARCH_CACHE_HOT_TTL_SECONDS = 90
        mock_s.SEARCH_CACHE_WARM_TTL_SECONDS = 600
        mock_s.SEARCH_CACHE_TTL_SECONDS = 120
        await search_cache.set_offers("mock_supplier", q, [offer], band="hot")
        assert mock_set.await_args.args[2] == 90
        await search_cache.set_offers("mock_supplier", q, [offer], band="warm")
        assert mock_set.await_args.args[2] == 600


def test_worker_registers_cache_refresh_handler():
    source = (API_ROOT / "worker.py").read_text(encoding="utf-8")
    assert "inventory_cache_refresh" in source
    assert "refresh_hot_routes" in source
    assert "SEARCH_CACHE_REFRESH_ENABLED" in source


def test_ops_checklist_documents_pause():
    text = (REPO_ROOT / "docs" / "ops" / "PHASE_39_CHECKLIST.md").read_text(
        encoding="utf-8"
    )
    assert "SEARCH_CACHE_REFRESH_ENABLED=false" in text
    assert "Pause refresher" in text or "pause" in text.lower()


def test_phase5_modules_compile():
    for rel in (
        "app/services/search_popularity.py",
        "app/services/cache_refresh.py",
        "app/services/search_cache.py",
        "worker.py",
        "app/core/config.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)
