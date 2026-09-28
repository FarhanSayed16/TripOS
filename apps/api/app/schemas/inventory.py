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


class RevalidateRequest(BaseModel):
    offer: NormalizedOffer
