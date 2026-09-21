"""Sprint G security unit tests (no DB required)."""
from datetime import timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token


def test_access_token_defaults_type_access():
    token = create_access_token({"sub": "user-1"})
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["type"] == "access"
    assert payload["sub"] == "user-1"


def test_verify_token_keeps_explicit_type():
    token = create_access_token({"sub": "user-1", "type": "verify"})
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["type"] == "verify"


def test_reset_token_keeps_explicit_type():
    token = create_access_token(
        {"sub": "user-1", "type": "reset_password"},
        expires_delta=timedelta(minutes=15),
    )
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["type"] == "reset_password"


def test_refresh_token_type():
    token = create_refresh_token({"sub": "user-1"})
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_deps_module_compiles():
    """AUDIT-001 regression: deps.py must parse."""
    import py_compile
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "app" / "api" / "deps.py"
    py_compile.compile(str(path), doraise=True)


def test_non_access_types_are_rejected_by_policy():
    """Mirrors get_current_user type gate without FastAPI/DB."""
    for t in ("verify", "reset_password", "refresh"):
        token = (
            create_refresh_token({"sub": "u"})
            if t == "refresh"
            else create_access_token({"sub": "u", "type": t})
        )
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload.get("type", "access") != "access"
