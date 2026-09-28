import uuid
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class VerifyRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    first_name: str = ""
    last_name: str = ""
    active_organization_id: uuid.UUID | None = None
    org_role: str | None = None
    org_status: str | None = None
    is_platform_admin: bool = False
    preferred_currency: str | None = None


class UserPreferencesUpdate(BaseModel):
    preferred_currency: str | None = Field(None, min_length=3, max_length=3)
