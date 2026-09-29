"""FC Phase 8 — signed outbound webhooks to partner apps."""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.partner import PartnerApp, PartnerWebhookDelivery

logger = structlog.get_logger()


def sign_payload(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


async def dispatch_partner_event(
    db: AsyncSession,
    organization_id: uuid.UUID,
    event_type: str,
    data: dict[str, Any],
) -> int:
    """
    Fan-out event to all active partner apps on this org with a webhook_url.
    Returns number of delivery attempts started.
    """
    if not settings.FC_PARTNER_API_ENABLED:
        return 0

    apps = (
        await db.execute(
            select(PartnerApp).where(
                PartnerApp.organization_id == organization_id,
                PartnerApp.is_active.is_(True),
                PartnerApp.deleted_at.is_(None),
                PartnerApp.webhook_url.isnot(None),
            )
        )
    ).scalars().all()

    sent = 0
    for app in apps:
        if not app.webhook_url:
            continue
        payload = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        delivery = PartnerWebhookDelivery(
            id=uuid.uuid4(),
            partner_app_id=app.id,
            event_type=event_type,
            payload=payload,
            status="pending",
            attempts=0,
        )
        db.add(delivery)
        await db.flush()
        await _deliver(db, app, delivery, payload)
        sent += 1
    if sent:
        await db.commit()
    return sent


async def _deliver(
    db: AsyncSession,
    app: PartnerApp,
    delivery: PartnerWebhookDelivery,
    payload: dict,
) -> None:
    body = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
    secret = app.webhook_secret or ""
    headers = {
        "Content-Type": "application/json",
        "X-TripOS-Event": delivery.event_type,
        "X-TripOS-Delivery": str(delivery.id),
        "User-Agent": "TripOS-PartnerWebhook/1.0",
    }
    if secret:
        headers["X-TripOS-Signature"] = sign_payload(secret, body)

    delivery.attempts = int(delivery.attempts or 0) + 1
    try:
        timeout = settings.FC_PARTNER_WEBHOOK_TIMEOUT_SECONDS
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(app.webhook_url, content=body, headers=headers)
        delivery.http_status = resp.status_code
        if 200 <= resp.status_code < 300:
            delivery.status = "delivered"
            delivery.last_error = None
        else:
            delivery.status = "failed"
            delivery.last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
    except Exception as e:
        delivery.status = "failed"
        delivery.last_error = str(e)[:500]
        logger.warning(
            "partner_webhook_failed",
            partner_app_id=str(app.id),
            event=delivery.event_type,
            error=str(e),
        )
    await db.flush()
