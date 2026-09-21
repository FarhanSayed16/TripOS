from datetime import datetime, timedelta, timezone
import secrets
import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from app.core.config import settings

_ph = PasswordHasher()


def _is_bcrypt_hash(hashed_password: str) -> bool:
    return hashed_password.startswith(("$2a$", "$2b$", "$2y$"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify argon2 (preferred) or legacy bcrypt hashes from pre-Sprint-C seeds."""
    if _is_bcrypt_hash(hashed_password):
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except (ValueError, TypeError):
            return False
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(hashed_password: str) -> bool:
    if _is_bcrypt_hash(hashed_password):
        return True
    try:
        return _ph.check_needs_rehash(hashed_password)
    except Exception:
        return True


def get_password_hash(password: str) -> str:
    return _ph.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Mint a short-lived JWT. Defaults to type=access for Bearer auth.
    Callers may pass type=verify | reset_password for email links (rejected by get_current_user).
    Include tv (token_version) for session revoke.
    """
    to_encode = data.copy()
    if "type" not in to_encode:
        to_encode["type"] = "access"
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Rotating refresh JWT with jti + tv. Invalidated when user.token_version bumps."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh", "jti": secrets.token_urlsafe(16)})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def tokens_for_user(user) -> tuple[str, str]:
    """Mint access + refresh bound to the user's current token_version."""
    tv = int(getattr(user, "token_version", 0) or 0)
    access = create_access_token(data={"sub": str(user.id), "tv": tv})
    refresh = create_refresh_token(data={"sub": str(user.id), "tv": tv})
    return access, refresh
