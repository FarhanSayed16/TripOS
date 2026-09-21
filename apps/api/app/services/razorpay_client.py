"""
Razorpay Payment Links (Sprint I).

Activated when PAYMENTS_MODE=razorpay and KEY_ID + KEY_SECRET are set.
Falls back is handled by caller (payments service).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple
import structlog

from app.core.config import settings

logger = structlog.get_logger()


def razorpay_live_configured() -> bool:
    return bool(
        settings.PAYMENTS_MODE == "razorpay"
        and settings.RAZORPAY_KEY_ID
        and settings.RAZORPAY_KEY_SECRET
    )


def _client():
    from app.core.exceptions import AppError

    try:
        import razorpay
    except ImportError as e:
        raise AppError(
            "razorpay package not installed. pip install razorpay",
            status_code=503,
            error_code="RAZORPAY_SDK_MISSING",
        ) from e
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


async def create_razorpay_payment_link(
    *,
    amount_paise: int,
    quote_id: str,
    public_token: str,
    valid_until: datetime,
    customer_name: str | None = None,
    customer_email: str | None = None,
    customer_phone: str | None = None,
) -> Tuple[str, str]:
    """
    Returns (gateway_order_id, payment_link_url).
    gateway_order_id prefers Razorpay order_id when present, else payment_link id.
    """
    from app.core.exceptions import AppError

    if amount_paise <= 0:
        raise AppError("Amount must be positive", status_code=400, error_code="INVALID_AMOUNT")

    expire_by = int(valid_until.timestamp())
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if expire_by <= now_ts:
        raise AppError("Quote already expired", status_code=400, error_code="QUOTE_EXPIRED")

    callback = f"{settings.FRONTEND_URL.rstrip('/')}/q/{public_token}/status"
    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "expire_by": expire_by,
        "reference_id": quote_id.replace("-", "")[:40],
        "description": f"TripOS travel quote {quote_id[:8]}",
        "callback_url": callback,
        "callback_method": "get",
        "notes": {
            "tripos_quote_id": quote_id,
        },
    }
    customer: dict = {}
    if customer_name:
        customer["name"] = customer_name[:50]
    if customer_email:
        customer["email"] = customer_email
    if customer_phone:
        customer["contact"] = customer_phone.lstrip("+")
    if customer:
        payload["customer"] = customer

    try:
        client = _client()
        # SDK is sync; fine for V1 pilot volume
        link = client.payment_link.create(payload)
    except AppError:
        raise
    except Exception as e:
        logger.error("razorpay_payment_link_failed", error=str(e))
        raise AppError(
            f"Razorpay payment link failed: {e}",
            status_code=502,
            error_code="RAZORPAY_ERROR",
        ) from e

    plink_id = link.get("id") or ""
    order_id = link.get("order_id") or plink_id
    short_url = link.get("short_url") or ""
    if not order_id or not short_url:
        raise AppError(
            "Razorpay returned incomplete payment link",
            status_code=502,
            error_code="RAZORPAY_ERROR",
        )

    logger.info(
        "razorpay_payment_link_created",
        quote_id=quote_id,
        plink_id=plink_id,
        order_id=order_id,
    )
    return str(order_id), str(short_url)
