import jwt
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import get_db  # re-export for API routers
from app.models import User, UserRole, Organization
from app.models.tenancy import OrganizationMember
from app.models.enums import OrgStatus

security = HTTPBearer()

__all__ = [
    "security",
    "get_db",
    "get_current_user",
    "require_platform_admin",
    "require_org_admin",
    "require_active_org",
]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise AppError("Invalid token payload", status_code=401, error_code="UNAUTHORIZED")
        # AUDIT-003: reject verify / reset / refresh JWTs used as Bearer access
        token_type = payload.get("type", "access")
        if token_type != "access":
            raise AppError(
                "Invalid token type for this endpoint",
                status_code=401,
                error_code="UNAUTHORIZED",
            )
        token_tv = int(payload.get("tv", 0))
    except AppError:
        raise
    except jwt.PyJWTError:
        raise AppError("Could not validate credentials", status_code=401, error_code="UNAUTHORIZED")

    stmt = (
        select(User)
        .options(selectinload(User.memberships).selectinload(OrganizationMember.organization))
        .where(User.id == user_id, User.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AppError("User not found", status_code=401, error_code="UNAUTHORIZED")
    if not user.is_verified:
        raise AppError("User is not verified", status_code=403, error_code="FORBIDDEN")

    # AUDIT-004: reject access tokens minted before a logout/reset/refresh rotate
    if token_tv != int(user.token_version or 0):
        raise AppError("Token revoked", status_code=401, error_code="TOKEN_REVOKED")

    # V1: single org per user — first membership is active org context.
    # Multi-org switching is out of scope until V3; see docs/architecture/phase-4-schema-decisions.md
    user.active_organization_id = (
        user.memberships[0].organization_id if user.memberships else None
    )

    return user


async def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_platform_admin:
        raise AppError("Platform Admin privileges required", status_code=403, error_code="FORBIDDEN")
    return current_user


async def require_org_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.memberships:
        raise AppError("Not part of any organization", status_code=403, error_code="FORBIDDEN")

    active_membership = next(
        (m for m in current_user.memberships if m.organization_id == current_user.active_organization_id),
        None,
    )

    role = active_membership.role if active_membership else None
    if role != UserRole.admin and role != "admin":
        raise AppError("Organization Admin privileges required", status_code=403, error_code="FORBIDDEN")

    return current_user


async def require_active_org(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    AUDIT-006: commercial routes require an active organization.
    Pending / inactive agencies can still auth and hit /me, but not CRM/search/quotes/pay.
    """
    if not current_user.active_organization_id:
        raise AppError(
            "User must belong to an organization",
            status_code=403,
            error_code="ORG_REQUIRED",
        )

    org = await db.get(Organization, current_user.active_organization_id)
    if org is None or org.deleted_at is not None:
        raise AppError("Organization not found", status_code=403, error_code="ORG_NOT_FOUND")
    if org.status != OrgStatus.active:
        raise AppError(
            "Organization is not active. Wait for platform approval.",
            status_code=403,
            error_code="ORG_INACTIVE",
        )

    return current_user
