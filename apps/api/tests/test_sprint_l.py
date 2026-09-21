"""Sprint L — inventory supplier gating + simulated TBO labels (no DB)."""
from __future__ import annotations

import py_compile
from pathlib import Path

from app.core.config import Settings


API_ROOT = Path(__file__).resolve().parents[1]


def test_inventory_suppliers_default_mock_only():
    s = Settings(INVENTORY_SUPPLIERS="mock_supplier")
    assert s.inventory_supplier_codes == ["mock_supplier"]


def test_inventory_suppliers_can_include_tbo():
    s = Settings(INVENTORY_SUPPLIERS="mock_supplier,tbo")
    assert s.inventory_supplier_codes == ["mock_supplier", "tbo"]


def test_inventory_suppliers_empty_falls_back_to_mock():
    s = Settings(INVENTORY_SUPPLIERS="")
    assert s.inventory_supplier_codes == ["mock_supplier"]


def test_inventory_service_uses_settings_not_hardcoded_tbo():
    source = (API_ROOT / "app" / "services" / "inventory.py").read_text(encoding="utf-8")
    assert "inventory_supplier_codes" in source
    assert '["mock_supplier", "tbo"]' not in source


def test_tbo_pnr_and_title_simulated():
    source = (API_ROOT / "app" / "adapters" / "tbo_adapter.py").read_text(encoding="utf-8")
    assert "SIM-TBO" in source
    assert "[SIMULATED]" in source


def test_e2e_happy_path_uses_current_routes():
    happy = (API_ROOT / "tests" / "e2e" / "test_e2e_happy_path.py").read_text(encoding="utf-8")
    assert "mark-sent" not in happy
    assert "pay-link" not in happy
    assert "process_outbox_jobs" not in happy
    assert "poll_outbox" in happy or "drain_outbox" in happy
    assert "/payment" in happy or "create_payment" in happy


def test_sprint_l_modules_compile():
    for rel in (
        "app/core/config.py",
        "app/services/inventory.py",
        "app/adapters/tbo_adapter.py",
        "tests/e2e/helpers.py",
        "tests/e2e/test_e2e_happy_path.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)
