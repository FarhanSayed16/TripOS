"""FC Phase 5 — locale resolution + localized errors + WhatsApp templates."""
from __future__ import annotations

from app.core.exceptions import AppError, app_error_handler
from app.services.i18n import (
    localize_error,
    normalize_locale,
    parse_accept_language,
)
from app.services.message_templates import (
    amount_line_for_locale,
    whatsapp_quote_template,
)


def test_normalize_locale_en_hi():
    assert normalize_locale("en") == "en"
    assert normalize_locale("hi-IN") == "hi"
    assert normalize_locale("HI") == "hi"
    assert normalize_locale("fr") == "en"  # fallback


def test_parse_accept_language_prefers_hi():
    assert parse_accept_language("hi-IN,hi;q=0.9,en;q=0.8") == "hi"
    assert parse_accept_language("en-US,en;q=0.9") == "en"
    assert parse_accept_language(None) is None


def test_localize_error_hi():
    msg = localize_error("NOT_FOUND", "hi", "Resource not found")
    assert "नहीं" in msg or "मिला" in msg
    assert localize_error("NOT_FOUND", "en", "x") == "Resource not found"


def test_localize_error_unknown_code_falls_back_to_message():
    assert localize_error("SOME_NEW_CODE", "hi", "Original English") == "Original English"


def test_whatsapp_template_hi_contains_devanagari():
    body = whatsapp_quote_template(
        locale="hi",
        first_name="राज",
        amount_line="आपका यात्रा कोट INR 1,000.00 का है।\n\n",
        public_url="https://example.com/q/abc",
        valid_until="28/09/2026",
    )
    assert "नमस्ते" in body
    assert "https://example.com/q/abc" in body


def test_whatsapp_template_en():
    body = whatsapp_quote_template(
        locale="en",
        first_name="Raj",
        amount_line="Here is your travel quote for INR 1,000.00.\n\n",
        public_url="https://example.com/q/abc",
        valid_until="September 28, 2026",
    )
    assert body.startswith("Hi Raj")


def test_amount_line_hi_same_currency():
    line = amount_line_for_locale(
        locale="hi",
        display_cur="INR",
        display_amt=1000,
        charge="INR",
        total_charge=1000,
        fx_as_of_str=None,
    )
    assert "कोट" in line


import pytest
from starlette.requests import Request


@pytest.mark.asyncio
async def test_app_error_handler_localizes_with_accept_language():
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [(b"accept-language", b"hi")],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
    }
    request = Request(scope)
    request.state.locale = "hi"
    exc = AppError("Resource not found", status_code=404, error_code="NOT_FOUND")
    resp = await app_error_handler(request, exc)
    assert resp.status_code == 404
    body = resp.body.decode()
    assert "NOT_FOUND" in body
    assert "locale" in body
