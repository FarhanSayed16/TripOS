from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.deps import require_active_org, get_db
from app.models.commercial import Payment, Quote
from app.models.tenancy import User
from app.schemas.payments import PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get("", response_model=dict)
async def api_list_payments(
    status: str = None,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """List payments for the active organization."""
    if not current_user.active_organization_id:
        raise HTTPException(status_code=403, detail="User must belong to an organization")

    # Join with Quote to filter by organization
    stmt = select(Payment).join(Quote).where(Quote.organization_id == current_user.active_organization_id)
    
    if status:
        stmt = stmt.where(Payment.status == status)
        
    stmt = stmt.order_by(Payment.created_at.desc())
    payments = (await db.execute(stmt)).scalars().all()
    
    return {"items": payments, "total": len(payments)}
