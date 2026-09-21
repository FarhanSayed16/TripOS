"""Public token helpers for quotes and similar share links."""
import secrets


def generate_public_token(nbytes: int = 32) -> str:
    """URL-safe token for quotes.public_token (and similar)."""
    return secrets.token_urlsafe(nbytes)
