from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid

from app.api.deps import get_db, require_platform_admin
from app.models.tenancy import User, Organization
from app.models.commercial import Booking, Payment, Quote, JobOutbox
from app.models.enums import OrgStatus, JobStatus

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/analytics")
async def get_admin_analytics(
    days: int = 30,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    """Phase 31.1: Aggregated platform analytics for V1 exit decision."""
    from sqlalchemy import func
    from datetime import datetime, timedelta, timezone
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Orgs
    active_orgs = (
        await db.execute(
            select(func.count(Organization.id)).where(Organization.status == OrgStatus.active)
        )
    ).scalar_one()

    # Quotes
    total_quotes = (
        await db.execute(
            select(func.count(Quote.id)).where(Quote.created_at >= cutoff)
        )
    ).scalar_one()

    # Bookings
    bookings = (
        await db.execute(
            select(Booking)
            .options(selectinload(Booking.quote).selectinload(Quote.items))
            .where(Booking.created_at >= cutoff)
        )
    ).scalars().all()

    total_bookings = len(bookings)
    confirmed_bookings = sum(1 for b in bookings if b.status == "confirmed")
    failed_bookings = sum(1 for b in bookings if b.status == "failed")
    booking_failure_rate = failed_bookings / total_bookings if total_bookings > 0 else 0.0
    
    total_gmv_paise = 0
    for b in bookings:
        if b.status == "confirmed" and b.quote and b.quote.items:
            total_gmv_paise += sum(item.customer_total for item in b.quote.items)

    # Dead jobs
    dead_letter_jobs = (
        await db.execute(
            select(func.count(JobOutbox.id)).where(
                JobOutbox.status == JobStatus.dead,
                JobOutbox.created_at >= cutoff
            )
        )
    ).scalar_one()

    # Monthly active transacting agents
    # Number of unique users who created a quote that turned into a confirmed booking
    active_agent_ids = set()
    for b in bookings:
        if b.status == "confirmed" and b.quote:
            active_agent_ids.add(b.quote.created_by_user_id)
            
    active_agents_count = len(active_agent_ids)
    avg_gmv_per_agent = total_gmv_paise / active_agents_count if active_agents_count > 0 else 0

    from app.services.supplier_usage import summarize_l2b
    from app.services.l2b_survival import get_survival_state
    from app.models.commercial import Payment
    from app.models.enums import PaymentStatus, BookingStatus

    l2b_7d = await summarize_l2b(db, days=7)
    survival = await get_survival_state(db, force=True)

    cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
    # Pay captured but booking failed (money stuck / ops gap)
    captured_failed_7d = (
        await db.execute(
            select(func.count(Booking.id))
            .join(Quote, Booking.quote_id == Quote.id)
            .join(Payment, Payment.quote_id == Quote.id)
            .where(
                Booking.status == BookingStatus.failed,
                Payment.status == PaymentStatus.captured,
                Booking.created_at >= cutoff_7d,
            )
        )
    ).scalar_one()

    return {
        "active_orgs": active_orgs,
        "total_quotes": total_quotes,
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_bookings,
        "failed_bookings": failed_bookings,
        "booking_failure_rate": round(booking_failure_rate, 3),
        "total_gmv_paise": total_gmv_paise,
        "monthly_active_transacting_agents": active_agents_count,
        "avg_gmv_per_agent_paise": int(avg_gmv_per_agent),
        "dead_letter_jobs": dead_letter_jobs,
        "l2b_7d": l2b_7d,
        "l2b_survival": survival,
        "payment_captured_booking_failed_7d": int(captured_failed_7d or 0),
    }


@router.get("/l2b")
async def get_admin_l2b(
    days: int = 7,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Rolling look-to-book ratios from supplier_usage_daily (live-inventory Phase 1)."""
    from app.services.supplier_usage import summarize_l2b
    from app.services.l2b_survival import get_survival_state

    summary = await summarize_l2b(db, days=days)
    survival = await get_survival_state(db, force=True, days=days)
    return {**summary, "survival": survival}


@router.get("/l2b/survival")
async def get_admin_l2b_survival(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Phase 7 survival soft-brake status (TTL widen + warm refresh pause)."""
    from app.services.l2b_survival import get_survival_state

    return await get_survival_state(db, force=True)


@router.get("/l2b/orgs")
async def get_admin_l2b_orgs(
    days: int = 7,
    limit: int = 20,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Top orgs by L2B ratio (live-inventory Phase 4)."""
    from app.services.supplier_usage import list_org_l2b_offenders
    from app.core.config import settings

    offenders = await list_org_l2b_offenders(db, days=days, limit=limit)
    # Attach brand names when available
    org_ids = [o["organization_id"] for o in offenders]
    names: dict[str, str] = {}
    if org_ids:
        from uuid import UUID

        uuid_ids = []
        for oid in org_ids:
            try:
                uuid_ids.append(UUID(oid))
            except ValueError:
                continue
        if uuid_ids:
            rows = (
                await db.execute(
                    select(Organization).where(Organization.id.in_(uuid_ids))
                )
            ).scalars().all()
            names = {str(r.id): r.brand_name for r in rows}
    for o in offenders:
        o["organization_name"] = names.get(o["organization_id"], "Unknown")

    return {
        "window_days": days,
        "warn_ratio": settings.L2B_WARN_RATIO,
        "critical_ratio": settings.L2B_CRITICAL_RATIO,
        "orgs": offenders,
    }

@router.get("/sentry-debug")
async def sentry_debug(current_user: User = Depends(require_platform_admin)):
    """Trigger an intentional error to test Sentry integration."""
    raise Exception("This is a test exception for Sentry observability.")

@router.get("/dead-letters")
async def list_dead_letters(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    """View exhausted background jobs (FIX-P24-01: JobStatus.dead + error_details)."""
    stmt = (
        select(JobOutbox)
        .where(JobOutbox.status == JobStatus.dead)
        .order_by(JobOutbox.updated_at.desc())
    )
    jobs = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": str(job.id),
            "type": job.type,
            "payload": job.payload,
            "error_details": job.error_details,
            "attempts": job.attempts,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }
        for job in jobs
    ]

@router.get("/organizations")
async def list_organizations(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Organization).order_by(Organization.created_at.desc())
    orgs = (await db.execute(stmt)).scalars().all()
    return orgs

@router.post("/organizations/{org_id}/approve")
async def approve_organization(
    org_id: str,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    org.status = OrgStatus.active
    await db.commit()
    await db.refresh(org)
    return org

@router.post("/organizations/{org_id}/reject")
async def reject_organization(
    org_id: str,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    org.status = OrgStatus.inactive
    await db.commit()
    await db.refresh(org)
    return org

@router.get("/bookings")
async def list_global_bookings(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Booking).options(
        selectinload(Booking.quote).selectinload(Quote.organization)
    ).order_by(Booking.created_at.desc())
    bookings = (await db.execute(stmt)).scalars().all()
    
    # Format for UI to include org details and quote public token
    results = []
    for b in bookings:
        results.append({
            "id": str(b.id),
            "quote_id": str(b.quote_id),
            "quote_public_token": b.quote.public_token if b.quote else None,
            "organization_name": b.quote.organization.brand_name if b.quote and b.quote.organization else "Unknown",
            "status": b.status,
            "failure_reason": b.failure_reason,
            "supplier_pnr": b.supplier_pnr,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })
    return results

@router.get("/payments")
async def list_global_payments(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Payment).options(
        selectinload(Payment.quote).selectinload(Quote.organization)
    ).order_by(Payment.created_at.desc())
    payments = (await db.execute(stmt)).scalars().all()
    
    results = []
    for p in payments:
        results.append({
            "id": str(p.id),
            "quote_id": str(p.quote_id),
            "organization_name": p.quote.organization.brand_name if p.quote and p.quote.organization else "Unknown",
            "amount": p.amount,
            "status": p.status,
            "gateway_order_id": p.gateway_order_id,
            "gateway_payment_id": p.gateway_payment_id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return results

from app.models.wallet import CommissionRule, WalletLedgerEntry

@router.get("/commissions")
async def list_admin_commissions(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    # This should list all orgs with pending/owed amounts
    stmt = select(Organization).options(selectinload(Organization.users))
    orgs = (await db.execute(stmt)).scalars().all()
    
    results = []
    for org in orgs:
        # Get ledger entries for org
        ledger_stmt = select(WalletLedgerEntry).where(WalletLedgerEntry.organization_id == org.id)
        entries = (await db.execute(ledger_stmt)).scalars().all()
        
        pending = sum(e.amount_paise for e in entries if e.status == "pending" and e.type == "commission_earned")
        available = sum(e.amount_paise for e in entries if e.status == "available") # Commission paid reduces this
        settled = sum(e.amount_paise for e in entries if e.status == "settled" and e.type == "commission_earned")
        
        results.append({
            "organization_id": str(org.id),
            "organization_name": org.brand_name,
            "pending_paise": pending,
            "available_paise": available,
            "settled_paise": settled,
        })
    return results

@router.post("/commissions/{org_id}/settle")
async def settle_commissions(
    org_id: str,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime, timezone
    # Settle all available commissions
    stmt = select(WalletLedgerEntry).where(
        WalletLedgerEntry.organization_id == org_id,
        WalletLedgerEntry.status == "available"
    )
    entries = (await db.execute(stmt)).scalars().all()
    
    total_settled = 0
    now = datetime.now(timezone.utc)
    for entry in entries:
        entry.status = "settled"
        entry.settled_at = now
        total_settled += entry.amount_paise
        
    if total_settled > 0:
        # Record payout entry
        payout = WalletLedgerEntry(
            organization_id=org_id,
            type="commission_paid",
            amount_paise=-total_settled,  # Debit the available balance
            status="settled",
            description="Commission payout",
            settled_at=now
        )
        db.add(payout)
        
    await db.commit()
    return {"status": "success", "settled_amount_paise": total_settled}


@router.get("/commissions/statement.csv")
async def export_commission_statement(
    org_id: Optional[str] = None,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """FC Phase 7 — download settle statement CSV for one org or all."""
    import uuid as uuid_mod
    from fastapi.responses import Response
    from app.services.commissions import export_commission_statement_csv

    oid = uuid_mod.UUID(org_id) if org_id else None
    csv_body = await export_commission_statement_csv(db, org_id=oid)
    filename = f"commission-statement-{org_id or 'all'}.csv"
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


from app.schemas.wallet import CommissionRuleResponse, CommissionRuleCreate

@router.get("/commission-rules", response_model=List[CommissionRuleResponse])
async def list_commission_rules(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CommissionRule)
    rules = (await db.execute(stmt)).scalars().all()
    return rules

@router.post("/commission-rules", response_model=CommissionRuleResponse)
async def create_commission_rule(
    payload: CommissionRuleCreate,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    rule = CommissionRule(**payload.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule

from app.core.circuit_breaker import circuit_breaker
from app.services.supplier_strategy import SupplierStrategy
from app.adapters.registry import AdapterRegistry
from app.core.config import settings

@router.get("/suppliers")
async def list_suppliers(
    current_user: User = Depends(require_platform_admin),
):
    """List all registered suppliers and their current circuit status."""
    results = []
    
    strategy = SupplierStrategy.get_strategy()
    configured_suppliers = settings.inventory_supplier_codes

    from app.services.supplier_metrics import supplier_metrics, last_offer_counts

    # Platform L2B contribution is global; per-supplier from usage tables would be Phase later
    for code, adapter in AdapterRegistry._adapters.items():
        state = circuit_breaker.state.get(code, "CLOSED")
        is_open = circuit_breaker.is_open(code)
        failures = circuit_breaker.failures.get(code, 0)
        is_manual_override = circuit_breaker.manual_override.get(code, False)
        metrics = supplier_metrics.snapshot(code)
        
        results.append({
            "code": code,
            "name": code.replace("_", " ").title(),
            "is_configured": code in configured_suppliers,
            "circuit_state": state,
            "is_open": is_open,
            "failures": failures,
            "is_manual_override": is_manual_override,
            "status": "Inactive" if is_manual_override else ("Failing" if is_open else "Active"),
            "health": metrics,
        })
        
    return {
        "global_strategy": strategy,
        "suppliers": results,
        "last_search_offer_counts": last_offer_counts(),
    }


@router.get("/suppliers/health")
async def get_suppliers_health(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """FC Phase 2 — latency / error rates + circuit + L2B strip."""
    from app.services.supplier_metrics import supplier_metrics
    from app.services.supplier_usage import summarize_l2b

    codes = list(AdapterRegistry._adapters.keys())
    health = supplier_metrics.all_snapshots(codes)
    l2b = await summarize_l2b(db, days=7)
    from app.services.supplier_metrics import last_offer_counts

    return {
        "window_seconds": 3600,
        "l2b_7d": l2b,
        "suppliers": health,
        "last_search_offer_counts": last_offer_counts(),
    }


@router.get("/refunds")
async def admin_list_refunds(
    status: str | None = None,
    limit: int = 50,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """FC Phase 2 — refund queue for ops."""
    from app.models.enums import RefundStatus
    from app.services.refunds import list_refunds
    from app.schemas.refunds import RefundResponse

    status_enum = None
    if status:
        try:
            status_enum = RefundStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid refund status")
    rows = await list_refunds(db, status=status_enum, limit=min(limit, 200))
    out = []
    for r in rows:
        item = RefundResponse.model_validate(r).model_dump()
        if r.payment:
            item["quote_id"] = r.payment.quote_id
        out.append(item)
    return {"items": out, "count": len(out)}


@router.post("/refunds/{refund_id}/status")
async def admin_update_refund_status(
    refund_id: str,
    body: dict,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark refund processing / succeeded / failed after gateway action."""
    from app.models.enums import RefundStatus
    from app.services.refunds import update_refund_status
    from app.schemas.refunds import RefundResponse

    try:
        new_status = RefundStatus(body.get("status"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid status")
    try:
        refund = await update_refund_status(
            db,
            uuid.UUID(refund_id),
            status=new_status,
            notes=body.get("notes"),
            gateway_refund_id=body.get("gateway_refund_id"),
            actor_user_id=current_user.id,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Refund not found")
    await db.commit()
    await db.refresh(refund)
    return RefundResponse.model_validate(refund)


@router.get("/audit/export")
async def admin_audit_export(
    days: int = 7,
    limit: int = 500,
    action_prefix: str | None = None,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """FC Phase 2 — export recent audit events for compliance / ops."""
    from datetime import datetime, timedelta, timezone
    from app.models.commercial import AuditEvent

    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 90)))
    stmt = (
        select(AuditEvent)
        .where(AuditEvent.created_at >= cutoff)
        .order_by(AuditEvent.created_at.desc())
        .limit(min(limit, 2000))
    )
    if action_prefix:
        stmt = stmt.where(AuditEvent.action.startswith(action_prefix))
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "window_days": days,
        "count": len(rows),
        "events": [
            {
                "id": str(e.id),
                "organization_id": str(e.organization_id) if e.organization_id else None,
                "actor_user_id": str(e.actor_user_id) if e.actor_user_id else None,
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "metadata": e.metadata_payload,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in rows
        ],
    }

@router.post("/suppliers/{code}/toggle")
async def toggle_supplier(
    code: str,
    disable: bool,
    current_user: User = Depends(require_platform_admin),
):
    """Manually disable or enable a supplier via the circuit breaker override."""
    if code not in AdapterRegistry._adapters:
        raise HTTPException(status_code=404, detail="Supplier not found in registry")
        
    circuit_breaker.set_manual_override(code, disable)
    return {"status": "success", "code": code, "disabled": disable}


# --- FC Phase 4: FX rates ---

@router.get("/fx-rates")
async def admin_list_fx_rates(
    active_only: bool = False,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.services.fx import list_fx_rates
    from app.core.config import settings

    rows = await list_fx_rates(db, active_only=active_only)
    return {
        "charge_currency": settings.CHARGE_CURRENCY,
        "fx_provider_enabled": settings.FX_PROVIDER_ENABLED,
        "items": [
            {
                "id": str(r.id),
                "base_currency": r.base_currency,
                "quote_currency": r.quote_currency,
                "rate": float(r.rate),
                "as_of": r.as_of.isoformat() if r.as_of else None,
                "source": r.source,
                "is_active": r.is_active,
            }
            for r in rows
        ],
    }


@router.post("/fx-rates")
async def admin_upsert_fx_rate(
    body: dict,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime
    from app.services.fx import upsert_fx_rate

    try:
        as_of = body.get("as_of")
        if isinstance(as_of, str):
            as_of = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        row = await upsert_fx_rate(
            db,
            base_currency=body.get("base_currency") or "INR",
            quote_currency=body["quote_currency"],
            rate=body["rate"],
            source=body.get("source") or "manual",
            as_of=as_of,
            is_active=bool(body.get("is_active", True)),
        )
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    await db.refresh(row)
    return {
        "id": str(row.id),
        "base_currency": row.base_currency,
        "quote_currency": row.quote_currency,
        "rate": float(row.rate),
        "as_of": row.as_of.isoformat() if row.as_of else None,
        "source": row.source,
        "is_active": row.is_active,
    }


@router.post("/fx-rates/seed")
async def admin_seed_fx_rates(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Bootstrap illustrative INR→USD/AED/EUR/GBP rates for staging."""
    from app.services.fx import seed_default_fx_rates

    rows = await seed_default_fx_rates(db)
    await db.commit()
    return {
        "seeded": len(rows),
        "pairs": [f"{r.base_currency}/{r.quote_currency}" for r in rows],
    }


# --- FC Phase 8 — Partner apps ---

from app.schemas.partner import PartnerAppCreate, PartnerAppUpdate, PartnerAppResponse
from app.models.partner import PartnerApp
from app.services.partner_auth import create_partner_app, rotate_partner_key
from app.services.supplier_usage import summarize_org_l2b
from datetime import datetime, timezone


def _partner_response(app: PartnerApp, *, api_key: str | None = None) -> PartnerAppResponse:
    return PartnerAppResponse(
        id=app.id,
        organization_id=app.organization_id,
        name=app.name,
        key_prefix=app.key_prefix,
        env=app.env,
        webhook_url=app.webhook_url,
        scopes=list(app.scopes or []),
        rate_limit_per_minute=app.rate_limit_per_minute,
        ip_allowlist=app.ip_allowlist,
        is_active=app.is_active,
        last_used_at=app.last_used_at,
        rotated_at=app.rotated_at,
        created_at=app.created_at,
        api_key=api_key,
        webhook_secret=app.webhook_secret if api_key else None,
    )


@router.get("/partners", response_model=List[PartnerAppResponse])
async def list_partner_apps(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(PartnerApp)
            .where(PartnerApp.deleted_at.is_(None))
            .order_by(PartnerApp.created_at.desc())
        )
    ).scalars().all()
    return [_partner_response(r) for r in rows]


@router.post("/partners", response_model=PartnerAppResponse)
async def create_partner_app_admin(
    body: PartnerAppCreate,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    app, raw_key = await create_partner_app(
        db,
        organization_id=body.organization_id,
        name=body.name,
        env=body.env,
        webhook_url=body.webhook_url,
        rate_limit_per_minute=body.rate_limit_per_minute,
        scopes=body.scopes,
        ip_allowlist=body.ip_allowlist,
    )
    return _partner_response(app, api_key=raw_key)


@router.patch("/partners/{partner_id}", response_model=PartnerAppResponse)
async def update_partner_app_admin(
    partner_id: uuid.UUID,
    body: PartnerAppUpdate,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    app = await db.get(PartnerApp, partner_id)
    if not app or app.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Partner app not found")
    if body.name is not None:
        app.name = body.name
    if body.webhook_url is not None:
        app.webhook_url = body.webhook_url or None
    if body.rate_limit_per_minute is not None:
        app.rate_limit_per_minute = body.rate_limit_per_minute
    if body.scopes is not None:
        app.scopes = body.scopes
    if body.ip_allowlist is not None:
        app.ip_allowlist = body.ip_allowlist
    if body.is_active is not None:
        app.is_active = body.is_active
    await db.commit()
    await db.refresh(app)
    return _partner_response(app)


@router.post("/partners/{partner_id}/rotate-key", response_model=PartnerAppResponse)
async def rotate_partner_key_admin(
    partner_id: uuid.UUID,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    app = await db.get(PartnerApp, partner_id)
    if not app or app.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Partner app not found")
    raw_key = await rotate_partner_key(db, app)
    return _partner_response(app, api_key=raw_key)


@router.delete("/partners/{partner_id}")
async def soft_delete_partner_app(
    partner_id: uuid.UUID,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    app = await db.get(PartnerApp, partner_id)
    if not app or app.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Partner app not found")
    app.is_active = False
    app.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "deleted"}


@router.get("/partners/{partner_id}/usage")
async def partner_usage(
    partner_id: uuid.UUID,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """L2B / look summary for the partner's tenant org."""
    app = await db.get(PartnerApp, partner_id)
    if not app or app.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Partner app not found")
    summary = await summarize_org_l2b(db, app.organization_id, days=7)
    return {
        "partner_app_id": str(app.id),
        "organization_id": str(app.organization_id),
        "name": app.name,
        "rate_limit_per_minute": app.rate_limit_per_minute,
        "l2b": summary,
    }
