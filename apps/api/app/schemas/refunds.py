"""Refund API schemas (FC Phase 2)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import RefundStatus


class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    payment_id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    amount: int
    status: RefundStatus
    reason: Optional[str] = None
    notes: Optional[str] = None
    gateway_refund_id: Optional[str] = None
    requested_by_user_id: Optional[uuid.UUID] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    quote_id: Optional[uuid.UUID] = None


class RefundStatusUpdate(BaseModel):
    status: RefundStatus
    notes: Optional[str] = None
    gateway_refund_id: Optional[str] = None
