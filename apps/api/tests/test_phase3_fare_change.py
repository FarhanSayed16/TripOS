"""Live-inventory Phase 3 — fare-change payload, quote TTL, pay/book metric."""
from __future__ import annotations

import py_compile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.inventory_errors import InventoryRevalidateError
from app.schemas.inventory import InventoryType, NormalizedOffer
from app.services.quotes import _apply_fare_change_to_offer, _quote_ttl_hours


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def test_quote_ttl_from_settings():
    s = Settings(_env_file=None)
    assert s.QUOTE_FLIGHT_TTL_HOURS == 4
    assert s.QUOTE_HOTEL_TTL_HOURS == 12
    with patch("app.services.quotes.settings") as mock_s:
        mock_s.QUOTE_FLIGHT_TTL_HOURS = 2
        mock_s.QUOTE_HOTEL_TTL_HOURS = 8
        assert _quote_ttl_hours(InventoryType.FLIGHT) == 2
        assert _quote_ttl_hours("hotel") == 8


@pytest.mark.asyncio
async def test_mock_fare_changed_includes_amount_delta():
    from app.adapters.mock_adapter import MockAdapter

    adapter = MockAdapter()
    offer = NormalizedOffer(
        id="o1",
        supplier_code="mock_supplier",
        supplier_reference="MOCK-FARE-CHG-1",
        type=InventoryType.FLIGHT,
        total_amount=1000.0,
        base_amount=800.0,
        tax_amount=200.0,
        currency="INR",
        title="Fare chg",
        raw_data={"simulate": "fare_changed"},
    )
    with pytest.raises(InventoryRevalidateError) as exc:
        await adapter.revalidate(offer)
    assert exc.value.error_code == "fare_changed"
    assert exc.value.previous_total_paise == 100000
    assert exc.value.new_total_paise == 108000


def test_apply_fare_change_clears_simulate():
    offer = NormalizedOffer(
        id="o1",
        supplier_code="mock_supplier",
        supplier_reference="MOCK-FARE-CHG-1",
        type=InventoryType.FLIGHT,
        total_amount=1000.0,
        base_amount=800.0,
        tax_amount=200.0,
        currency="INR",
        title="Fare chg",
        raw_data={"simulate": "fare_changed"},
    )
    refreshed = _apply_fare_change_to_offer(offer, 108000)
    assert refreshed.total_amount == 1080.0
    assert "simulate" not in (refreshed.raw_data or {})
    assert "FARE-CHG" not in (refreshed.supplier_reference or "").upper()
    assert refreshed.raw_data.get("fare_accepted") is True


@pytest.mark.asyncio
async def test_payment_revalidate_failure_does_not_create_link():
    """Guardrail: FARE_CHANGED must raise before payment link creation."""
    from app.services import payments as pay_mod
    from app.core.inventory_errors import InventoryRevalidateError

    quote = MagicMock()
    quote.organization_id = "org-1"
    item = MagicMock()
    item.supplier_cost = 100000
    snap = MagicMock()
    snap.offer_data = {
        "id": "o1",
        "supplier_code": "mock_supplier",
        "supplier_reference": "MOCK-FARE-CHG",
        "type": "flight",
        "total_amount": 1000.0,
        "base_amount": 800.0,
        "tax_amount": 200.0,
        "currency": "INR",
        "title": "x",
        "raw_data": {"simulate": "fare_changed"},
    }
    item.offer_snapshot = snap
    quote.items = [item]
    db = AsyncMock()

    with patch(
        "app.services.payments.revalidate_normalized_offer",
        new_callable=AsyncMock,
        side_effect=InventoryRevalidateError(
            "fare_changed",
            "Fare changed",
            previous_total_paise=100000,
            new_total_paise=108000,
        ),
    ):
        with pytest.raises(AppError) as exc:
            await pay_mod._revalidate_quote_items(quote, db)

    assert exc.value.error_code == "FARE_CHANGED"
    assert exc.value.details["previous_total_paise"] == 100000
    assert exc.value.details["new_total_paise"] == 108000


@pytest.mark.asyncio
async def test_app_error_handler_includes_fare_fields():
    from app.core.exceptions import AppError, app_error_handler
    import json

    exc = AppError(
        "Fare changed",
        status_code=409,
        error_code="FARE_CHANGED",
        details={"previous_total_paise": 1, "new_total_paise": 2},
    )
    resp = await app_error_handler(MagicMock(), exc)
    data = json.loads(resp.body)
    assert data["previous_total_paise"] == 1
    assert data["new_total_paise"] == 2


def test_admin_analytics_exposes_captured_failed_metric():
    source = (API_ROOT / "app" / "api" / "admin.py").read_text(encoding="utf-8")
    assert "payment_captured_booking_failed_7d" in source


def test_fe_fare_change_modal_source():
    page = (
        REPO_ROOT
        / "apps"
        / "web"
        / "src"
        / "app"
        / "(agent)"
        / "app"
        / "quotes"
        / "[id]"
        / "page.tsx"
    ).read_text(encoding="utf-8")
    assert "Accept new fare" in page
    assert "previous_total_paise" in page
    assert "useRefreshQuoteMutation" in page


def test_phase3_modules_compile():
    for rel in (
        "app/core/inventory_errors.py",
        "app/core/exceptions.py",
        "app/services/payments.py",
        "app/services/quotes.py",
        "app/api/admin.py",
        "app/adapters/mock_adapter.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)
