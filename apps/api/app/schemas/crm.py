import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class CustomerCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone: str


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    first_name: str
    last_name: str
    email: str | None
    phone_e164: str
    created_at: datetime


class CustomerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None


class CustomerTimelineItem(BaseModel):
    id: str
    type: str  # 'quote', 'booking', 'note'
    title: str
    description: str | None = None
    created_at: datetime
