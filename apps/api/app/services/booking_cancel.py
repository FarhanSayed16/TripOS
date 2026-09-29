"""Shared cancel helpers — soft-fail supplier cancel so TripOS can still close the booking."""
from __future__ import annotations

from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import Quote
from app.models.enums import BookingStatus, QuoteStatus
from app.services.audit import write_audit
from app.services.inventory import cancel_booking
from app.services.refunds import maybe_request_refund_on_cancel

logger = structlog.get_logger()


async def cancel_quote_with_soft_supplier(
    db: AsyncSession,
    quote: Quote,
    *,
    actor_user_id,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Cancel quote in TripOS. If supplier cancel fails, still mark cancelled locally,
    open refund if needed, and return supplier_cancel_ok=False for audit/ops.
    """
    meta = dict(metadata or {})
    supplier_cancel_ok: Optional[bool] = None
    supplier_cancel_error: Optional[str] = None

    if quote.status == QuoteStatus.cancelled:
        return {
            "already_cancelled": True,
            "supplier_cancel_ok": None,
            "supplier_cancel_error": None,
        }

    if quote.booking and quote.booking.status == BookingStatus.confirmed:
        supplier_code = "mock_supplier"
        pnr = quote.booking.supplier_pnr
        if quote.items and quote.items[0].offer_snapshot:
            raw_data = quote.items[0].offer_snapshot.offer_data or {}
            supplier_code = raw_data.get("supplier_code") or supplier_code

        if not pnr:
            supplier_cancel_ok = False
            supplier_cancel_error = "missing_pnr"
            logger.warning(
                "cancel_missing_pnr",
                quote_id=str(quote.id),
                booking_id=str(quote.booking.id),
            )
        else:
            try:
                supplier_cancel_ok = bool(await cancel_booking(supplier_code, pnr))
                if not supplier_cancel_ok:
                    supplier_cancel_error = "supplier_returned_false"
            except Exception as e:
                supplier_cancel_ok = False
                supplier_cancel_error = str(e)[:300]
                logger.warning(
                    "cancel_supplier_exception",
                    quote_id=str(quote.id),
                    error=str(e),
                )

        quote.booking.status = BookingStatus.cancelled
        meta["supplier_cancel_ok"] = supplier_cancel_ok
        if supplier_cancel_error:
            meta["supplier_cancel_error"] = supplier_cancel_error
            meta["needs_manual_supplier_cancel"] = True

    quote.status = QuoteStatus.cancelled

    await write_audit(
        db,
        organization_id=quote.organization_id,
        actor_user_id=actor_user_id,
        action="cancel.requested",
        entity_type="quote",
        entity_id=str(quote.id),
        metadata=meta,
    )

    await maybe_request_refund_on_cancel(
        db, quote, requested_by_user_id=actor_user_id
    )

    return {
        "already_cancelled": False,
        "supplier_cancel_ok": supplier_cancel_ok,
        "supplier_cancel_error": supplier_cancel_error,
    }
