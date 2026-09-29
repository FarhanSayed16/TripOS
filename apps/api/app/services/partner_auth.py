"""FC Phase 8 — partner API key generation and verification."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import get_password_hash
from app.models.enums import OrgStatus, UserRole
from app.models.partner import PartnerApp
from app.models.tenancy import Organization, OrganizationMember, User


DEFAULT_SCOPES = ["search", "quote", "pay", "booking"]


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key(env: str = "test") -> Tuple[str, str, str]:
    """
    Returns (full_key, prefix, key_hash).
    Format: tp_{env}_{prefix}_{secret}
    """
    env_safe = "live" if env == "live" else "test"
    prefix = secrets.token_hex(4)
    secret = secrets.token_urlsafe(24)
    full = f"tp_{env_safe}_{prefix}_{secret}"
    return full, prefix, hash_api_key(full)


def generate_webhook_secret() -> str:
    return secrets.token_urlsafe(32)


def parse_key_prefix(raw_key: str) -> Optional[str]:
    parts = (raw_key or "").strip().split("_")
    # tp_test_<prefix>_<secret> → 4 parts minimum
    if len(parts) < 4 or parts[0] != "tp":
        return None
    return parts[2]


async def authenticate_api_key(
    raw_key: str,
    db: AsyncSession,
    *,
    client_ip: Optional[str] = None,
) -> PartnerApp:
    if not settings.FC_PARTNER_API_ENABLED:
        raise AppError(
            "Partner API is disabled",
            status_code=403,
            error_code="PARTNER_API_DISABLED",
        )
    prefix = parse_key_prefix(raw_key)
    if not prefix:
        raise AppError("Invalid API key", status_code=401, error_code="PARTNER_UNAUTHORIZED")

    stmt = select(PartnerApp).where(
        PartnerApp.key_prefix == prefix,
        PartnerApp.deleted_at.is_(None),
    )
    app = (await db.execute(stmt)).scalar_one_or_none()
    if not app or not app.is_active:
        raise AppError("Invalid API key", status_code=401, error_code="PARTNER_UNAUTHORIZED")

    expected = app.key_hash
    actual = hash_api_key(raw_key)
    if not hmac.compare_digest(expected, actual):
        raise AppError("Invalid API key", status_code=401, error_code="PARTNER_UNAUTHORIZED")

    allow = app.ip_allowlist if isinstance(app.ip_allowlist, list) else None
    if allow and client_ip and client_ip not in allow:
        raise AppError(
            "Client IP not allowlisted",
            status_code=403,
            error_code="PARTNER_IP_DENIED",
        )

    app.last_used_at = datetime.now(timezone.utc)
    # Flush only — avoid mid-request commit; caller/endpoint commit persists it
    await db.flush()
    return app


async def ensure_service_user(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    partner_name: str,
) -> User:
    """Create a non-login service user bound to the partner org for quote ownership."""
    email = f"partner+{organization_id.hex[:12]}@tripos.internal"
    existing = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing:
        # Ensure membership
        mem = (
            await db.execute(
                select(OrganizationMember).where(
                    OrganizationMember.user_id == existing.id,
                    OrganizationMember.organization_id == organization_id,
                )
            )
        ).scalar_one_or_none()
        if not mem:
            db.add(
                OrganizationMember(
                    user_id=existing.id,
                    organization_id=organization_id,
                    role=UserRole.agent,
                )
            )
            await db.flush()
        return existing

    user = User(
        email=email,
        hashed_password=get_password_hash(secrets.token_urlsafe(32)),
        first_name="Partner",
        last_name=partner_name[:80],
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    db.add(
        OrganizationMember(
            user_id=user.id,
            organization_id=organization_id,
            role=UserRole.agent,
        )
    )
    await db.flush()
    return user


async def create_partner_app(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    name: str,
    env: str = "test",
    webhook_url: Optional[str] = None,
    rate_limit_per_minute: Optional[int] = None,
    scopes: Optional[list] = None,
    ip_allowlist: Optional[list] = None,
) -> tuple[PartnerApp, str]:
    org = await db.get(Organization, organization_id)
    if not org or org.deleted_at is not None:
        raise AppError("Organization not found", status_code=404)
    if org.status != OrgStatus.active:
        raise AppError("Organization must be active", status_code=400)

    service_user = await ensure_service_user(
        db, organization_id=organization_id, partner_name=name
    )
    raw_key, prefix, key_hash = generate_api_key(env=env)
    app = PartnerApp(
        id=uuid.uuid4(),
        organization_id=organization_id,
        service_user_id=service_user.id,
        name=name,
        key_prefix=prefix,
        key_hash=key_hash,
        env="live" if env == "live" else "test",
        webhook_url=webhook_url,
        webhook_secret=generate_webhook_secret(),
        scopes=scopes or list(DEFAULT_SCOPES),
        rate_limit_per_minute=rate_limit_per_minute
        or settings.FC_PARTNER_DEFAULT_RATE_LIMIT,
        ip_allowlist=ip_allowlist,
        is_active=True,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app, raw_key


async def rotate_partner_key(db: AsyncSession, app: PartnerApp) -> str:
    raw_key, prefix, key_hash = generate_api_key(env=app.env)
    app.key_prefix = prefix
    app.key_hash = key_hash
    app.rotated_at = datetime.now(timezone.utc)
    app.webhook_secret = app.webhook_secret or generate_webhook_secret()
    await db.commit()
    await db.refresh(app)
    return raw_key


async def load_partner_service_user(app: PartnerApp, db: AsyncSession) -> User:
    if not app.service_user_id:
        raise AppError(
            "Partner app missing service user",
            status_code=500,
            error_code="PARTNER_MISCONFIGURED",
        )
    stmt = (
        select(User)
        .options(selectinload(User.memberships))
        .where(User.id == app.service_user_id, User.deleted_at.is_(None))
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise AppError(
            "Partner service user not found",
            status_code=500,
            error_code="PARTNER_MISCONFIGURED",
        )
    user.active_organization_id = app.organization_id
    return user


def require_scope(app: PartnerApp, scope: str) -> None:
    scopes = app.scopes if isinstance(app.scopes, list) else []
    if scope not in scopes and "*" not in scopes:
        raise AppError(
            f"Partner key missing scope: {scope}",
            status_code=403,
            error_code="PARTNER_SCOPE_DENIED",
        )
