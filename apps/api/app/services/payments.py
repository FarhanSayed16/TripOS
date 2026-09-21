import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import structlog

from app.models.commercial import Quote, Payment, JobOutbox, QuoteItem
from app.models.enums import QuoteStatus, PaymentStatus, JobStatus, BookingStatus
from app.models.tenancy import User
from app.schemas.payments import RazorpayWebhookPayload
from app.schemas.inventory import NormalizedOffer
from app.services.inventory import revalidate_normalized_offer
from app.core.exceptions import AppError
from app.core.config import settings
from app.utils.idempotency import claim_idempotency_key
from app.services.razorpay_client import create_razorpay_payment_link, razorpay_live_configured
from app.services.audit import write_audit

logger = structlog.get_logger()


async def _mock_create_razorpay_link(amount: int, quote_id: str, valid_until: datetime):
    """Mock Razorpay payment link (PAYMENTS_MODE=mock)."""
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    payment_link_id = f"plink_{uuid.uuid4().hex[:12]}"
    payment_link_url = f"https://rzp.io/i/{payment_link_id}?quote={quote_id}"
    _ = amount, valid_until
    return order_id, payment_link_url


async def _create_payment_link(quote: Quote, total_amount: int) -> tuple[str, str]:
    if razorpay_live_configured():
        customer = quote.customer
        return await create_razorpay_payment_link(
            amount_paise=total_amount,
            quote_id=str(quote.id),
            public_token=quote.public_token,
            valid_until=quote.valid_until,
            customer_name=(
                f"{customer.first_name} {customer.last_name}".strip() if customer else None
            ),
            customer_email=customer.email if customer else None,
            customer_phone=customer.phone_e164 if customer else None,
        )
    if settings.PAYMENTS_MODE == "razorpay":
        logger.warning("payments_mode_razorpay_missing_keys_falling_back_to_mock")
    return await _mock_create_razorpay_link(total_amount, str(quote.id), quote.valid_until)


async def _revalidate_quote_items(quote: Quote) -> None:
    from app.core.inventory_errors import InventoryRevalidateError

    for item in quote.items:
        snap = item.offer_snapshot
        if not snap or not snap.offer_data:
            raise AppError(
                "Quote item missing offer snapshot",
                status_code=400,
                error_code="MISSING_SNAPSHOT",
            )
        try:
            offer = NormalizedOffer.model_validate(snap.offer_data)
        except Exception as e:
            raise AppError(
                f"Invalid offer snapshot: {e}",
                status_code=400,
                error_code="INVALID_SNAPSHOT",
            )
        try:
            await revalidate_normalized_offer(offer)
        except InventoryRevalidateError as e:
            raise AppError(
                e.message,
                status_code=409,
                error_code=e.error_code.upper(),
            ) from e


async def create_payment_for_quote(quote_id: str, current_user: User, db: AsyncSession):
    from app.services.quotes import assert_pax_gate

    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.offer_snapshot),
            selectinload(Quote.passengers),
            selectinload(Quote.payment),
            selectinload(Quote.customer),
        )
        .where(
            Quote.id == quote_id,
            Quote.organization_id == current_user.active_organization_id,
        )
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()

    if not quote:
        raise AppError("Quote not found", status_code=404, error_code="NOT_FOUND")

    if quote.status not in (QuoteStatus.ready, QuoteStatus.sent):
        raise AppError(
            "Quote must be 'ready' or 'sent' to generate payment.",
            status_code=400,
            error_code="INVALID_STATUS",
        )

    if quote.valid_until < datetime.now(timezone.utc):
        raise AppError("Quote has expired.", status_code=400, error_code="QUOTE_EXPIRED")

    await assert_pax_gate(quote, db)
    await _revalidate_quote_items(quote)

    if quote.payment and quote.payment.status == PaymentStatus.captured:
        raise AppError(
            "Payment already captured for this quote.",
            status_code=400,
            error_code="ALREADY_PAID",
        )

    if quote.payment and quote.payment.status == PaymentStatus.pending:
        return quote.payment

    total_amount = sum(item.customer_total for item in quote.items)
    if total_amount <= 0:
        raise AppError("Quote total must be positive", status_code=400, error_code="INVALID_AMOUNT")

    idem_key = f"pay_link_{quote.id}"
    claimed = await claim_idempotency_key(db, idem_key, "create_payment_link")
    if not claimed:
        await db.refresh(quote, ["payment"])
        if quote.payment:
            return quote.payment
        raise AppError(
            "Payment creation already in progress",
            status_code=409,
            error_code="IDEMPOTENCY_CONFLICT",
        )

    order_id, payment_link_url = await _create_payment_link(quote, total_amount)

    payment = Payment(
        quote_id=quote.id,
        gateway_order_id=order_id,
        status=PaymentStatus.pending,
        amount=total_amount,
        idempotency_key=idem_key,
        payment_link_url=payment_link_url,
    )
    db.add(payment)
    try:
        await db.commit()
    except Exception as e:
        # AUDIT-016: unique constraint race — return existing payment
        await db.rollback()
        from sqlalchemy.exc import IntegrityError

        if isinstance(e, IntegrityError):
            await db.refresh(quote, ["payment"])
            if quote.payment:
                return quote.payment
        raise AppError(
            "Payment creation conflict",
            status_code=409,
            error_code="IDEMPOTENCY_CONFLICT",
        ) from e
    await db.refresh(payment)
    return payment


async def mark_quote_paid_offline(quote_id: str, current_user: User, db: AsyncSession):
    """Mark a quote as paid via offline methods (NEFT, cash). FIX-P21-06."""
    from app.services.audit import write_audit

    stmt = (
        select(Quote)
        .options(
            selectinload(Quote.items),
            selectinload(Quote.payment),
            selectinload(Quote.booking),
        )
        .where(
            Quote.id == quote_id,
            Quote.organization_id == current_user.active_organization_id,
        )
    )
    quote = (await db.execute(stmt)).scalar_one_or_none()

    if not quote:
        raise AppError("Quote not found", status_code=404, error_code="NOT_FOUND")

    if quote.status not in (QuoteStatus.ready, QuoteStatus.sent):
        raise AppError(
            "Quote must be 'ready' or 'sent' to mark paid offline.",
            status_code=400,
            error_code="INVALID_STATUS",
        )

    if quote.valid_until < datetime.now(timezone.utc):
        raise AppError("Quote has expired.", status_code=400, error_code="QUOTE_EXPIRED")

    if quote.payment and quote.payment.status == PaymentStatus.captured:
        raise AppError(
            "Payment already captured for this quote.",
            status_code=400,
            error_code="ALREADY_PAID",
        )

    if quote.payment:
        payment = quote.payment
        payment.status = PaymentStatus.captured
        payment.gateway_payment_id = f"OFFLINE_{uuid.uuid4().hex[:12]}"
    else:
        total_amount = sum(item.customer_total for item in quote.items)
        if total_amount <= 0:
            raise AppError("Quote total must be positive", status_code=400, error_code="INVALID_AMOUNT")
        payment = Payment(
            quote_id=quote.id,
            gateway_order_id=f"OFFLINE_ORDER_{uuid.uuid4().hex[:12]}",
            gateway_payment_id=f"OFFLINE_{uuid.uuid4().hex[:12]}",
            amount=total_amount,
            status=PaymentStatus.captured,
            idempotency_key=f"offline_pay_{quote.id}",
            payment_link_url=None,
        )
        db.add(payment)

    quote.status = QuoteStatus.paid

    await write_audit(
        db,
        organization_id=quote.organization_id,
        actor_user_id=current_user.id,
        action="payment.captured_offline",
        entity_type="quote",
        entity_id=str(quote.id),
        metadata={
            "payment_id": str(payment.id) if payment.id else None,
            "method": "offline",
        },
    )

    db.add(
        JobOutbox(
            type="booking_confirm",
            payload={"quote_id": str(quote.id)},
            status=JobStatus.pending,
            attempts=0,
            run_at=datetime.now(timezone.utc),
        )
    )

    await db.commit()
    await db.refresh(quote, ["items", "passengers", "booking"])
    return quote


async def process_razorpay_webhook(payload: RazorpayWebhookPayload, db: AsyncSession):
    event = payload.event
    if event not in ("payment.captured", "payment_link.paid"):
        logger.info("webhook_ignored", event=event)
        return {"status": "ignored"}

    payment_entity = payload.payload.get("payment", {}).get("entity", {})
    link_entity = payload.payload.get("payment_link", {}).get("entity", {})

    gateway_order_id = (
        payment_entity.get("order_id")
        or link_entity.get("order_id")
        or link_entity.get("id")
    )
    gateway_payment_id = payment_entity.get("id")
    webhook_amount = payment_entity.get("amount")
    if webhook_amount is None and link_entity:
        webhook_amount = link_entity.get("amount")
    webhook_currency = (payment_entity.get("currency") or link_entity.get("currency") or "INR").upper()

    # Fallback: match by tripos_quote_id note when order id missing
    notes = payment_entity.get("notes") or link_entity.get("notes") or {}
    quote_note_id = notes.get("tripos_quote_id") if isinstance(notes, dict) else None

    if not gateway_order_id and not quote_note_id:
        logger.error("webhook_missing_order_id")
        return {"status": "error", "message": "Missing order_id"}

    payment = None
    if gateway_order_id:
        payment = (
            await db.execute(select(Payment).where(Payment.gateway_order_id == gateway_order_id))
        ).scalar_one_or_none()
        # Also try matching plink id stored as gateway_order_id
        if not payment and link_entity.get("id"):
            payment = (
                await db.execute(
                    select(Payment).where(Payment.gateway_order_id == link_entity.get("id"))
                )
            ).scalar_one_or_none()

    if not payment and quote_note_id:
        payment = (
            await db.execute(select(Payment).where(Payment.quote_id == quote_note_id))
        ).scalar_one_or_none()

    if not payment:
        # ISSUE-09: Return non-200 so Razorpay retries — payment row may not be committed yet
        logger.error("webhook_payment_not_found", order_id=gateway_order_id, quote_id=quote_note_id)
        raise AppError("Payment not found for webhook", status_code=404, error_code="PAYMENT_NOT_FOUND")

    # AUDIT-007: amount/currency must match stored Payment (paise)
    if webhook_amount is None:
        logger.error("webhook_missing_amount", order_id=gateway_order_id)
        return {"status": "error", "message": "Missing amount"}
    try:
        webhook_amount_int = int(webhook_amount)
    except (TypeError, ValueError):
        logger.error("webhook_invalid_amount", amount=webhook_amount)
        return {"status": "error", "message": "Invalid amount"}
    if webhook_amount_int != payment.amount:
        logger.error(
            "webhook_amount_mismatch",
            order_id=gateway_order_id,
            expected=payment.amount,
            got=webhook_amount_int,
        )
        return {"status": "error", "message": "Amount mismatch"}
    if webhook_currency != "INR":
        logger.error("webhook_currency_mismatch", currency=webhook_currency)
        return {"status": "error", "message": "Currency mismatch"}

    if payment.status == PaymentStatus.captured:
        logger.info("webhook_idempotent_skip", payment_id=str(payment.id))
        return {"status": "ok", "message": "Already processed"}

    quote = (
        await db.execute(
            select(Quote)
            .options(selectinload(Quote.booking))
            .where(Quote.id == payment.quote_id)
        )
    ).scalar_one_or_none()

    if not quote:
        logger.error("webhook_quote_not_found", quote_id=str(payment.quote_id))
        return {"status": "error"}

    if quote.booking and quote.booking.status == BookingStatus.confirmed:
        payment.status = PaymentStatus.captured
        payment.gateway_payment_id = gateway_payment_id
        await db.commit()
        return {"status": "ok", "message": "Already booked — ack no-op"}

    if quote.valid_until < datetime.now(timezone.utc):
        logger.warning("payment_captured_quote_expired", quote_id=str(quote.id))
        payment.status = PaymentStatus.captured
        payment.gateway_payment_id = gateway_payment_id
        db.add(
            JobOutbox(
                type="manual_refund_review",
                payload={
                    "quote_id": str(quote.id),
                    "payment_id": str(payment.id),
                    "reason": "payment_captured_quote_expired",
                },
                status=JobStatus.pending,
                run_at=datetime.now(timezone.utc),
            )
        )
        
        await write_audit(
            db,
            organization_id=quote.organization_id,
            action="payment.captured_quote_expired",
            entity_type="quote",
            entity_id=str(quote.id),
            metadata={
                "payment_id": str(payment.id),
                "gateway_payment_id": gateway_payment_id,
                "needs_manual_support": True,
            },
        )
        
        await db.commit()
        return {"status": "ok", "message": "Captured but expired. Manual review required."}

    payment.status = PaymentStatus.captured
    payment.gateway_payment_id = gateway_payment_id
    quote.status = QuoteStatus.paid

    # ISSUE-03: Use SQL-level JSONB filter instead of Python-side full table scan
    already_queued = (
        await db.execute(
            select(JobOutbox.id).where(
                JobOutbox.type == "booking_confirm",
                JobOutbox.status.in_([JobStatus.pending, JobStatus.running]),
                JobOutbox.payload["quote_id"].as_string() == str(quote.id),
            ).limit(1)
        )
    ).scalar_one_or_none() is not None

    if not already_queued:
        db.add(
            JobOutbox(
                type="booking_confirm",
                payload={"quote_id": str(quote.id)},
                status=JobStatus.pending,
                run_at=datetime.now(timezone.utc),
            )
        )

    await write_audit(
        db,
        organization_id=quote.organization_id,
        action="payment.captured",
        entity_type="quote",
        entity_id=str(quote.id),
        metadata={
            "payment_id": str(payment.id),
            "gateway_payment_id": gateway_payment_id,
            "amount": payment.amount,
        },
    )

    await db.commit()
    logger.info("webhook_payment_captured", quote_id=str(quote.id))
    return {"status": "ok"}
