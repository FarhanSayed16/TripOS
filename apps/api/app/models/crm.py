import uuid
from typing import List, Optional
from sqlalchemy import String, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin


class Customer(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customers"
    __table_args__ = (
        Index(
            "uq_customers_org_phone_active",
            "organization_id",
            "phone_e164",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_e164: Mapped[str] = mapped_column(String(20), index=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="customers")
    quotes: Mapped[List["Quote"]] = relationship("Quote", back_populates="customer")
