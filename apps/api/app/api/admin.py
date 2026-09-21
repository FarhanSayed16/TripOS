from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

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
        "dead_letter_jobs": dead_letter_jobs
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
    
    for code, adapter in AdapterRegistry._adapters.items():
        state = circuit_breaker.state.get(code, "CLOSED")
        is_open = circuit_breaker.is_open(code)
        failures = circuit_breaker.failures.get(code, 0)
        is_manual_override = circuit_breaker.manual_override.get(code, False)
        
        results.append({
            "code": code,
            "name": code.replace("_", " ").title(),
            "is_configured": code in configured_suppliers,
            "circuit_state": state,
            "is_open": is_open,
            "failures": failures,
            "is_manual_override": is_manual_override,
            "status": "Inactive" if is_manual_override else ("Failing" if is_open else "Active")
        })
        
    return {
        "global_strategy": strategy,
        "suppliers": results
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
