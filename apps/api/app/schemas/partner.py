"""FC Phase 8 — partner API schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PartnerAppCreate(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(..., min_length=2, max_length=120)
    env: str = "test"
    webhook_url: Optional[str] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    scopes: Optional[List[str]] = None
    ip_allowlist: Optional[List[str]] = None


class PartnerAppUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    webhook_url: Optional[str] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    scopes: Optional[List[str]] = None
    ip_allowlist: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PartnerAppResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    key_prefix: str
    env: str
    webhook_url: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    rate_limit_per_minute: int
    ip_allowlist: Optional[List[str]] = None
    is_active: bool
    last_used_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None
    created_at: datetime
    # Only set on create/rotate — never stored again
    api_key: Optional[str] = None
    webhook_secret: Optional[str] = None


class PartnerCustomerCreate(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None


class PartnerPayLinkResponse(BaseModel):
    quote_id: uuid.UUID
    payment_id: uuid.UUID
    status: str
    amount_paise: int
    currency: str = "INR"
    payment_link_url: Optional[str] = None
    public_quote_url: Optional[str] = None


class PartnerBookingStatus(BaseModel):
    quote_id: uuid.UUID
    booking_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    supplier_pnr: Optional[str] = None
    failure_reason: Optional[str] = None
    payment_status: Optional[str] = None
