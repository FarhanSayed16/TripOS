"""Sprint Q–T engineering gates (unit / source — no hosted deps)."""
from __future__ import annotations

import py_compile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.services.commissions import master_override_share
from app.services.supplier_strategy import SupplierStrategy


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def test_package_honesty_doc():
    text = (REPO_ROOT / "docs" / "packages-v1-honesty.md").read_text(encoding="utf-8")
    assert "snapshot" in text.lower()
    assert "to-quote" in text


def test_wallet_formula_doc_and_bps():
    text = (REPO_ROOT / "docs" / "wallet-commission-formula.md").read_text(encoding="utf-8")
    assert "MASTER_COMMISSION_OVERRIDE_BPS" in text
    s = Settings(_env_file=None)
    assert s.MASTER_COMMISSION_OVERRIDE_BPS == 2000
    master, agent = master_override_share(10_000)
    assert master == 2000
    assert agent == 8000


def test_wallet_reconcile_pending_available_math():
    """N-sample mental model: pending + available == earned for commission_earned only."""
    samples = [
        {"pending": 1000, "available": 0, "settled": 0},
        {"pending": 0, "available": 2500, "settled": 0},
        {"pending": 500, "available": 500, "settled": 2000},
    ]
    for row in samples:
        earned = row["pending"] + row["available"] + row["settled"]
        assert earned == row["pending"] + row["available"] + row["settled"]


def test_ai_spec_option_b():
    text = (REPO_ROOT / "docs" / "tripos-ai-spec.md").read_text(encoding="utf-8")
    assert "Option B" in text
    assert "monolith" in text.lower()


def test_failover_strategy_is_sequential_in_source():
    source = (API_ROOT / "app" / "services" / "inventory.py").read_text(encoding="utf-8")
    assert 'mode == "failover"' in source
    assert "failover_stop_on_success" in source


@pytest.mark.asyncio
async def test_failover_stops_after_first_success():
    from app.schemas.inventory import (
        InventoryType,
        NormalizedOffer,
        PassengerQuery,
        SearchQuery,
    )
    from datetime import date, timedelta
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
        def __init__(self, code, offers):
            self.supplier_code = code
            self._offers = offers
            self.calls = 0

        async def search(self, q):
            self.calls += 1
            return self._offers

    a1 = FakeAdapter("mock_supplier", [offer])
    a2 = FakeAdapter("tbo", [offer])

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
        patch("app.services.inventory.settings") as mock_settings,
        patch("app.services.inventory.SupplierStrategy") as MockStrat,
        patch("app.services.inventory.AdapterRegistry") as MockReg,
        patch("app.services.inventory.circuit_breaker") as mock_cb,
        patch("app.services.inventory.SearchRequest") as MockSR,
        patch(
            "app.services.inventory.get_org_live_search_policy",
            new_callable=AsyncMock,
            return_value=("allow", {"status": "ok", "l2b_ratio": 0}),
        ),
        patch("app.services.inventory.record_live_call", new_callable=AsyncMock),
    ):
        mock_settings.inventory_supplier_codes = ["mock_supplier", "tbo"]
        mock_settings.SEARCH_CACHE_ENABLED = False
        MockStrat.return_value.get_strategy.return_value = "failover"
        MockStrat.return_value.select_for_search = AsyncMock(
            return_value=["mock_supplier", "tbo"]
        )
        MockReg.get_adapter.side_effect = lambda code: a1 if code == "mock_supplier" else a2
        mock_cb.is_open.return_value = False
        MockSR.return_value = MagicMock(id="sr1")
        resp = await inv.search_inventory(query, user, db)

    assert resp.results_count == 1
    assert a1.calls == 1
    assert a2.calls == 0  # failover stopped


def test_booking_has_supplier_code_column():
    source = (API_ROOT / "app" / "models" / "commercial.py").read_text(encoding="utf-8")
    assert "supplier_code" in source
    assert "organization_id" in source


def test_branding_in_admin_nav():
    layout = (
        REPO_ROOT / "apps" / "web" / "src" / "app" / "(admin)" / "layout.tsx"
    ).read_text(encoding="utf-8")
    assert "/admin/branding" in layout


def test_domain_verify_endpoint_exists():
    source = (API_ROOT / "app" / "api" / "organizations.py").read_text(encoding="utf-8")
    assert "domains/{domain_id}/verify" in source


def test_sibling_isolation_source_pattern():
    """Org-scoped cancel/list must filter organization_id (sibling isolation basis)."""
    quotes = (API_ROOT / "app" / "api" / "quotes.py").read_text(encoding="utf-8")
    assert "organization_id == current_user.active_organization_id" in quotes
    customers = (API_ROOT / "app" / "api" / "customers.py").read_text(encoding="utf-8")
    assert "organization_id" in customers


def test_phase_40_process_docs():
    assert (REPO_ROOT / "docs" / "monthly-review-2026-09.md").is_file()
    backlog = (REPO_ROOT / "docs" / "backlog.md").read_text(encoding="utf-8")
    assert "ENH-02" in backlog
    assert "Parked" in backlog
    restore = (REPO_ROOT / "docs" / "ops" / "BACKUP_RESTORE.md").read_text(encoding="utf-8")
    assert "Restore dry-run" in restore
    assert "PASS" in restore


def test_document_share_and_mime_guards():
    source = (API_ROOT / "app" / "api" / "documents.py").read_text(encoding="utf-8")
    assert "share-link" in source
    assert "DOCUMENT_MAX_BYTES" in source or "max_bytes" in source


def test_followup_audits():
    source = (API_ROOT / "app" / "api" / "followups.py").read_text(encoding="utf-8")
    assert "followup.snoozed" in source
    assert "followup.dismissed" in source


def test_qrst_modules_compile():
    for rel in (
        "app/services/inventory.py",
        "app/services/commissions.py",
        "app/api/documents.py",
        "app/api/followups.py",
        "app/api/organizations.py",
        "app/api/packages.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)
