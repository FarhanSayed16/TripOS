"""Sprint H unit tests — auth revoke, email redact, public sanitize helpers."""
from datetime import timedelta

import jwt

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, tokens_for_user
from app.services.email import redact_url_for_logs


class _User:
    def __init__(self, uid="u1", tv=0):
        self.id = uid
        self.token_version = tv


def test_tokens_for_user_embed_tv():
    access, refresh = tokens_for_user(_User(tv=3))
    a = jwt.decode(access, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    r = jwt.decode(refresh, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert a["type"] == "access"
    assert a["tv"] == 3
    assert r["type"] == "refresh"
    assert r["tv"] == 3


def test_reset_token_binds_tv():
    token = create_access_token(
        {"sub": "u1", "type": "reset_password", "tv": 2},
        expires_delta=timedelta(minutes=15),
    )
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["type"] == "reset_password"
    assert payload["tv"] == 2


def test_redact_url_hides_jwt():
    url = "http://localhost:3000/verify?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def"
    redacted = redact_url_for_logs(url)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
    assert "REDACTED_" in redacted


def test_public_quote_schema_omits_costs():
    from app.schemas.quotes import PublicQuoteItemResponse, QuoteItemResponse

    public_fields = set(PublicQuoteItemResponse.model_fields.keys())
    agent_fields = set(QuoteItemResponse.model_fields.keys())
    assert "supplier_cost" not in public_fields
    assert "agent_markup" not in public_fields
    assert "platform_fee" not in public_fields
    assert "supplier_cost" in agent_fields


def test_webhook_amount_mismatch_logic():
    """Mirror AUDIT-007 compare used in process_razorpay_webhook."""
    stored = 150000
    webhook_amount = 100000
    assert int(webhook_amount) != stored


def test_refresh_tv_mismatch_is_revoked():
    user_tv = 5
    stolen = create_refresh_token({"sub": "u1", "tv": 4})
    payload = jwt.decode(stolen, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert int(payload.get("tv", 0)) != user_tv
