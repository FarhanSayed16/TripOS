"""FC Phase 2 — fare rules, refunds, supplier metrics."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.models.enums import RefundStatus
from app.schemas.inventory import InventoryType, NormalizedOffer
from app.services.fare_rules import derive_fare_rules_from_offer, get_fare_rules_for_offer
from app.services.supplier_metrics import SupplierMetrics


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def _offer(**kwargs):
    base = dict(
        id="1",
        supplier_code="tbo",
        supplier_reference="trace::TBO-RES-1",
        type=InventoryType.FLIGHT,
        total_amount=5700,
        base_amount=4500,
        tax_amount=1200,
        title="Test",
        raw_data={"IsRefundable": True, "Segments": [[{"Baggage": "15 kg"}]]},
    )
    base.update(kwargs)
    return NormalizedOffer(**base)


def test_derive_fare_rules_refundable():
    rules = derive_fare_rules_from_offer(_offer())
    assert rules.is_refundable is True
    assert rules.change_allowed is True
    assert rules.baggage_summary == "15 kg"
    assert "Refundable" in (rules.raw_text or "")


def test_derive_fare_rules_non_refundable():
    rules = derive_fare_rules_from_offer(
        _offer(raw_data={"IsRefundable": False})
    )
    assert rules.is_refundable is False
    assert rules.change_allowed is False


@pytest.mark.asyncio
async def test_get_fare_rules_for_offer_fallback():
    rules = await get_fare_rules_for_offer(_offer(supplier_code="unknown_supplier_xyz"))
    assert rules.source == "derived"
    assert rules.supplier_code == "unknown_supplier_xyz"


def test_supplier_metrics_p95():
    m = SupplierMetrics(window_seconds=3600, max_samples=100)
    for i in range(20):
        m.record("mock_supplier", 100 + i * 10, ok=True)
    m.record("mock_supplier", 50, ok=False)
    snap = m.snapshot("mock_supplier")
    assert snap["sample_count"] == 21
    assert snap["error_count"] == 1
    assert snap["latency_p95_ms"] is not None
    assert snap["error_rate"] > 0


def test_refund_status_enum():
    assert RefundStatus.requested.value == "requested"
    assert RefundStatus.succeeded.value == "succeeded"


def test_fc_phase2_docs_exist():
    assert (REPO_ROOT / "docs" / "ops" / "REFUND_RUNBOOK.md").is_file()
