from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import csv
import io

from app.api.deps import get_db, require_active_org
from app.models.tenancy import User
from app.models.wallet import WalletLedgerEntry
from app.schemas.wallet import WalletSummary, WalletLedgerEntryResponse
from app.services.commissions import get_wallet_summary
from app.utils.pagination import PaginatedResponse, paginate

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.get("/summary", response_model=WalletSummary)
async def get_summary(
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db)
):
    summary = await get_wallet_summary(current_user.active_organization_id, db)
    return summary

@router.get("/ledger", response_model=PaginatedResponse[WalletLedgerEntryResponse])
async def list_ledger_entries(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(WalletLedgerEntry).where(
        WalletLedgerEntry.organization_id == current_user.active_organization_id
    ).order_by(WalletLedgerEntry.created_at.desc())
    
    return await paginate(db, stmt, limit, offset)

@router.get("/ledger/export")
async def export_ledger(
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(WalletLedgerEntry).where(
        WalletLedgerEntry.organization_id == current_user.active_organization_id
    ).order_by(WalletLedgerEntry.created_at.desc())
    
    result = await db.execute(stmt)
    entries = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Type", "Amount (INR)", "Status", "Booking ID", "Description"])
    
    for entry in entries:
        writer.writerow([
            str(entry.id),
            entry.created_at.isoformat(),
            entry.type,
            f"{entry.amount_paise / 100:.2f}",
            entry.status,
            str(entry.booking_id) if entry.booking_id else "",
            entry.description or ""
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=wallet_ledger_{current_user.active_organization_id}.csv"}
    )
