import uuid
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin
from .enums import UserRole, OrgStatus

class OrganizationDomain(Base, TimestampMixin):
    __tablename__ = "organization_domains"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    verification_token: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="domains")

class Organization(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "organizations"

    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    brand_name: Mapped[str] = mapped_column(String(255))
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    primary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    parent_organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    status: Mapped[OrgStatus] = mapped_column(default=OrgStatus.pending_approval)

    # Relationships
    domains: Mapped[List["OrganizationDomain"]] = relationship("OrganizationDomain", back_populates="organization", cascade="all, delete-orphan")
    members: Mapped[List["OrganizationMember"]] = relationship("OrganizationMember", back_populates="organization")
    customers: Mapped[List["Customer"]] = relationship("Customer", back_populates="organization")
    quotes: Mapped[List["Quote"]] = relationship("Quote", back_populates="organization")

class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    first_name: Mapped[str] = mapped_column(String(100), default="")
    last_name: Mapped[str] = mapped_column(String(100), default="")
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_platform_admin: Mapped[bool] = mapped_column(default=False)
    # Bumped on logout / password reset / refresh rotate — invalidates prior JWTs (AUDIT-004/018)
    token_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Relationships
    memberships: Mapped[List["OrganizationMember"]] = relationship("OrganizationMember", back_populates="user")

class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    role: Mapped[UserRole] = mapped_column(default=UserRole.agent)

    user: Mapped["User"] = relationship("User", back_populates="memberships")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="members")
