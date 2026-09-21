from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum


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


class NormalizedOffer(BaseModel):
    id: str
    supplier_code: str
    supplier_reference: str
    type: InventoryType
    
    # Financials
    currency: str = "INR"
    total_amount: float
    base_amount: float
    tax_amount: float
    
    # Payload
    title: str
    description: Optional[str] = None
    
    # Provider-specific raw data (for debugging or revalidation)
    raw_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # State flags
    is_revalidated: bool = False
    valid_until: Optional[datetime] = None


class SearchResponse(BaseModel):
    search_request_id: str
    results_count: int
    offers: List[NormalizedOffer]


class RevalidateRequest(BaseModel):
    offer: NormalizedOffer
