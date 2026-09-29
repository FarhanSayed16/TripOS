from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum

from app.schemas.fx import MoneyDisplay


class InventoryType(str, Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"


class AdapterCapabilities(BaseModel):
    can_revalidate: bool
    can_book: bool
    can_cancel: bool
    # FC Phase 6 — optional rich-offer capabilities (default off)
    can_ancillaries: bool = False
    can_seat_map: bool = False


class PassengerQuery(BaseModel):
    adults: int = 1
    children: int = 0
    infants: int = 0


class SearchQuery(BaseModel):
    type: InventoryType
    origin: str  # IATA or City Code
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    passengers: PassengerQuery
    # FC Phase 3 — server-side rank/filter (optional; FE can also filter client-side)
    sort: Optional[str] = "recommended"  # price | duration | stops | recommended
    max_stops: Optional[int] = None
    airlines: Optional[List[str]] = None
    max_price: Optional[float] = None
    depart_time_from: Optional[str] = None  # HH:MM
    depart_time_to: Optional[str] = None
    dedupe: bool = True
    # FC Phase 7 — promo / corp deal code (agent) + resolved org codes
    deal_code: Optional[str] = None
    deal_codes: Optional[List[str]] = None


class BaggageInfo(BaseModel):
    cabin_kg: Optional[float] = None
    checked_kg: Optional[float] = None
    pieces: Optional[int] = None
    notes: Optional[str] = None


class FlightSegment(BaseModel):
    """FC Phase 7 — structured segment with marketing vs operating carrier."""

    origin: str
    destination: str
    departure_at: Optional[str] = None  # ISO local or HH:MM
    arrival_at: Optional[str] = None
    marketing_carrier: Optional[str] = None
    operating_carrier: Optional[str] = None
    flight_number: Optional[str] = None
    duration_minutes: Optional[int] = None
    cabin: Optional[str] = None


class NormalizedOffer(BaseModel):
    id: str
    supplier_code: str
    supplier_reference: str
    type: InventoryType

    # Financials (supplier/charge — never mutated by FX)
    currency: str = "INR"
    total_amount: float
    base_amount: float
    tax_amount: float
    # FC Phase 4 — display conversion envelope
    money: Optional[MoneyDisplay] = None

    # Payload
    title: str
    description: Optional[str] = None

    # Provider-specific raw data (for debugging or revalidation)
    raw_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # State flags
    is_revalidated: bool = False
    valid_until: Optional[datetime] = None
    # FC Phase 1 — live | simulated | mock (honesty for agents)
    inventory_mode: Optional[str] = None
    # FC Phase 3 — aggregation / ranking fields
    source_type: Optional[str] = None  # mock | agg | gds | lcc
    duration_minutes: Optional[int] = None
    stops: Optional[int] = None
    airline_code: Optional[str] = None
    airline_name: Optional[str] = None
    depart_time: Optional[str] = None  # HH:MM local
    # FC Phase 6 — branded fares / cabin / baggage
    fare_family: Optional[str] = None  # Basic | Flex | Premium
    fare_family_code: Optional[str] = None
    cabin: Optional[str] = None  # economy | premium_economy | business
    baggage: Optional[BaggageInfo] = None
    family_group_id: Optional[str] = None  # links fare variants of same flight
    supports_ancillaries: Optional[bool] = None
    supports_seat_map: Optional[bool] = None
    # FC Phase 7 — structured segments + applied deal code
    segments: Optional[List[FlightSegment]] = None
    deal_code: Optional[str] = None


class SearchResponse(BaseModel):
    search_request_id: str
    results_count: int
    offers: List[NormalizedOffer]
    # Phase 2 shopping cache metadata (indicative browse)
    cache_hit: bool = False
    cache_age_seconds: Optional[int] = None
    # FC Phase 3
    supplier_counts: Optional[Dict[str, int]] = None
    airline_facets: Optional[List[Dict[str, Any]]] = None
    aggregation: Optional[Dict[str, Any]] = None
    # FC Phase 4
    charge_currency: str = "INR"
    display_currency: str = "INR"
    fx_rate: Optional[float] = None
    fx_as_of: Optional[str] = None
    fx_source: Optional[str] = None
    # FC Phase 6
    ancillaries_enabled: bool = False
    seat_map_enabled: bool = False


class RevalidateRequest(BaseModel):
    offer: NormalizedOffer
