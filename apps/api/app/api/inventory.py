from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.schemas.inventory import (
    SearchQuery,
    SearchResponse,
    RevalidateRequest,
    NormalizedOffer,
    InventoryType
)
from app.api.deps import require_active_org, get_db
from app.models.tenancy import User
from app.services.inventory import search_inventory, revalidate_offer
from app.core.rate_limit import inventory_rate_limiter

router = APIRouter(prefix="/inventory", tags=["inventory"])


def check_rate_limit(current_user: User = Depends(require_active_org)):
    """Dependency to check search rate limit per organization."""
    if not current_user.active_organization_id:
        raise HTTPException(status_code=403, detail="User is not assigned to an active organization")
    inventory_rate_limiter.check_rate_limit(current_user.active_organization_id)
    return current_user


@router.post("/search/flights", response_model=SearchResponse)
async def search_flights(
    query: SearchQuery,
    user: User = Depends(check_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for flights. Enforces rate limits and logs the request.
    """
    if query.type != InventoryType.FLIGHT:
        raise HTTPException(status_code=400, detail="Query type must be flight")
        
    return await search_inventory(query, user, db)


@router.post("/search/hotels", response_model=SearchResponse)
async def search_hotels(
    query: SearchQuery,
    user: User = Depends(check_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for hotels. Enforces rate limits and logs the request.
    """
    if query.type != InventoryType.HOTEL:
        raise HTTPException(status_code=400, detail="Query type must be hotel")
        
    return await search_inventory(query, user, db)


@router.post("/revalidate", response_model=NormalizedOffer)
async def revalidate(
    request: RevalidateRequest,
    user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Revalidates an offer before finalizing a quote or booking.
    """
    if not user.active_organization_id:
        raise HTTPException(status_code=403, detail="User is not assigned to an active organization")
        
    return await revalidate_offer(
        request,
        db=db,
        usage_source="user_revalidate",
        org_id=user.active_organization_id,
    )
