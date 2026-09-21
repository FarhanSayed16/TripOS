"""Encryption stub guards (FIX-P11-18)."""
import pytest

from app.utils.encryption import (
    EncryptionNotReadyError,
    decrypt_credential,
    encrypt_credential,
)


def test_stub_encrypt_decrypt_in_dev(monkeypatch):
    monkeypatch.setenv("ENV", "development")
    enc = encrypt_credential("secret")
    assert enc == "enc_secret"
    assert decrypt_credential(enc) == "secret"


def test_stub_forbidden_in_production(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    # Force os.getenv path even if Settings import succeeds with different ENV
    monkeypatch.setattr(
        "app.utils.encryption._is_production",
        lambda: True,
    )
    with pytest.raises(EncryptionNotReadyError):
        encrypt_credential("real-supplier-secret")
    with pytest.raises(EncryptionNotReadyError):
        decrypt_credential("enc_x")
