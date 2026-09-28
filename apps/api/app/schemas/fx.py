"""FC Phase 4 money / FX schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MoneyDisplay(BaseModel):
    """
    Display envelope. `currency`/`amount` are supplier/charge amounts.
    `display_*` are derived via FX and must never replace supplier fare.
    """

    currency: str = "INR"
    amount: float
    display_currency: str = "INR"
    display_amount: float
    fx_rate: float = 1.0
    fx_as_of: Optional[str] = None
    fx_source: Optional[str] = None


class FxRateCreate(BaseModel):
    base_currency: str = Field(..., min_length=3, max_length=3)
    quote_currency: str = Field(..., min_length=3, max_length=3)
    rate: float = Field(..., gt=0)
    source: str = "manual"
    as_of: Optional[datetime] = None
    is_active: bool = True


class FxRateUpdate(BaseModel):
    rate: Optional[float] = Field(None, gt=0)
    source: Optional[str] = None
    as_of: Optional[datetime] = None
    is_active: Optional[bool] = None


class FxRateResponse(BaseModel):
    id: str
    base_currency: str
    quote_currency: str
    rate: float
    as_of: datetime
    source: str
    is_active: bool
