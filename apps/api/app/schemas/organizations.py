import uuid
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.enums import OrgStatus, UserRole

class UserNestedResponse(BaseModel):
    id: uuid.UUID
    email: str

    class Config:
        from_attributes = True

class OrganizationBase(BaseModel):
    brand_name: str
    slug: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    status: OrgStatus
    preferred_currency: str = "INR"

class OrganizationResponse(OrganizationBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

class OrganizationUpdate(BaseModel):
    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    preferred_currency: Optional[str] = Field(None, min_length=3, max_length=3)

class MemberResponse(BaseModel):
    role: UserRole
    user: UserNestedResponse

    class Config:
        from_attributes = True
