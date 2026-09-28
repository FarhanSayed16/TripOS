import uuid
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, ForeignKey, DateTime, Integer, Text, Numeric, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import QuoteStatus, PaymentStatus, BookingStatus, BookingFailureReason, JobStatus, RefundStatus

class Quote(Base, TimestampMixin):
    __tablename__ = "quotes"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"))
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    public_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[QuoteStatus] = mapped_column(default=QuoteStatus.draft)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # FC Phase 4 — display FX snapshot (charge stays settle currency)
    charge_currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR")
    display_currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR")
    fx_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    fx_as_of: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    fx_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="quotes")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="quotes")
    items: Mapped[List["QuoteItem"]] = relationship("QuoteItem", back_populates="quote")
    passengers: Mapped[List["QuotePassenger"]] = relationship("QuotePassenger", back_populates="quote")
    payment: Mapped[Optional["Payment"]] = relationship("Payment", back_populates="quote", uselist=False)
    booking: Mapped[Optional["Booking"]] = relationship("Booking", back_populates="quote", uselist=False)

class QuoteItem(Base, TimestampMixin):
    __tablename__ = "quote_items"

    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"))
    offer_snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("offer_snapshots.id"))
    supplier_cost: Mapped[int] = mapped_column(Integer)  # Currency in smallest unit (e.g. paise)
    agent_markup: Mapped[int] = mapped_column(Integer)
    platform_fee: Mapped[int] = mapped_column(Integer)
    customer_total: Mapped[int] = mapped_column(Integer)

    quote: Mapped["Quote"] = relationship("Quote", back_populates="items")
    offer_snapshot: Mapped["OfferSnapshot"] = relationship(
        "OfferSnapshot",
        back_populates="quote_items",
    )
class QuotePassenger(Base, TimestampMixin):
    __tablename__ = "quote_passengers"

    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    passport_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    quote: Mapped["Quote"] = relationship("Quote", back_populates="passengers")

class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"), unique=True)
    gateway_payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gateway_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_link_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.pending)
    amount: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True)

    quote: Mapped["Quote"] = relationship("Quote", back_populates="payment")
    refunds: Mapped[List["Refund"]] = relationship("Refund", back_populates="payment")

class Refund(Base, TimestampMixin):
    __tablename__ = "refunds"

    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id"), index=True)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True, index=True
    )
    amount: Mapped[int] = mapped_column(Integer)
    gateway_refund_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[RefundStatus] = mapped_column(
        SAEnum(
            RefundStatus,
            name="refundstatus",
            create_type=False,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=RefundStatus.requested,
    )
    reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    payment: Mapped["Payment"] = relationship("Payment", back_populates="refunds")

class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"), unique=True)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True, index=True
    )
    status: Mapped[BookingStatus] = mapped_column(default=BookingStatus.pending)
    supplier_pnr: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    # FC Phase 1 — richer ticket refs from live suppliers
    supplier_booking_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ticket_numbers: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    failure_reason: Mapped[Optional[BookingFailureReason]] = mapped_column(nullable=True)

    quote: Mapped["Quote"] = relationship("Quote", back_populates="booking")

class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"))
    sender_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    channel: Mapped[str] = mapped_column(String(50)) # e.g. "whatsapp"
    content: Mapped[str] = mapped_column(String)

class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(100))
    metadata_payload: Mapped[dict] = mapped_column(JSONB)

class JobOutbox(Base, TimestampMixin):
    __tablename__ = "jobs_outbox"

    # PG column type is native enum `jobstatus` (see early migrations)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(
            JobStatus,
            name="jobstatus",
            create_type=False,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=JobStatus.pending,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)

class FollowUp(Base, TimestampMixin):
    __tablename__ = "follow_ups"

    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(30))  # auto_24h | auto_48h | manual
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | sent | snoozed | dismissed
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    snoozed_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    quote: Mapped["Quote"] = relationship("Quote", backref="follow_ups")
    organization: Mapped["Organization"] = relationship("Organization")

class BookingDocument(Base, TimestampMixin):
    __tablename__ = "booking_documents"

    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(30))  # ticket | voucher | invoice | receipt | other
    filename: Mapped[str] = mapped_column(String(255))
    storage_url: Mapped[str] = mapped_column(String)  # local path or URL
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    booking: Mapped["Booking"] = relationship("Booking", backref="documents")
    organization: Mapped["Organization"] = relationship("Organization")
