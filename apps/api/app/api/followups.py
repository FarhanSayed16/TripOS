from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid
from datetime import datetime, timezone, timedelta
from urllib.parse import quote as url_quote

from app.api.deps import get_db, require_active_org
from app.models.tenancy import User
from app.models.commercial import FollowUp, Quote
from app.schemas.followups import FollowUpResponse, SnoozeRequest
from app.services.audit import write_audit

router = APIRouter(prefix="/followups", tags=["followups"])


@router.get("", response_model=List[FollowUpResponse])
async def list_followups(
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(FollowUp)
        .options(
            selectinload(FollowUp.quote).selectinload(Quote.customer),
            selectinload(FollowUp.quote).selectinload(Quote.items),
        )
        .where(
            FollowUp.organization_id == current_user.active_organization_id,
            FollowUp.status.in_(["pending", "snoozed"]),
        )
        .order_by(FollowUp.created_at.desc())
    )

    followups = (await db.execute(stmt)).scalars().all()

    results = []
    now = datetime.now(timezone.utc)
    for f in followups:
        if f.snoozed_until and f.snoozed_until > now:
            continue
        if f.status == "snoozed" and (not f.snoozed_until or f.snoozed_until <= now):
            f.status = "pending"

        resp = FollowUpResponse.model_validate(f)
        if f.quote:
            resp.quote_public_token = f.quote.public_token
            if f.quote.customer:
                resp.customer_name = (
                    f"{f.quote.customer.first_name} {f.quote.customer.last_name}"
                )

            total = sum(i.customer_total for i in f.quote.items) if f.quote.items else 0
            resp.amount_paise = total

            diff = now - f.quote.created_at
            resp.hours_overdue = int(diff.total_seconds() / 3600)

        results.append(resp)

    return results


@router.post("/{followup_id}/snooze", response_model=FollowUpResponse)
async def snooze_followup(
    followup_id: uuid.UUID,
    payload: SnoozeRequest,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    f = await db.get(FollowUp, followup_id)
    if not f or f.organization_id != current_user.active_organization_id:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    f.status = "snoozed"
    f.snoozed_until = datetime.now(timezone.utc) + timedelta(hours=payload.hours)

    await write_audit(
        db,
        organization_id=f.organization_id,
        actor_user_id=current_user.id,
        action="followup.snoozed",
        entity_type="followup",
        entity_id=str(f.id),
        metadata={"hours": payload.hours, "quote_id": str(f.quote_id)},
    )

    await db.commit()
    await db.refresh(f)
    return f


@router.post("/{followup_id}/dismiss", response_model=FollowUpResponse)
async def dismiss_followup(
    followup_id: uuid.UUID,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    f = await db.get(FollowUp, followup_id)
    if not f or f.organization_id != current_user.active_organization_id:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    f.status = "dismissed"

    await write_audit(
        db,
        organization_id=f.organization_id,
        actor_user_id=current_user.id,
        action="followup.dismissed",
        entity_type="followup",
        entity_id=str(f.id),
        metadata={"quote_id": str(f.quote_id)},
    )

    await db.commit()
    await db.refresh(f)
    return f


@router.post("/{followup_id}/send-reminder", response_model=dict)
async def send_reminder(
    followup_id: uuid.UUID,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    f = await db.get(FollowUp, followup_id)
    if not f or f.organization_id != current_user.active_organization_id:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    f.status = "sent"

    stmt = select(Quote).where(Quote.id == f.quote_id).options(selectinload(Quote.customer))
    quote = (await db.execute(stmt)).scalar_one_or_none()

    phone = ""
    if quote and quote.customer:
        phone = getattr(quote.customer, "phone_e164", None) or ""
    digits = "".join(filter(str.isdigit, phone))
    text = (
        "Hi! Just following up on your TripOS quote. "
        "Let me know if you have any questions."
    )
    wa_link = f"https://wa.me/{digits}?text={url_quote(text)}" if digits else None

    await write_audit(
        db,
        organization_id=f.organization_id,
        actor_user_id=current_user.id,
        action="followup.reminder_sent",
        entity_type="followup",
        entity_id=str(f.id),
        metadata={"quote_id": str(f.quote_id), "wa_link": bool(wa_link)},
    )

    await db.commit()

    return {"status": "success", "wa_link": wa_link}
