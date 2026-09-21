from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional
import uuid
from app.models.enums import PaymentStatus


class RazorpayWebhookPayload(BaseModel):
    """
    Schema for Razorpay webhooks (simplified for mock + captured events).
    """

    event: str
    payload: Dict[str, Any]


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quote_id: uuid.UUID
    status: PaymentStatus
    amount: int
    gateway_order_id: Optional[str] = None
    payment_link_url: Optional[str] = None
