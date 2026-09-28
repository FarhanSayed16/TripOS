"""Fare rules DTOs (FC Phase 2)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.inventory import NormalizedOffer


class FareRules(BaseModel):
    supplier_code: str
    supplier_reference: str
    is_refundable: Optional[bool] = None
    change_allowed: Optional[bool] = None
    cancel_penalty_summary: Optional[str] = None
    change_penalty_summary: Optional[str] = None
    baggage_summary: Optional[str] = None
    raw_text: Optional[str] = None
    source: str = "derived"  # derived | supplier | snapshot


class FareRulesRequest(BaseModel):
    offer: NormalizedOffer
