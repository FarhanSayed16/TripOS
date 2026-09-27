"""Live-inventory Phase 2 — Redis shopping search cache."""
from __future__ import annotations

import json
import py_compile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.schemas.inventory import (
    InventoryType,
    NormalizedOffer,
    PassengerQuery,
    SearchQuery,
)
from app.services import search_cache


API_ROOT = Path(__file__).resolve().parents[1]


class FakeRedis:
    """In-memory stand-in for redis.asyncio used by redis_client helpers."""

    def __init__(self):
        self.store: dict[str, str] = {}
        self.locks: dict[str, str] = {}

    async def get(self, key: str) -> Optional[str]:
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None, nx: bool = False):
        if nx:
            if key in self.store or key in self.locks:
                return False
            self.locks[key] = value
            self.store[key] = value
            return True
        self.store[key] = value
        return True

    async def delete(self, key: str):
        self.store.pop(key, None)
        self.locks.pop(key, None)
        return 1

    async def aclose(self):
        pass


def _sample_query() -> SearchQuery:
    return SearchQuery(
        type=InventoryType.FLIGHT,
        origin="del",
        destination="bom",
        departure_date=date.today() + timedelta(days=14),
        passengers=PassengerQuery(adults=1, children=0, infants=0),
    )


def _sample_offer() -> NormalizedOffer:
    return NormalizedOffer(
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


def test_cache_key_normalizes_route():
    q = _sample_query()
    key = search_cache.cache_key("mock_supplier", q)
    assert key.startswith("inv:mock_supplier:flight:DEL:BOM:")
    assert ":1:0:0" in key


def test_search_cache_settings_defaults():
    s = Settings(_env_file=None)
    assert s.SEARCH_CACHE_ENABLED is False
    assert s.SEARCH_CACHE_TTL_SECONDS == 120


@pytest.mark.asyncio
async def test_get_set_offers_roundtrip():
    fake = FakeRedis()
    q = _sample_query()
    offer = _sample_offer()

    with (
        patch("app.services.search_cache.settings") as mock_settings,
        patch("app.core.redis_client.get_redis", return_value=fake),
    ):
        mock_settings.SEARCH_CACHE_ENABLED = True
        mock_settings.SEARCH_CACHE_TTL_SECONDS = 120

        assert await search_cache.get_offers("mock_supplier", q) is None
        await search_cache.set_offers("mock_supplier", q, [offer])
        hit = await search_cache.get_offers("mock_supplier", q)
        assert hit is not None
        assert len(hit.offers) == 1
        assert hit.offers[0].id == "o1"
        assert hit.age_seconds >= 0


@pytest.mark.asyncio
async def test_cache_disabled_skips_redis():
    q = _sample_query()
    with patch("app.services.search_cache.settings") as mock_settings:
        mock_settings.SEARCH_CACHE_ENABLED = False
        assert await search_cache.get_offers("mock_supplier", q) is None
        await search_cache.set_offers("mock_supplier", q, [_sample_offer()])
        # still none — set is no-op when disabled
        assert await search_cache.get_offers("mock_supplier", q) is None


@pytest.mark.asyncio
async def test_redis_down_falls_through_to_live():
    """get_json failures return None → search path must live-call."""
    from app.core import redis_client

    with patch("app.core.redis_client.get_redis", side_effect=RuntimeError("down")):
        assert await redis_client.get_json("any") is None
        assert await redis_client.set_json("any", {"a": 1}, 10) is False
        assert await redis_client.try_lock("lock") is True  # fail open


@pytest.mark.asyncio
async def test_ten_searches_one_live_when_cached():
    """Same query ×10 within TTL → ≤1 adapter.search."""
    from app.services import inventory as inv

    offer = _sample_offer()
    q = _sample_query()
    fake = FakeRedis()
    live_calls = {"n": 0}

    class FakeAdapter:
        supplier_code = "mock_supplier"

        async def search(self, query):
            live_calls["n"] += 1
            return [offer]

    user = MagicMock()
    user.active_organization_id = "00000000-0000-0000-0000-000000000001"
    user.id = "00000000-0000-0000-0000-000000000002"
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    with (
        patch("app.services.inventory.settings") as inv_settings,
        patch("app.services.search_cache.settings") as cache_settings,
        patch("app.core.redis_client.get_redis", return_value=fake),
        patch("app.services.inventory.SupplierStrategy") as MockStrat,
        patch("app.services.inventory.AdapterRegistry") as MockReg,
        patch("app.services.inventory.circuit_breaker") as mock_cb,
        patch("app.services.inventory.SearchRequest") as MockSR,
        patch("app.services.inventory.record_live_call", new_callable=AsyncMock),
        patch(
            "app.services.inventory.get_org_live_search_policy",
            new_callable=AsyncMock,
            return_value=("allow", {"status": "ok", "l2b_ratio": 0}),
        ),
    ):
        inv_settings.SEARCH_CACHE_ENABLED = True
        cache_settings.SEARCH_CACHE_ENABLED = True
        cache_settings.SEARCH_CACHE_TTL_SECONDS = 120
        MockStrat.return_value.get_strategy.return_value = "all"
        MockStrat.return_value.select_for_search = AsyncMock(
            return_value=["mock_supplier"]
        )
        MockReg.get_adapter.return_value = FakeAdapter()
        mock_cb.is_open.return_value = False
        MockSR.return_value = MagicMock(id="sr1")

        first = await inv.search_inventory(q, user, db)
        assert first.cache_hit is False
        assert live_calls["n"] == 1

        for _ in range(9):
            resp = await inv.search_inventory(q, user, db)
            assert resp.cache_hit is True
            assert resp.results_count == 1
            assert resp.cache_age_seconds is not None

        assert live_calls["n"] == 1


@pytest.mark.asyncio
async def test_cache_miss_still_returns_offers():
    from app.services import inventory as inv

    offer = _sample_offer()
    q = _sample_query()
    fake = FakeRedis()

    class FakeAdapter:
        supplier_code = "mock_supplier"

        async def search(self, query):
            return [offer]

    user = MagicMock()
    user.active_organization_id = "00000000-0000-0000-0000-000000000001"
    user.id = "00000000-0000-0000-0000-000000000002"
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    with (
        patch("app.services.inventory.settings") as inv_settings,
        patch("app.services.search_cache.settings") as cache_settings,
        patch("app.core.redis_client.get_redis", return_value=fake),
        patch("app.services.inventory.SupplierStrategy") as MockStrat,
        patch("app.services.inventory.AdapterRegistry") as MockReg,
        patch("app.services.inventory.circuit_breaker") as mock_cb,
        patch("app.services.inventory.SearchRequest") as MockSR,
        patch("app.services.inventory.record_live_call", new_callable=AsyncMock),
        patch(
            "app.services.inventory.get_org_live_search_policy",
            new_callable=AsyncMock,
            return_value=("allow", {"status": "ok", "l2b_ratio": 0}),
        ),
    ):
        inv_settings.SEARCH_CACHE_ENABLED = True
        cache_settings.SEARCH_CACHE_ENABLED = True
        cache_settings.SEARCH_CACHE_TTL_SECONDS = 120
        MockStrat.return_value.get_strategy.return_value = "all"
        MockStrat.return_value.select_for_search = AsyncMock(
            return_value=["mock_supplier"]
        )
        MockReg.get_adapter.return_value = FakeAdapter()
        mock_cb.is_open.return_value = False
        MockSR.return_value = MagicMock(id="sr1")

        resp = await inv.search_inventory(q, user, db)
        assert resp.results_count == 1
        assert resp.offers[0].id == "o1"
        assert resp.cache_hit is False


def test_phase2_modules_compile():
    for rel in (
        "app/core/redis_client.py",
        "app/services/search_cache.py",
        "app/services/inventory.py",
        "app/schemas/inventory.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)


def test_fe_indicative_badge_source():
    web = API_ROOT.parent / "web" / "src" / "app" / "(agent)" / "app" / "search"
    results = (web / "components" / "OfferResults.tsx").read_text(encoding="utf-8")
    assert "Indicative" in results
    page = (web / "page.tsx").read_text(encoding="utf-8")
    assert "cacheHit" in page
    api = (
        API_ROOT.parent / "web" / "src" / "lib" / "api" / "inventoryApi.ts"
    ).read_text(encoding="utf-8")
    assert "cache_hit" in api
