import uuid
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base, TimestampMixin, SoftDeleteMixin

class Package(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "packages"
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    destination: Mapped[str] = mapped_column(String(100))
    duration_days: Mapped[int] = mapped_column(Integer)
    base_price_paise: Mapped[int] = mapped_column(Integer)  # suggested customer price
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | published | archived
    cover_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    items: Mapped[List["PackageItem"]] = relationship(back_populates="package", cascade="all, delete-orphan")
    organization = relationship("Organization")
    created_by_user = relationship("User")

class PackageItem(Base, TimestampMixin):
    __tablename__ = "package_items"
    package_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("packages.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(20))  # flight | hotel | activity | transfer
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_cost_paise: Mapped[int] = mapped_column(Integer)
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    search_params: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # pre-fill search for this item
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    package: Mapped["Package"] = relationship(back_populates="items")
