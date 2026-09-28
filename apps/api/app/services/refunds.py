"""Refund lifecycle service (FC Phase 2)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.commercial import Payment, Refund, Quote
from app.models.enums import PaymentStatus, RefundStatus
from app.services.audit import write_audit


async def request_refund_for_payment(
    db: AsyncSession,
    payment: Payment,
    *,
    organization_id,
    amount: Optional[int] = None,
    reason: str = "manual",
    notes: Optional[str] = None,
    requested_by_user_id=None,
) -> Refund:
    """Create a refund row in `requested` state (gateway action still ops/manual for V1)."""
    # Avoid duplicate open refunds for same payment
    existing = (
        await db.execute(
            select(Refund).where(
                Refund.payment_id == payment.id,
                Refund.status.in_(
                    [RefundStatus.requested, RefundStatus.processing]
                ),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    refund = Refund(
        payment_id=payment.id,
        organization_id=organization_id,
        amount=int(amount if amount is not None else payment.amount),
        status=RefundStatus.requested,
        reason=reason,
        notes=notes,
        requested_by_user_id=requested_by_user_id,
    )
    db.add(refund)
    await db.flush()
    await write_audit(
        db,
        organization_id=organization_id,
        actor_user_id=requested_by_user_id,
        action="refund.requested",
        entity_type="payment",
        entity_id=str(payment.id),
        metadata={
            "refund_id": str(refund.id),
            "amount": refund.amount,
            "reason": reason,
        },
    )
    return refund


async def update_refund_status(
    db: AsyncSession,
    refund_id: uuid.UUID,
    *,
    status: RefundStatus,
    notes: Optional[str] = None,
    gateway_refund_id: Optional[str] = None,
    actor_user_id=None,
) -> Refund:
    refund = await db.get(Refund, refund_id)
    if not refund:
        raise ValueError("Refund not found")

    refund.status = status
    if notes is not None:
        refund.notes = notes
    if gateway_refund_id is not None:
        refund.gateway_refund_id = gateway_refund_id
    if status in (RefundStatus.succeeded, RefundStatus.failed):
        refund.processed_at = datetime.now(timezone.utc)

    await write_audit(
        db,
        organization_id=refund.organization_id,
        actor_user_id=actor_user_id,
        action=f"refund.{status.value}",
        entity_type="refund",
        entity_id=str(refund.id),
        metadata={
            "gateway_refund_id": refund.gateway_refund_id,
            "notes": refund.notes,
        },
    )
    return refund


async def list_refunds(
    db: AsyncSession,
    *,
    organization_id=None,
    status: Optional[RefundStatus] = None,
    limit: int = 50,
) -> List[Refund]:
    stmt = select(Refund).options(selectinload(Refund.payment)).order_by(Refund.created_at.desc())
    if organization_id:
        stmt = stmt.where(Refund.organization_id == organization_id)
    if status:
        stmt = stmt.where(Refund.status == status)
    stmt = stmt.limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def refunds_for_quote(db: AsyncSession, quote_id) -> List[Refund]:
    payment = (
        await db.execute(select(Payment).where(Payment.quote_id == quote_id))
    ).scalar_one_or_none()
    if not payment:
        return []
    return list(
        (
            await db.execute(
                select(Refund)
                .where(Refund.payment_id == payment.id)
                .order_by(Refund.created_at.desc())
            )
        )
        .scalars()
        .all()
    )


async def maybe_request_refund_on_cancel(
    db: AsyncSession,
    quote: Quote,
    *,
    requested_by_user_id=None,
) -> Optional[Refund]:
    """If payment captured and booking cancelled, open a refund request for ops."""
    await db.refresh(quote, attribute_names=["payment"])
    payment = quote.payment
    if not payment or payment.status != PaymentStatus.captured:
        # load payment if relationship not set
        payment = (
            await db.execute(select(Payment).where(Payment.quote_id == quote.id))
        ).scalar_one_or_none()
    if not payment or payment.status != PaymentStatus.captured:
        return None
    return await request_refund_for_payment(
        db,
        payment,
        organization_id=quote.organization_id,
        reason="booking_cancelled",
        notes="Auto-requested on cancel after captured payment",
        requested_by_user_id=requested_by_user_id,
    )
