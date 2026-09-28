import hmac
import hashlib
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.api.deps import get_db
from app.schemas.payments import RazorpayWebhookPayload
from app.services.payments import process_razorpay_webhook
from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_razorpay_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not signature:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


@router.post("/razorpay")
async def api_razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Razorpay webhook endpoint.
    - If RAZORPAY_WEBHOOK_SECRET (or KEY_SECRET) is set: require valid X-Razorpay-Signature.
    - If PAYMENTS_MODE=mock and no secret: allow unsigned payloads for local simulation.
    - Production always requires a configured webhook secret.
    """
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    secret = settings.RAZORPAY_WEBHOOK_SECRET or settings.RAZORPAY_KEY_SECRET

    # AUDIT-008: production always requires a secret; unsigned only for local mock
    if settings.is_production:
        if not secret:
            raise HTTPException(status_code=503, detail="Webhook secret not configured")
        if not _verify_razorpay_signature(body, signature, secret):
            logger.warning("webhook_signature_invalid")
            if settings.SENTRY_DSN:
                import sentry_sdk

                sentry_sdk.capture_message("webhook_signature_invalid", level="warning")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
    elif secret:
        if not _verify_razorpay_signature(body, signature, secret):
            logger.warning("webhook_signature_invalid")
            if settings.SENTRY_DSN:
                import sentry_sdk

                sentry_sdk.capture_message("webhook_signature_invalid", level="warning")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
    elif settings.PAYMENTS_MODE == "mock":
        logger.warning("webhook_signature_skipped_local_mock_only")
    else:
        raise HTTPException(status_code=503, detail="Webhook secret required")

    try:
        payload = RazorpayWebhookPayload.model_validate_json(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook JSON")

    return await process_razorpay_webhook(payload, db)


@router.post("/schedule-change")
async def api_schedule_change_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    FC Phase 7 — ingest supplier schedule-change notifications.
    Optional shared secret via header X-TripOS-Webhook-Secret when configured.
    """
    from app.schemas.servicing import ScheduleChangeIngest
    from app.services.schedule_change import ingest_schedule_change

    secret = settings.FC_SCHEDULE_CHANGE_WEBHOOK_SECRET
    if secret:
        provided = request.headers.get("x-tripos-webhook-secret")
        if not provided or not hmac.compare_digest(provided, secret):
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
    elif settings.is_production:
        raise HTTPException(status_code=503, detail="Schedule-change webhook secret required")

    body = await request.json()
    payload = ScheduleChangeIngest.model_validate(body)
    event = await ingest_schedule_change(payload, db)
    return {
        "status": "ok",
        "event_id": str(event.id),
        "booking_id": str(event.booking_id) if event.booking_id else None,
        "notified": event.notified,
    }
