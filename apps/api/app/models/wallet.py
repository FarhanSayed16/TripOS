import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

class WalletLedgerEntry(Base, TimestampMixin):
    __tablename__ = "wallet_ledger"
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bookings.id"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(30))  # commission_earned | commission_paid | adjustment
    amount_paise: Mapped[int] = mapped_column(Integer)  # positive = credit, negative = debit
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | available | settled
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization")
    booking = relationship("Booking")

class CommissionRule(Base, TimestampMixin):
    __tablename__ = "commission_rules"
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("organizations.id"), nullable=True)  # NULL = platform default
    product_type: Mapped[str] = mapped_column(String(20), default="flight")  # flight | hotel | all
    rule_type: Mapped[str] = mapped_column(String(20), default="percentage")  # percentage | flat_paise
    value: Mapped[int] = mapped_column(Integer)  # e.g. 70 = 70% of agent_markup goes to agent
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization = relationship("Organization")
