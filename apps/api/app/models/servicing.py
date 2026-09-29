"""FC Phase 7 — booking change (reissue) + schedule change events."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import String, ForeignKey, Integer, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class BookingChangeRequest(Base, TimestampMixin):
    """
    Post-booking change / reissue request.
    status: quoted | awaiting_payment | confirmed | failed | manual_sop
    change_type: date | route | name | other
    """

    __tablename__ = "booking_change_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    requested_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    change_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="quoted", nullable=False)
    request_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    supplier_diff_paise: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    new_total_paise: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manual_sop: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ScheduleChangeEvent(Base, TimestampMixin):
    """Inbound schedule-change notification from supplier (or ops ingest)."""

    __tablename__ = "schedule_change_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True, index=True
    )
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("bookings.id"), nullable=True, index=True
    )
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    supplier_pnr: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
