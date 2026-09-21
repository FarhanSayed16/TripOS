from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
import uuid
from datetime import datetime

from app.models.enums import PackageStatus

class PackageItemCreate(BaseModel):
    type: str  # flight | hotel | activity | transfer
    title: str
    description: Optional[str] = None
    estimated_cost_paise: int
    supplier_code: Optional[str] = None
    search_params: Optional[dict] = None
    sort_order: int = 0

class PackageCreate(BaseModel):
    title: str
    description: Optional[str] = None
    destination: str
    duration_days: int
    base_price_paise: int
    cover_image_url: Optional[str] = None
    items: List[PackageItemCreate] = Field(default_factory=list)

class PackageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    destination: Optional[str] = None
    duration_days: Optional[int] = None
    base_price_paise: Optional[int] = None
    cover_image_url: Optional[str] = None
    status: Optional[PackageStatus] = None

class PackageItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: str
    title: str
    description: Optional[str]
    estimated_cost_paise: int
    supplier_code: Optional[str]
    sort_order: int

class PackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    description: Optional[str]
    destination: str
    duration_days: int
    base_price_paise: int
    cover_image_url: Optional[str]
    status: str
    created_at: datetime
    items: List[PackageItemResponse] = Field(default_factory=list)
