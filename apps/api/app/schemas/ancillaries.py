"""FC Phase 6 — fare families, ancillaries, seat map schemas."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.inventory import NormalizedOffer


class BaggageSummary(BaseModel):
    cabin_kg: Optional[float] = None
    checked_kg: Optional[float] = None
    pieces: Optional[int] = None
    notes: Optional[str] = None


class AncillaryOption(BaseModel):
    code: str
    type: Literal["baggage", "meal", "seat", "ssr", "other"] = "other"
    label: str
    description: Optional[str] = None
    amount: float  # major units in offer currency
    currency: str = "INR"
    per_passenger: bool = True
    meta: Dict[str, Any] = Field(default_factory=dict)


class AncillaryCatalog(BaseModel):
    supported: bool = False
    currency: str = "INR"
    items: List[AncillaryOption] = Field(default_factory=list)
    message: Optional[str] = None  # when unsupported


class SeatCell(BaseModel):
    seat: str  # e.g. 12A
    available: bool = True
    amount: float = 0.0
    currency: str = "INR"
    characteristics: List[str] = Field(default_factory=list)  # window, aisle, exit, etc.


class SeatRow(BaseModel):
    row: int
    seats: List[SeatCell]


class SeatMapResponse(BaseModel):
    supported: bool = False
    currency: str = "INR"
    cabin: Optional[str] = None
    rows: List[SeatRow] = Field(default_factory=list)
    message: Optional[str] = None


class OfferExtrasRequest(BaseModel):
    """Body for ancillary / seat-map fetch."""

    offer: NormalizedOffer


class QuoteExtraLine(BaseModel):
    """Frozen line on quote item (paise)."""

    type: Literal["baggage", "meal", "seat", "ssr", "other"] = "other"
    code: str
    label: str
    amount_paise: int
    passenger_index: Optional[int] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class QuoteItemExtrasUpdate(BaseModel):
    """Replace extras on a quote item (draft only)."""

    extras: List[QuoteExtraLine] = Field(default_factory=list)
