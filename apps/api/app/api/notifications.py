"""Notification API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from app.api.deps import require_active_org, get_db
from app.models.tenancy import User
from app.services.notifications import (
    get_notifications,
    get_unread_count,
    mark_read,
    mark_all_read,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    type: str
    title: str
    body: Optional[str] = None
    icon: str
    severity: str
    link: Optional[str] = None
    is_read: bool
    metadata: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj):
        return cls(
            id=obj.id,
            organization_id=obj.organization_id,
            user_id=obj.user_id,
            type=obj.type,
            title=obj.title,
            body=obj.body,
            icon=obj.icon,
            severity=obj.severity,
            link=obj.link,
            is_read=obj.is_read,
            metadata=obj.metadata_,
            created_at=obj.created_at,
        )


class UnreadCountOut(BaseModel):
    count: int


@router.get("", response_model=List[NotificationOut])
async def list_notifications(
    limit: int = 30,
    offset: int = 0,
    unread_only: bool = False,
    user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """List notifications for the current org, newest first."""
    if not user.active_organization_id:
        raise HTTPException(status_code=403, detail="No active organization")
    notifications = await get_notifications(
        db,
        user.active_organization_id,
        limit=min(limit, 100),
        offset=offset,
        unread_only=unread_only,
    )
    return [NotificationOut.from_orm_model(n) for n in notifications]


@router.get("/unread-count", response_model=UnreadCountOut)
async def unread_count(
    user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Return the count of unread notifications."""
    if not user.active_organization_id:
        raise HTTPException(status_code=403, detail="No active organization")
    count = await get_unread_count(db, user.active_organization_id)
    return UnreadCountOut(count=count)


@router.patch("/{notification_id}/read")
async def read_one(
    notification_id: uuid.UUID,
    user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Mark a single notification as read."""
    if not user.active_organization_id:
        raise HTTPException(status_code=403, detail="No active organization")
    updated = await mark_read(db, notification_id, user.active_organization_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.commit()
    return {"ok": True}


@router.post("/read-all")
async def read_all(
    user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """Mark all unread notifications as read."""
    if not user.active_organization_id:
        raise HTTPException(status_code=403, detail="No active organization")
    count = await mark_all_read(db, user.active_organization_id)
    await db.commit()
    return {"ok": True, "count": count}
