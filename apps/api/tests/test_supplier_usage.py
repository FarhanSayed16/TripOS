"""Live-inventory Phase 1 — supplier usage metering + L2B ratios."""
from __future__ import annotations

import py_compile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.services.supplier_usage import compute_l2b_ratio, l2b_status, record_live_call


API_ROOT = Path(__file__).resolve().parents[1]


def test_l2b_settings_defaults():
    s = Settings(_env_file=None)
    assert s.L2B_WARN_RATIO == 80.0
    assert s.L2B_CRITICAL_RATIO == 120.0
    assert s.SEARCH_CACHE_ENABLED is False


def test_compute_l2b_ratio_floor_one_confirmed():
    # 80 looks, 0 confirmed → 80 / 1
    assert compute_l2b_ratio(50, 30, 0) == 80.0
    assert compute_l2b_ratio(100, 20, 2) == 60.0


def test_l2b_status_thresholds():
    with patch("app.services.supplier_usage.settings") as mock_s:
        mock_s.L2B_WARN_RATIO = 80.0
        mock_s.L2B_CRITICAL_RATIO = 120.0
        assert l2b_status(10) == "ok"
        assert l2b_status(80) == "warn"
        assert l2b_status(120) == "critical"
        assert l2b_status(200) == "critical"


@pytest.mark.asyncio
async def test_record_live_call_upserts_search():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()

    await record_live_call(db, "mock_supplier", "search", "user_search", org_id="org-1")

    assert db.execute.await_count == 1
    assert db.flush.await_count == 1


@pytest.mark.asyncio
async def test_record_live_call_swallows_db_errors():
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=RuntimeError("db down"))
    # Must not raise
    await record_live_call(db, "mock_supplier", "revalidate", "payment_revalidate")


@pytest.mark.asyncio
async def test_search_inventory_meters_live_search():
    from datetime import date, timedelta

    from app.schemas.inventory import (
        InventoryType,
        NormalizedOffer,
        PassengerQuery,
        SearchQuery,
    )
    from app.services import inventory as inv

    offer = NormalizedOffer(
        id="o1",
        supplier_code="mock_supplier",
        supplier_reference="MOCK-1",
        type=InventoryType.FLIGHT,
        title="A",
        total_amount=100.0,
        base_amount=80.0,
        tax_amount=20.0,
        currency="INR",
    )

    class FakeAdapter:
        supplier_code = "mock_supplier"

        async def search(self, q):
            return [offer]

    user = MagicMock()
    user.active_organization_id = "00000000-0000-0000-0000-000000000001"
    user.id = "00000000-0000-0000-0000-000000000002"
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    query = SearchQuery(
        type=InventoryType.FLIGHT,
        origin="DEL",
        destination="BOM",
        departure_date=date.today() + timedelta(days=7),
        passengers=PassengerQuery(adults=1),
    )

    with (
        patch("app.services.inventory.SupplierStrategy") as MockStrat,
        patch("app.services.inventory.AdapterRegistry") as MockReg,
        patch("app.services.inventory.circuit_breaker") as mock_cb,
        patch("app.services.inventory.SearchRequest") as MockSR,
        patch("app.services.inventory.record_live_call", new_callable=AsyncMock) as mock_rec,
        patch(
            "app.services.inventory.get_org_live_search_policy",
            new_callable=AsyncMock,
            return_value=("allow", {"status": "ok", "l2b_ratio": 0}),
        ),
    ):
        MockStrat.return_value.get_strategy.return_value = "all"
        MockStrat.return_value.select_for_search = AsyncMock(
            return_value=["mock_supplier"]
        )
        MockReg.get_adapter.return_value = FakeAdapter()
        mock_cb.is_open.return_value = False
        MockSR.return_value = MagicMock(id="sr1")
        await inv.search_inventory(query, user, db, usage_source="user_search")

    mock_rec.assert_awaited()
    kwargs = mock_rec.await_args
    assert kwargs.args[2] == "search" or (
        kwargs.kwargs.get("kind") == "search" if kwargs.kwargs else False
    )
    # positional: db, supplier_code, kind, source
    assert mock_rec.await_args.args[1] == "mock_supplier"
    assert mock_rec.await_args.args[2] == "search"
    assert mock_rec.await_args.args[3] == "user_search"


def test_admin_exposes_l2b_routes():
    source = (API_ROOT / "app" / "api" / "admin.py").read_text(encoding="utf-8")
    assert '"/l2b"' in source or "'/l2b'" in source
    assert "l2b_7d" in source
    assert "summarize_l2b" in source


def test_phase1_modules_compile():
    for rel in (
        "app/services/supplier_usage.py",
        "app/services/inventory.py",
        "app/services/payments.py",
        "app/services/jobs.py",
        "app/api/admin.py",
        "app/models/inventory.py",
        "alembic/versions/b3c4d5e6f7a8_add_supplier_usage_daily.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)
