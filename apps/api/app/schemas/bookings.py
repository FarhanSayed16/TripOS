from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import Optional
from app.models.enums import BookingStatus, BookingFailureReason


FAILURE_LABELS: dict[str, str] = {
    BookingFailureReason.fare_changed.value: "Fare changed — customer paid a different price than the supplier now quotes",
    BookingFailureReason.sold_out.value: "Sold out — seats/rooms no longer available",
    BookingFailureReason.supplier_timeout.value: "Supplier timed out — retryable; support may need to rebook",
    BookingFailureReason.supplier_error.value: "Supplier error — needs manual support",
    BookingFailureReason.missing_pax.value: "Missing passenger details — cannot book",
    BookingFailureReason.unknown.value: "Unknown booking failure — needs manual review",
}


def failure_label(reason: Optional[str]) -> Optional[str]:
    if not reason:
        return None
    key = reason if isinstance(reason, str) else getattr(reason, "value", str(reason))
    return FAILURE_LABELS.get(key, key.replace("_", " ").title())


class BookingQuoteSummary(BaseModel):
    id: uuid.UUID
    customer_name: str
    total_price: Optional[int] = None  # paise
    currency: str = "INR"
    status: Optional[str] = None


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quote_id: uuid.UUID
    status: BookingStatus
    supplier_pnr: Optional[str] = None
    failure_reason: Optional[str] = None
    failure_label: Optional[str] = None
    needs_manual_support: bool = False
    created_at: datetime
    updated_at: datetime
    quote: Optional[BookingQuoteSummary] = None
