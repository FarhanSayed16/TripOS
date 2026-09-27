"""Live-inventory Phase 4 — per-org L2B throttle + AI guard."""
from __future__ import annotations

import py_compile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.exceptions import AppError
from app.services.supplier_usage import (
    compute_l2b_ratio,
    get_org_live_search_policy,
    l2b_status,
)


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def test_phase4_settings_defaults():
    s = Settings(_env_file=None)
    assert s.L2B_THROTTLE_MIN_CONFIRMED == 1
    assert s.L2B_ORG_CACHE_ONLY is False
    assert s.L2B_AI_BLOCK_ON_CRITICAL is True


def test_critical_ratio_with_zero_books():
    # 150 looks / max(0,1) = 150 → critical at default 120
    assert compute_l2b_ratio(150, 0, 0) == 150.0
    with patch("app.services.supplier_usage.settings") as mock_s:
        mock_s.L2B_WARN_RATIO = 80.0
        mock_s.L2B_CRITICAL_RATIO = 120.0
        assert l2b_status(150) == "critical"


@pytest.mark.asyncio
async def test_org_with_huge_searches_blocked():
    org_id = uuid4()
    summary = {
        "organization_id": str(org_id),
        "searches": 200,
        "revalidates": 0,
        "books": 0,
        "confirmed_bookings": 0,
        "looks": 200,
        "l2b_ratio": 200.0,
        "status": "critical",
        "warn_ratio": 80.0,
        "critical_ratio": 120.0,
    }
    with (
        patch(
            "app.services.supplier_usage.summarize_org_l2b",
            new_callable=AsyncMock,
            return_value=summary,
        ),
        patch("app.services.supplier_usage.settings") as mock_s,
    ):
        mock_s.L2B_THROTTLE_MIN_CONFIRMED = 1
        mock_s.L2B_ORG_CACHE_ONLY = False
        mock_s.L2B_AI_BLOCK_ON_CRITICAL = True
        policy, _ = await get_org_live_search_policy(
            AsyncMock(), org_id, usage_source="user_search"
        )
        assert policy == "block"


@pytest.mark.asyncio
async def test_org_cache_only_at_warn():
    org_id = uuid4()
    summary = {
        "organization_id": str(org_id),
        "searches": 90,
        "revalidates": 0,
        "books": 0,
        "confirmed_bookings": 0,
        "looks": 90,
        "l2b_ratio": 90.0,
        "status": "warn",
        "warn_ratio": 80.0,
        "critical_ratio": 120.0,
    }
    with (
        patch(
            "app.services.supplier_usage.summarize_org_l2b",
            new_callable=AsyncMock,
            return_value=summary,
        ),
        patch("app.services.supplier_usage.settings") as mock_s,
    ):
        mock_s.L2B_THROTTLE_MIN_CONFIRMED = 1
        mock_s.L2B_ORG_CACHE_ONLY = True
        mock_s.L2B_AI_BLOCK_ON_CRITICAL = True
        policy, _ = await get_org_live_search_policy(
            AsyncMock(), org_id, usage_source="user_search"
        )
        assert policy == "cache_only"


@pytest.mark.asyncio
async def test_ai_blocked_when_org_critical():
    org_id = uuid4()
    summary = {
        "organization_id": str(org_id),
        "searches": 50,
        "revalidates": 0,
        "books": 0,
        "confirmed_bookings": 5,  # enough confirmed → not throttle via min
        "looks": 50,
        "l2b_ratio": 130.0,
        "status": "critical",
        "warn_ratio": 80.0,
        "critical_ratio": 120.0,
    }
    # With confirmed >= min, user_search would allow unless cache_only;
    # but AI still blocks on critical status.
    with (
        patch(
            "app.services.supplier_usage.summarize_org_l2b",
            new_callable=AsyncMock,
            return_value=summary,
        ),
        patch("app.services.supplier_usage.settings") as mock_s,
    ):
        mock_s.L2B_THROTTLE_MIN_CONFIRMED = 1
        mock_s.L2B_ORG_CACHE_ONLY = False
        mock_s.L2B_AI_BLOCK_ON_CRITICAL = True
        # user: confirmed >= 1 and critical — NOT blocked by min_confirmed rule
        # wait: critical AND confirmed < min → block. confirmed=5 >= 1 → allow for user
        policy_user, _ = await get_org_live_search_policy(
            AsyncMock(), org_id, usage_source="user_search"
        )
        assert policy_user == "allow"

        policy_ai, _ = await get_org_live_search_policy(
            AsyncMock(), org_id, usage_source="ai_search"
        )
        assert policy_ai == "block"


@pytest.mark.asyncio
async def test_search_inventory_raises_throttled():
    from datetime import date, timedelta

    from app.schemas.inventory import (
        InventoryType,
        PassengerQuery,
        SearchQuery,
    )
    from app.services import inventory as inv

    user = MagicMock()
    user.active_organization_id = str(uuid4())
    user.id = str(uuid4())
    db = AsyncMock()
    query = SearchQuery(
        type=InventoryType.FLIGHT,
        origin="DEL",
        destination="BOM",
        departure_date=date.today() + timedelta(days=7),
        passengers=PassengerQuery(adults=1),
    )

    summary = {
        "l2b_ratio": 200.0,
        "confirmed_bookings": 0,
        "looks": 200,
        "status": "critical",
    }

    with (
        patch(
            "app.services.inventory.get_org_live_search_policy",
            new_callable=AsyncMock,
            return_value=("block", summary),
        ),
        patch("app.services.inventory.SupplierStrategy") as MockStrat,
        patch("app.services.inventory.AdapterRegistry") as MockReg,
        patch("app.services.inventory.circuit_breaker") as mock_cb,
        patch("app.services.inventory.settings") as inv_settings,
    ):
        inv_settings.SEARCH_CACHE_ENABLED = False
        MockStrat.return_value.get_strategy.return_value = "all"
        MockStrat.return_value.select_for_search = AsyncMock(
            return_value=["mock_supplier"]
        )

        class FakeAdapter:
            supplier_code = "mock_supplier"

            async def search(self, q):
                return []

        MockReg.get_adapter.return_value = FakeAdapter()
        mock_cb.is_open.return_value = False

        with pytest.raises(AppError) as exc:
            await inv.search_inventory(query, user, db)

        assert exc.value.status_code == 429
        assert exc.value.error_code == "SEARCH_THROTTLED_L2B"


def test_admin_l2b_orgs_route():
    source = (API_ROOT / "app" / "api" / "admin.py").read_text(encoding="utf-8")
    assert '"/l2b/orgs"' in source or "'/l2b/orgs'" in source
    assert "list_org_l2b_offenders" in source


def test_ai_rethrows_app_error():
    source = (API_ROOT / "app" / "api" / "ai.py").read_text(encoding="utf-8")
    assert "except AppError" in source


def test_fe_org_l2b_table():
    page = (
        REPO_ROOT
        / "apps"
        / "web"
        / "src"
        / "app"
        / "(admin)"
        / "admin"
        / "analytics"
        / "page.tsx"
    ).read_text(encoding="utf-8")
    assert "Org L2B offenders" in page
    assert "useGetAdminL2bOrgsQuery" in page


def test_phase4_modules_compile():
    for rel in (
        "app/services/supplier_usage.py",
        "app/services/inventory.py",
        "app/api/ai.py",
        "app/api/admin.py",
        "app/models/inventory.py",
        "alembic/versions/c4d5e6f7a8b9_add_supplier_usage_daily_org.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)
