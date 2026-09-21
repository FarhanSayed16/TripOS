"""Sprint J — AuditEvent alignment, cancel IDOR, error codes, backoff (no DB)."""
from __future__ import annotations

import ast
import inspect
import py_compile
import uuid
from datetime import timedelta
from pathlib import Path

import pytest

from app.adapters.mock_adapter import MockAdapter
from app.adapters.tbo_adapter import TboAdapter
from app.core.inventory_errors import InventoryRevalidateError
from app.models.enums import BookingFailureReason
from app.schemas.inventory import NormalizedOffer, InventoryType
from app.services.audit import make_audit_event
from app.services.jobs import _map_failure_reason
from worker import BACKOFF_SCHEDULE, MAX_RETRIES


API_ROOT = Path(__file__).resolve().parents[1]


def test_audit_event_uses_entity_columns_not_resource():
    org_id = uuid.uuid4()
    event = make_audit_event(
        organization_id=org_id,
        action="payment.captured",
        entity_type="quote",
        entity_id="quote-1",
        metadata={"amount": 100},
    )
    assert event.entity_type == "quote"
    assert event.entity_id == "quote-1"
    assert event.metadata_payload == {"amount": 100}
    assert event.action == "payment.captured"
    assert "resource_type" not in event.__dict__
    assert "resource_id" not in event.__dict__


def test_audit_metadata_defaults_to_empty_dict():
    event = make_audit_event(
        organization_id=uuid.uuid4(),
        action="cancel.requested",
        entity_type="quote",
        entity_id="q",
    )
    assert event.metadata_payload == {}


def test_cancel_quote_filters_by_organization():
    """FIX-P21-02: cancel must org-scope Quote lookup (404, no leak)."""
    source = (API_ROOT / "app" / "api" / "quotes.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    cancel_fn = None
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "api_cancel_quote":
            cancel_fn = node
            break
    assert cancel_fn is not None, "api_cancel_quote missing"
    dumped = ast.dump(cancel_fn)
    assert "organization_id" in dumped
    assert "active_organization_id" in dumped


def test_quote_audit_reader_uses_entity_columns():
    source = (API_ROOT / "app" / "api" / "quotes.py").read_text(encoding="utf-8")
    assert "AuditEvent.entity_id" in source
    assert "AuditEvent.entity_type" in source
    assert "AuditEvent.resource_id" not in source
    assert "AuditEvent.resource_type" not in source


def test_map_failure_reason_timeout_to_supplier_timeout():
    assert _map_failure_reason("timeout") == BookingFailureReason.supplier_timeout
    assert _map_failure_reason("supplier_timeout") == BookingFailureReason.supplier_timeout
    assert _map_failure_reason("fare_changed") == BookingFailureReason.fare_changed
    assert _map_failure_reason("bogus") == BookingFailureReason.unknown


@pytest.mark.asyncio
async def test_mock_timeout_maps_to_supplier_timeout():
    adapter = MockAdapter()
    offer = NormalizedOffer(
        id="o1",
        supplier_code="mock_supplier",
        supplier_reference="MOCK-TIMEOUT-1",
        type=InventoryType.FLIGHT,
        total_amount=1000.0,
        base_amount=800.0,
        tax_amount=200.0,
        currency="INR",
        title="Timeout sim",
        raw_data={"simulate": "timeout"},
    )
    with pytest.raises(InventoryRevalidateError) as exc:
        await adapter.revalidate(offer)
    assert exc.value.error_code == "supplier_timeout"
    assert _map_failure_reason(exc.value.error_code) == BookingFailureReason.supplier_timeout


@pytest.mark.asyncio
async def test_tbo_revalidate_error_arg_order():
    """FIX-P21-05: (error_code, message) — not swapped."""
    adapter = TboAdapter()
    offer = NormalizedOffer(
        id="o1",
        supplier_code="tbo",
        supplier_reference="bad-ref-no-separator",
        type=InventoryType.FLIGHT,
        total_amount=1000.0,
        base_amount=800.0,
        tax_amount=200.0,
        currency="INR",
        title="Bad ref",
        raw_data={},
    )
    with pytest.raises(InventoryRevalidateError) as exc:
        await adapter.revalidate(offer)
    assert exc.value.error_code == "supplier_error"
    assert "supplier_reference" in exc.value.message.lower() or "Invalid" in exc.value.message


def test_backoff_schedule_matches_plan():
    assert MAX_RETRIES == 3
    assert BACKOFF_SCHEDULE == [
        timedelta(seconds=30),
        timedelta(minutes=2),
        timedelta(minutes=10),
    ]


def test_offline_pay_sets_run_at():
    source = inspect.getsource(
        __import__("app.services.payments", fromlist=["mark_quote_paid_offline"]).mark_quote_paid_offline
    )
    assert "run_at=" in source
    assert "customer_total" in source
    assert "write_audit" in source


def test_sprint_j_modules_compile():
    files = [
        API_ROOT / "app" / "services" / "audit.py",
        API_ROOT / "app" / "services" / "jobs.py",
        API_ROOT / "app" / "services" / "payments.py",
        API_ROOT / "app" / "api" / "quotes.py",
        API_ROOT / "app" / "adapters" / "tbo_adapter.py",
        API_ROOT / "app" / "adapters" / "mock_adapter.py",
        API_ROOT / "worker.py",
    ]
    for path in files:
        py_compile.compile(str(path), doraise=True)
