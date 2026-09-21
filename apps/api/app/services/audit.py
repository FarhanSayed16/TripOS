"""Helpers for durable audit_events (FIX-P21-01)."""
from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import AuditEvent


def make_audit_event(
    *,
    organization_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_user_id: Optional[uuid.UUID] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AuditEvent:
    """Construct AuditEvent with the real schema columns."""
    return AuditEvent(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata_payload=metadata if metadata is not None else {},
    )


async def write_audit(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_user_id: Optional[uuid.UUID] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AuditEvent:
    event = make_audit_event(
        organization_id=organization_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        metadata=metadata,
    )
    db.add(event)
    return event
