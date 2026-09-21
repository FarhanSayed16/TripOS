from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
from datetime import datetime

class BookingDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    booking_id: uuid.UUID
    organization_id: uuid.UUID
    type: str
    filename: str
    storage_url: str
    mime_type: str
    uploaded_by_user_id: uuid.UUID
    created_at: datetime
