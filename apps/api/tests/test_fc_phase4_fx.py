"""FC Phase 4 — FX conversion math + money envelope (display only)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.services.fx import (
    convert_major,
    convert_paise_to_display_major,
    money_display_dict,
    normalize_currency,
    round_money,
    FxQuote,
    paise_money_display,
)


def test_normalize_currency_uppercases():
    assert normalize_currency("usd") == "USD"
    assert normalize_currency("INR") == "INR"


def test_normalize_currency_rejects_bad():
    with pytest.raises(ValueError):
        normalize_currency("US")
    with pytest.raises(ValueError):
        normalize_currency("123")


def test_round_money_half_up():
    assert round_money(Decimal("10.125")) == Decimal("10.13")
    assert round_money(Decimal("10.124")) == Decimal("10.12")
    assert round_money(Decimal("1.005")) == Decimal("1.01")


def test_convert_major_inr_to_usd():
    rate = Decimal("0.012")
    assert convert_major(10000, rate=rate) == Decimal("120.00")


def test_convert_paise():
    rate = Decimal("0.012")
    # 1_000_000 paise = ₹10,000 → $120.00
    assert convert_paise_to_display_major(1_000_000, rate=rate) == Decimal("120.00")


def test_money_display_identity_same_currency():
    out = money_display_dict(currency="INR", amount_major=1500.5, fx=None)
    assert out["currency"] == "INR"
    assert out["display_currency"] == "INR"
    assert out["display_amount"] == 1500.5
    assert out["fx_rate"] == 1.0


def test_money_display_converts_without_mutating_charge():
    fx = FxQuote(
        base_currency="INR",
        quote_currency="USD",
        rate=Decimal("0.012"),
        as_of=datetime.now(timezone.utc),
        source="test",
    )
    out = money_display_dict(
        currency="INR",
        amount_major=10000,
        fx=fx,
        display_currency="USD",
    )
    assert out["currency"] == "INR"
    assert out["amount"] == 10000.0
    assert out["display_currency"] == "USD"
    assert out["display_amount"] == 120.0
    assert out["fx_rate"] == 0.012


def test_paise_money_display_snapshot():
    fx = FxQuote(
        base_currency="INR",
        quote_currency="AED",
        rate=Decimal("0.044"),
        as_of=datetime(2026, 9, 28, tzinfo=timezone.utc),
        source="manual",
    )
    out = paise_money_display(
        100_000,  # ₹1000
        charge_currency="INR",
        fx=fx,
        display_currency="AED",
    )
    assert out["amount"] == 1000.0
    assert out["display_amount"] == 44.0
    assert out["display_currency"] == "AED"
    assert out["fx_source"] == "manual"


def test_supplier_fare_never_equals_display_when_fx_applied():
    """Guardrail: display conversion must not overwrite charge amount."""
    fx = FxQuote(
        base_currency="INR",
        quote_currency="USD",
        rate=Decimal("0.012"),
        as_of=datetime.now(timezone.utc),
        source="test",
    )
    supplier_total = 8500.0
    money = money_display_dict(
        currency="INR",
        amount_major=supplier_total,
        fx=fx,
        display_currency="USD",
    )
    assert money["amount"] == supplier_total
    assert money["display_amount"] != supplier_total
