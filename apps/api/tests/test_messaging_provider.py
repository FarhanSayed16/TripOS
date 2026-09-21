"""Messaging provider port (FIX-P11-17)."""
from app.services.messaging_provider import WaMeMessagingProvider, get_messaging_provider


def test_wa_me_url_encoding():
    p = WaMeMessagingProvider()
    url = p.build_outbound_url("+919876543210", "Hi there\n\nSee quote")
    assert url.startswith("https://wa.me/919876543210?text=")
    assert "Hi" in url


def test_get_provider_whatsapp():
    assert get_messaging_provider("whatsapp").channel == "whatsapp"


def test_get_provider_unknown():
    import pytest

    with pytest.raises(ValueError):
        get_messaging_provider("sms")
