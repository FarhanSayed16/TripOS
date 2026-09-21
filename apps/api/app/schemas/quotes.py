import uuid
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import QuoteStatus, BookingStatus, BookingFailureReason
from app.schemas.inventory import NormalizedOffer


# --- Quote Passengers ---

class QuotePassengerBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    passport_number: Optional[str] = None


class QuotePassengerUpdate(QuotePassengerBase):
    pass


class QuotePassengerResponse(QuotePassengerBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# --- Quote Items ---

class QuoteItemCreate(BaseModel):
    search_request_id: str
    offer: NormalizedOffer
    agent_markup: int = 0  # in paise


class QuoteItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    offer_snapshot_id: uuid.UUID
    supplier_cost: int
    agent_markup: int
    platform_fee: int
    customer_total: int


class PublicQuoteItemResponse(BaseModel):
    """Sanitized view for end customers"""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    customer_total: int
    # Inject sanitized offer data (title, description, type, currency) from the snapshot
    sanitized_offer_data: dict = Field(default_factory=dict)


# --- Quotes ---

class QuoteCreate(BaseModel):
    customer_id: uuid.UUID  # ISSUE-14: Pydantic validates UUID format automatically
    items: List[QuoteItemCreate] = Field(min_length=1)


class QuoteBookingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: BookingStatus
    supplier_pnr: Optional[str] = None
    failure_reason: Optional[BookingFailureReason] = None


class QuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    customer_id: uuid.UUID
    public_token: str
    status: QuoteStatus
    valid_until: datetime
    created_at: datetime
    items: List[QuoteItemResponse]
    passengers: List[QuotePassengerResponse] = Field(default_factory=list)
    booking: Optional[QuoteBookingSummary] = None


class PublicQuoteResponse(BaseModel):
    """Sanitized quote payload for public links"""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: QuoteStatus
    valid_until: datetime
    items: List[PublicQuoteItemResponse]
    payment_link_url: Optional[str] = None
    agency_name: str = "TripOS"
    agency_logo_url: Optional[str] = None
    payment_status: Optional[str] = None
    booking_status: Optional[str] = None


# --- Messaging ---

class WhatsAppPreviewResponse(BaseModel):
    phone_e164: str
    message_template: str
    wa_me_url: str | None = None


class QuoteSendRequest(BaseModel):
    channel: str = "whatsapp"
    content: str
