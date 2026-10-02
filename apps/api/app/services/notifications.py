"""Notification service — create, query, and manage in-app notifications."""
import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc
import structlog

from app.models.notification import Notification

logger = structlog.get_logger()


async def create_notification(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    type: str,
    title: str,
    body: Optional[str] = None,
    icon: str = "bell",
    severity: str = "info",
    link: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    metadata: Optional[dict] = None,
) -> Notification:
    """Insert a new notification row."""
    notif = Notification(
        organization_id=organization_id,
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        icon=icon,
        severity=severity,
        link=link,
        metadata_=metadata,
    )
    db.add(notif)
    await db.flush()
    logger.info(
        "notification_created",
        notification_id=str(notif.id),
        type=type,
        severity=severity,
        org_id=str(organization_id),
    )
    return notif


async def get_notifications(
    db: AsyncSession,
    organization_id: uuid.UUID,
    *,
    limit: int = 30,
    offset: int = 0,
    unread_only: bool = False,
) -> List[Notification]:
    """Fetch notifications for an org, newest first."""
    stmt = (
        select(Notification)
        .where(Notification.organization_id == organization_id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
        .offset(offset)
    )
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_unread_count(
    db: AsyncSession,
    organization_id: uuid.UUID,
) -> int:
    """Return count of unread notifications for an org."""
    stmt = (
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.organization_id == organization_id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def mark_read(
    db: AsyncSession,
    notification_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> bool:
    """Mark a single notification as read. Returns True if updated."""
    stmt = (
        update(Notification)
        .where(
            Notification.id == notification_id,
            Notification.organization_id == organization_id,
        )
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount > 0


async def mark_all_read(
    db: AsyncSession,
    organization_id: uuid.UUID,
) -> int:
    """Mark all unread notifications as read. Returns count updated."""
    stmt = (
        update(Notification)
        .where(
            Notification.organization_id == organization_id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount
