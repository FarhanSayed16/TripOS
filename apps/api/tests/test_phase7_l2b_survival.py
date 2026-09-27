"""Live-inventory Phase 7 — platform L2B survival soft-brakes."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.services.l2b_survival import (
    effective_cache_ttl,
    get_survival_state,
    peek_survival,
    reset_survival_cache_for_tests,
)


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def test_phase7_settings_defaults():
    s = Settings(_env_file=None)
    assert s.L2B_SURVIVAL_ENABLED is True
    assert s.L2B_SURVIVAL_TTL_MULTIPLIER == 2.0
    assert s.L2B_SURVIVAL_TTL_CAP_SECONDS == 900
    assert s.L2B_SURVIVAL_PAUSE_WARM_REFRESH is True


def test_effective_cache_ttl_idle():
    reset_survival_cache_for_tests()
    assert effective_cache_ttl(120) == 120


def test_effective_cache_ttl_widens_when_active():
    reset_survival_cache_for_tests()
    import app.services.l2b_survival as mod

    mod._cached = (
        0.0,
        {
            "enabled": True,
            "active": True,
            "ttl_multiplier": 2.0,
            "ttl_cap_seconds": 900,
        },
    )
    assert effective_cache_ttl(120) == 240
    assert effective_cache_ttl(600) == 900  # capped


@pytest.mark.asyncio
async def test_get_survival_state_critical_activates():
    reset_survival_cache_for_tests()
    db = AsyncMock()
    summary = {
        "status": "critical",
        "l2b_ratio": 150.0,
        "looks": 150,
        "confirmed_bookings": 1,
        "window_days": 7,
    }
    with (
        patch("app.services.l2b_survival.summarize_l2b", new=AsyncMock(return_value=summary)),
        patch("app.services.l2b_survival.settings") as mock_s,
    ):
        mock_s.L2B_SURVIVAL_ENABLED = True
        mock_s.L2B_SURVIVAL_TTL_MULTIPLIER = 2.0
        mock_s.L2B_SURVIVAL_TTL_CAP_SECONDS = 900
        mock_s.L2B_SURVIVAL_PAUSE_WARM_REFRESH = True
        mock_s.L2B_WARN_RATIO = 80
        mock_s.L2B_CRITICAL_RATIO = 120
        mock_s.SENTRY_DSN = None

        state = await get_survival_state(db, force=True)
        assert state["active"] is True
        assert state["ttl_multiplier"] == 2.0
        assert state["pause_warm_refresh"] is True
        assert peek_survival()["active"] is True


@pytest.mark.asyncio
async def test_get_survival_state_ok_idle():
    reset_survival_cache_for_tests()
    db = AsyncMock()
    summary = {
        "status": "ok",
        "l2b_ratio": 40.0,
        "looks": 40,
        "confirmed_bookings": 1,
        "window_days": 7,
    }
    with (
        patch("app.services.l2b_survival.summarize_l2b", new=AsyncMock(return_value=summary)),
        patch("app.services.l2b_survival.settings") as mock_s,
    ):
        mock_s.L2B_SURVIVAL_ENABLED = True
        mock_s.L2B_SURVIVAL_TTL_MULTIPLIER = 2.0
        mock_s.L2B_SURVIVAL_TTL_CAP_SECONDS = 900
        mock_s.L2B_SURVIVAL_PAUSE_WARM_REFRESH = True
        mock_s.L2B_WARN_RATIO = 80
        mock_s.L2B_CRITICAL_RATIO = 120
        mock_s.SENTRY_DSN = None

        state = await get_survival_state(db, force=True)
        assert state["active"] is False
        assert state["ttl_multiplier"] == 1.0
        assert state["pause_warm_refresh"] is False


@pytest.mark.asyncio
async def test_refresh_pauses_warm_when_survival_active():
    from app.services.cache_refresh import refresh_hot_routes
    from app.services.search_popularity import PopularRoute
    from datetime import date, timedelta

    db = AsyncMock()
    db.commit = AsyncMock()
    routes = [
        PopularRoute(
            inv_type="flight",
            origin="DEL",
            destination="BOM",
            departure_date=(date.today() + timedelta(days=10)).isoformat(),
            return_date=None,
            adults=1,
            children=0,
            infants=0,
            hits=100,
        ),
        PopularRoute(
            inv_type="flight",
            origin="BOM",
            destination="GOI",
            departure_date=(date.today() + timedelta(days=12)).isoformat(),
            return_date=None,
            adults=1,
            children=0,
            infants=0,
            hits=50,
        ),
    ]
    survival = {
        "active": True,
        "pause_warm_refresh": True,
        "ttl_multiplier": 2.0,
    }

    with (
        patch("app.services.cache_refresh.settings") as mock_s,
        patch(
            "app.services.cache_refresh.get_survival_state",
            new=AsyncMock(return_value=survival),
        ),
        patch(
            "app.services.cache_refresh.get_popular_routes",
            new=AsyncMock(return_value=routes),
        ),
        patch("app.services.cache_refresh.AdapterRegistry") as mock_reg,
        patch("app.services.cache_refresh.search_cache") as mock_cache,
        patch("app.services.cache_refresh.record_live_call", new=AsyncMock()),
        patch("app.services.cache_refresh.circuit_breaker") as mock_cb,
    ):
        mock_s.SEARCH_CACHE_ENABLED = True
        mock_s.SEARCH_CACHE_REFRESH_ENABLED = True
        mock_s.SEARCH_CACHE_TOP_N = 50
        mock_s.SEARCH_CACHE_HOT_TOP_N = 1
        mock_s.inventory_supplier_codes = ["mock"]
        mock_cb.is_open.return_value = False
        mock_cb.record_success = MagicMock()
        mock_cb.record_failure = MagicMock()

        adapter = AsyncMock()
        adapter.search = AsyncMock(return_value=[])
        mock_reg.get_adapter.return_value = adapter
        mock_cache.acquire_singleflight = AsyncMock(return_value=True)
        mock_cache.release_singleflight = AsyncMock()
        mock_cache.set_offers = AsyncMock()

        result = await refresh_hot_routes(db)
        assert result["skipped"] is False
        assert result["pause_warm_refresh"] is True
        assert result["skipped_warm"] == 1
        assert result["refreshed"] == 1


def test_phase7_files_exist():
    assert (API_ROOT / "app" / "services" / "l2b_survival.py").is_file()
    assert (REPO_ROOT / "docs" / "ops" / "L2B_SURVIVAL_RUNBOOK.md").is_file()
