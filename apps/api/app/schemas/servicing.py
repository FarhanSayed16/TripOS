"""FC Phase 7 — reissue / booking change schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReissueQuoteRequest(BaseModel):
    change_type: str = Field(..., description="date | route | name | other")
    request_payload: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class ReissueConfirmRequest(BaseModel):
    """Confirm a quoted change. Set payment_collected when diff > 0 (mock collect)."""

    payment_collected: bool = False
    force_manual_sop: bool = False


class BookingChangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    organization_id: uuid.UUID
    change_type: str
    status: str
    request_payload: Dict[str, Any]
    supplier_diff_paise: Optional[int] = None
    new_total_paise: Optional[int] = None
    currency: str = "INR"
    notes: Optional[str] = None
    manual_sop: bool = False
    created_at: datetime
    updated_at: datetime
    # Human guidance when automated reissue is unavailable
    sop_hint: Optional[str] = None


class ScheduleChangeIngest(BaseModel):
    supplier_pnr: Optional[str] = None
    supplier_code: Optional[str] = None
    booking_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    changes: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None
