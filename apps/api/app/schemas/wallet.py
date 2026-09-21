from pydantic import BaseModel, ConfigDict
from typing import Optional, List
import uuid
from datetime import datetime

class WalletSummary(BaseModel):
    pending_paise: int
    available_paise: int
    total_earned_paise: int
    total_settled_paise: int

class WalletLedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    booking_id: Optional[uuid.UUID]
    type: str
    amount_paise: int
    status: str
    description: Optional[str]
    settled_at: Optional[datetime]
    created_at: datetime

class CommissionRuleCreate(BaseModel):
    organization_id: Optional[uuid.UUID] = None
    product_type: str = "flight"
    rule_type: str = "percentage"
    value: int
    is_active: bool = True

class CommissionRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: Optional[uuid.UUID]
    product_type: str
    rule_type: str
    value: int
    is_active: bool
    created_at: datetime
