from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
from datetime import datetime

class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    quote_id: uuid.UUID
    organization_id: uuid.UUID
    type: str
    status: str
    message: Optional[str]
    snoozed_until: Optional[datetime]
    created_at: datetime
    
    # Extra fields for UI convenience
    quote_public_token: Optional[str] = None
    customer_name: Optional[str] = None
    amount_paise: Optional[int] = None
    hours_overdue: Optional[int] = None

class SnoozeRequest(BaseModel):
    hours: int
