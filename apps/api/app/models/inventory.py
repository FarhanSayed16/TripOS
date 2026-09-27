import uuid
from datetime import date
from typing import List
from sqlalchemy import String, ForeignKey, Boolean, Date, Integer, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)

class SupplierCredential(Base, TimestampMixin):
    __tablename__ = "supplier_credentials"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"))
    encrypted_payload: Mapped[str] = mapped_column(String)
    
    def set_encrypted_payload(self, plaintext: str) -> None:
        from app.core.encryption import encrypt_string
        self.encrypted_payload = encrypt_string(plaintext)
        
    def get_decrypted_payload(self) -> str:
        from app.core.encryption import decrypt_string
        return decrypt_string(self.encrypted_payload)

class SupplierConfig(Base, TimestampMixin):
    __tablename__ = "supplier_configs"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"))
    is_enabled: Mapped[bool] = mapped_column(default=True)

class SearchRequest(Base, TimestampMixin):
    __tablename__ = "search_requests"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    payload: Mapped[dict] = mapped_column(JSONB)

class OfferSnapshot(Base, TimestampMixin):
    __tablename__ = "offer_snapshots"

    search_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("search_requests.id"))
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"))
    supplier_offer_id: Mapped[str] = mapped_column(String)
    offer_data: Mapped[dict] = mapped_column(JSONB)

    quote_items: Mapped[List["QuoteItem"]] = relationship(
        "QuoteItem",
        back_populates="offer_snapshot",
    )


class SupplierUsageDaily(Base):
    """Rolling daily rollup of live supplier calls (live-inventory readiness Phase 1)."""

    __tablename__ = "supplier_usage_daily"
    __table_args__ = (PrimaryKeyConstraint("day", "supplier_code"),)

    day: Mapped[date] = mapped_column(Date, nullable=False)
    supplier_code: Mapped[str] = mapped_column(String(50), nullable=False)
    searches: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    revalidates: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    books: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    confirmed_bookings: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class SupplierUsageDailyOrg(Base):
    """Per-org daily rollup for L2B brakes (live-inventory readiness Phase 4)."""

    __tablename__ = "supplier_usage_daily_org"
    __table_args__ = (PrimaryKeyConstraint("day", "organization_id", "supplier_code"),)

    day: Mapped[date] = mapped_column(Date, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    supplier_code: Mapped[str] = mapped_column(String(50), nullable=False)
    searches: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    revalidates: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    books: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    confirmed_bookings: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
