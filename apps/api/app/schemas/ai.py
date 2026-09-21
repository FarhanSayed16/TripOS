from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date

class ParseIntentRequest(BaseModel):
    message: str

class ParsedIntent(BaseModel):
    type: str  # "flight", "hotel", "package"
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None # ISO format YYYY-MM-DD
    return_date: Optional[str] = None
    passengers: int = 1
    budget_max: Optional[int] = None # in rupees
    raw_message: str

class FormatDraftRequest(BaseModel):
    intent: ParsedIntent
    offers: List[dict] # JSON versions of NormalizedOffer

class QuoteDraft(BaseModel):
    selected_offer_ids: List[str]
    summary: str
    suggested_markup_paise: int

class SearchAndDraftRequest(BaseModel):
    message: str

class SearchAndDraftResponse(BaseModel):
    intent: ParsedIntent
    search_results: List[dict]
    draft: QuoteDraft
