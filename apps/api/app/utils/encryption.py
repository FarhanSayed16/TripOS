"""
Supplier credential encryption.

V1: stub only — safe for local/dev placeholders. Must not store real
supplier secrets until Fernet/KMS is implemented (Phase 25).
"""
import os


class EncryptionNotReadyError(RuntimeError):
    """Raised when stub encrypt/decrypt would be used in production."""


def _is_production() -> bool:
    env = os.getenv("ENV", "development")
    try:
        from app.core.config import settings

        env = settings.ENV
    except Exception:
        pass
    return str(env).lower() == "production"


def encrypt_credential(raw_secret: str) -> str:
    """
    Stub encrypt. Forbidden when ENV=production so real secrets cannot
    be persisted as `enc_<plaintext>`.
    """
    if _is_production():
        raise EncryptionNotReadyError(
            "Stub encrypt_credential cannot run when ENV=production. "
            "Implement Fernet/KMS before storing supplier secrets."
        )
    return f"enc_{raw_secret}"


def decrypt_credential(encrypted_secret: str) -> str:
    """Stub decrypt. Forbidden in production for the same reason."""
    if _is_production():
        raise EncryptionNotReadyError(
            "Stub decrypt_credential cannot run when ENV=production. "
            "Implement Fernet/KMS before reading supplier secrets."
        )
    if encrypted_secret.startswith("enc_"):
        return encrypted_secret[4:]
    return encrypted_secret
