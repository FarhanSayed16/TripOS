from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import jwt
import re

from app.core.security import (
    verify_password,
    create_access_token,
    get_password_hash,
    tokens_for_user,
    needs_rehash,
)
from app.core.exceptions import AppError
from app.core.config import settings
from app.db.session import get_db
from app.models import User, Organization, OrganizationMember, UserRole, OrgStatus
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    SignupRequest,
    VerifyRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.api.deps import get_current_user
from app.services.email import send_verification_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "org"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        path="/",
        samesite="lax",
        secure=settings.cookie_secure,
    )


def _user_response(user: User, org_status: str | None = None) -> UserResponse:
    active_org_id = getattr(user, "active_organization_id", None)
    org_role = None
    if user.memberships and active_org_id:
        membership = next((m for m in user.memberships if m.organization_id == active_org_id), None)
        if membership:
            org_role = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
    elif user.memberships:
        membership = user.memberships[0]
        org_role = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
        active_org_id = membership.organization_id

    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        active_organization_id=active_org_id,
        org_role=org_role,
        org_status=org_status,
        is_platform_admin=bool(user.is_platform_admin),
    )


async def _bump_token_version(user: User, db: AsyncSession) -> int:
    user.token_version = int(user.token_version or 0) + 1
    await db.commit()
    await db.refresh(user)
    return user.token_version


@router.post("/signup")
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise AppError("Email already registered", status_code=400)

    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        is_verified=False,
        is_platform_admin=False,
    )
    db.add(user)
    await db.flush()

    brand_name = f"{data.first_name}'s Agency".strip()
    slug = f"{_slugify(brand_name)}-{str(user.id)[:8]}"
    org = Organization(
        brand_name=brand_name,
        slug=slug,
        status=OrgStatus.pending_approval,
    )
    db.add(org)
    await db.flush()

    member = OrganizationMember(
        user_id=user.id,
        organization_id=org.id,
        role=UserRole.admin,
    )
    db.add(member)
    await db.commit()

    token = create_access_token(data={"sub": str(user.id), "type": "verify"})
    await send_verification_email(user.email, token)

    return {"message": "Signup successful. Please check your email to verify your account."}


@router.post("/verify")
async def verify(data: VerifyRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(data.token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "verify":
            raise ValueError()
        user_id = payload.get("sub")
    except Exception:
        raise AppError("Invalid or expired token", status_code=400)

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise AppError("User not found", status_code=404)

    user.is_verified = True
    await db.commit()
    return {"message": "Email verified successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == data.email, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise AppError("Invalid email or password", status_code=401, error_code="INVALID_CREDENTIALS")
    if not user.is_verified:
        raise AppError("User is not verified", status_code=403, error_code="FORBIDDEN")

    if needs_rehash(user.hashed_password):
        user.hashed_password = get_password_hash(data.password)
        await db.commit()

    access_token, refresh_token = tokens_for_user(user)
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Rotate refresh cookie (AUDIT-004).
    On success: bump token_version so the previous refresh JWT cannot be reused.
    """
    token = request.cookies.get("refresh_token")
    if not token:
        raise AppError("No refresh token", status_code=401)

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError()
        user_id = payload.get("sub")
        token_tv = int(payload.get("tv", 0))
    except Exception:
        _clear_refresh_cookie(response)
        raise AppError("Invalid refresh token", status_code=401)

    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_verified:
        _clear_refresh_cookie(response)
        raise AppError("Invalid user", status_code=401)

    if token_tv != int(user.token_version or 0):
        _clear_refresh_cookie(response)
        raise AppError("Refresh token revoked", status_code=401, error_code="TOKEN_REVOKED")

    await _bump_token_version(user, db)
    access_token, new_refresh = tokens_for_user(user)
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Clear cookie and bump token_version when refresh JWT is present (AUDIT-004)."""
    token = request.cookies.get("refresh_token")
    if token:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            if payload.get("type") == "refresh" and payload.get("sub"):
                stmt = select(User).where(User.id == payload["sub"], User.deleted_at.is_(None))
                user = (await db.execute(stmt)).scalar_one_or_none()
                if user:
                    await _bump_token_version(user, db)
        except Exception:
            pass
    _clear_refresh_cookie(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(User)
        .options(selectinload(User.memberships).selectinload(OrganizationMember.organization))
        .where(User.id == current_user.id)
    )
    result = await db.execute(stmt)
    user = result.scalar_one()
    user.active_organization_id = getattr(current_user, "active_organization_id", None)

    org_status = None
    if user.active_organization_id and user.memberships:
        membership = next(
            (m for m in user.memberships if m.organization_id == user.active_organization_id),
            user.memberships[0],
        )
        if membership and membership.organization:
            org_status = (
                membership.organization.status.value
                if hasattr(membership.organization.status, "value")
                else str(membership.organization.status)
            )

    return _user_response(user, org_status=org_status)


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == data.email, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        from datetime import timedelta

        # Bind reset token to current token_version (AUDIT-018)
        tv = int(user.token_version or 0)
        token = create_access_token(
            data={"sub": str(user.id), "type": "reset_password", "tv": tv},
            expires_delta=timedelta(minutes=15),
        )
        await send_password_reset_email(user.email, token)

    return {"message": "If an account exists, a recovery email has been sent."}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(data.token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "reset_password":
            raise ValueError()
        user_id = payload.get("sub")
        token_tv = int(payload.get("tv", 0))
    except Exception:
        raise AppError("Invalid or expired reset token", status_code=400)

    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise AppError("User not found", status_code=404)

    if token_tv != int(user.token_version or 0):
        raise AppError("Reset token already used or revoked", status_code=400, error_code="TOKEN_REVOKED")

    user.hashed_password = get_password_hash(data.new_password)
    # Invalidate this reset token + any active sessions
    user.token_version = int(user.token_version or 0) + 1
    await db.commit()

    return {"message": "Password has been successfully reset."}
