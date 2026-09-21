"""Sprint I — payments mode helpers (no live network)."""
from app.services.razorpay_client import razorpay_live_configured
from app.core.config import settings


def test_razorpay_live_not_configured_by_default(monkeypatch):
    monkeypatch.setattr(settings, "PAYMENTS_MODE", "mock")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", "")
    assert razorpay_live_configured() is False


def test_razorpay_live_configured_when_mode_and_keys(monkeypatch):
    monkeypatch.setattr(settings, "PAYMENTS_MODE", "razorpay")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "rzp_test_x")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", "secret")
    assert razorpay_live_configured() is True


def test_platform_fee_default_zero():
    assert int(settings.PLATFORM_FEE_PAISE) == 0
