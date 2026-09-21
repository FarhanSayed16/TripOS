from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid

from app.api.deps import get_db, require_active_org, require_org_admin
from app.models.tenancy import User
from app.models.packages import Package, PackageItem
from app.schemas.packages import (
    PackageCreate, PackageUpdate, PackageResponse, PackageItemCreate
)
from app.models.enums import PackageStatus
from app.core.exceptions import AppError
from app.utils.pagination import PaginatedResponse, paginate

router = APIRouter(prefix="/packages", tags=["packages"])

@router.post("", response_model=PackageResponse)
async def create_package(
    payload: PackageCreate,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    pkg = Package(
        organization_id=current_user.active_organization_id,
        created_by_user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        destination=payload.destination,
        duration_days=payload.duration_days,
        base_price_paise=payload.base_price_paise,
        cover_image_url=payload.cover_image_url,
        status=PackageStatus.draft.value
    )
    db.add(pkg)
    await db.flush()

    for item_in in payload.items:
        item = PackageItem(
            package_id=pkg.id,
            **item_in.model_dump()
        )
        db.add(item)
    
    await db.commit()
    await db.refresh(pkg, ["items"])
    return pkg

@router.get("", response_model=PaginatedResponse[PackageResponse])
async def list_packages(
    status: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Package).where(
        Package.organization_id == current_user.active_organization_id,
        Package.deleted_at.is_(None)
    )
    if status:
        stmt = stmt.where(Package.status == status)
    
    stmt = stmt.order_by(Package.created_at.desc()).options(selectinload(Package.items))
    return await paginate(db, stmt, limit, offset)

@router.get("/{package_id}", response_model=PackageResponse)
async def get_package(
    package_id: uuid.UUID,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Package).where(
        Package.id == package_id,
        Package.organization_id == current_user.active_organization_id,
        Package.deleted_at.is_(None)
    ).options(selectinload(Package.items))
    pkg = (await db.execute(stmt)).scalar_one_or_none()
    
    if not pkg:
        raise AppError("Package not found", status_code=404)
    return pkg

@router.patch("/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: uuid.UUID,
    payload: PackageUpdate,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    pkg = await get_package(package_id, current_user, db)
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(pkg, key, value)
    
    await db.commit()
    await db.refresh(pkg, ["items"])
    return pkg

@router.post("/{package_id}/publish", response_model=PackageResponse)
async def publish_package(
    package_id: uuid.UUID,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    pkg = await get_package(package_id, current_user, db)
    
    if not pkg.items:
        raise AppError("Cannot publish a package with no items", status_code=400)
        
    pkg.status = PackageStatus.published.value
    await db.commit()
    await db.refresh(pkg, ["items"])
    return pkg

@router.delete("/{package_id}")
async def delete_package(
    package_id: uuid.UUID,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    pkg = await get_package(package_id, current_user, db)
    
    from datetime import datetime, timezone
    pkg.deleted_at = datetime.now(timezone.utc)
    
    await db.commit()
    return {"status": "success"}

@router.post("/{package_id}/items", response_model=PackageResponse)
async def add_package_item(
    package_id: uuid.UUID,
    payload: PackageItemCreate,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    pkg = await get_package(package_id, current_user, db)
    
    item = PackageItem(
        package_id=pkg.id,
        **payload.model_dump()
    )
    db.add(item)
    
    await db.commit()
    await db.refresh(pkg, ["items"])
    return pkg

@router.delete("/{package_id}/items/{item_id}", response_model=PackageResponse)
async def remove_package_item(
    package_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    pkg = await get_package(package_id, current_user, db)
    
    item_to_remove = next((item for item in pkg.items if item.id == item_id), None)
    if not item_to_remove:
        raise AppError("Item not found in package", status_code=404)
        
    await db.delete(item_to_remove)
    await db.commit()
    await db.refresh(pkg, ["items"])
    return pkg

@router.post("/{package_id}/to-quote")
async def package_to_quote(
    package_id: uuid.UUID,
    payload: dict,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a draft Quote from a package price snapshot (FIX-P32-01).

    V1 honesty: packages are **estimated cost snapshots**, not live inventory.
    Each item gets a synthetic OfferSnapshot so QuoteItem FK is satisfied.
    Pay → book still requires a bookable supplier offer (use inventory search
    for live mock path); package quotes are for CRM/share pricing.
    """
    pkg = await get_package(package_id, current_user, db)

    customer_id_str = payload.get("customer_id")
    if not customer_id_str:
        raise AppError("customer_id is required", status_code=400)

    customer_id = uuid.UUID(customer_id_str)

    from app.models.commercial import Quote, QuoteItem
    from app.models.inventory import OfferSnapshot, SearchRequest, Supplier
    from app.models.enums import QuoteStatus
    from app.core.config import settings
    import secrets
    from datetime import datetime, timezone, timedelta

    new_quote = Quote(
        organization_id=current_user.active_organization_id,
        customer_id=customer_id,
        created_by_user_id=current_user.id,
        status=QuoteStatus.draft,
        public_token=secrets.token_urlsafe(32),
        valid_until=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(new_quote)
    await db.flush()

    # Synthetic search request for package snapshot lineage
    search_req = SearchRequest(
        organization_id=current_user.active_organization_id,
        user_id=current_user.id,
        payload={"source": "package", "package_id": str(pkg.id)},
    )
    db.add(search_req)
    await db.flush()

    supplier = (
        await db.execute(select(Supplier).where(Supplier.code == "mock_supplier"))
    ).scalar_one_or_none()
    if not supplier:
        supplier = Supplier(code="mock_supplier", name="Mock Flight Supplier API", is_active=True)
        db.add(supplier)
        await db.flush()

    platform_fee = int(settings.PLATFORM_FEE_PAISE or 0)

    for p_item in pkg.items:
        supplier_cost = int(p_item.estimated_cost_paise or 0)
        agent_markup = int(supplier_cost * 0.1)
        customer_total = supplier_cost + agent_markup + platform_fee

        snapshot = OfferSnapshot(
            search_request_id=search_req.id,
            supplier_id=supplier.id,
            supplier_offer_id=f"PKG-{pkg.id}-{p_item.id}",
            offer_data={
                "id": str(uuid.uuid4()),
                "supplier_code": "mock_supplier",
                "supplier_reference": f"PKG-SNAPSHOT-{p_item.id}",
                "type": p_item.type or "flight",
                "title": getattr(p_item, "title", None) or pkg.title,
                "description": "Package price snapshot (not live inventory)",
                "total_amount": supplier_cost / 100.0,
                "base_amount": supplier_cost / 100.0,
                "tax_amount": 0,
                "currency": "INR",
                "raw_data": {"package_id": str(pkg.id), "package_item_id": str(p_item.id)},
            },
        )
        db.add(snapshot)
        await db.flush()

        db.add(
            QuoteItem(
                quote_id=new_quote.id,
                offer_snapshot_id=snapshot.id,
                supplier_cost=supplier_cost,
                agent_markup=agent_markup,
                platform_fee=platform_fee,
                customer_total=customer_total,
            )
        )

    await db.commit()
    await db.refresh(new_quote, ["items", "passengers", "booking"])

    from app.schemas.quotes import QuoteResponse
    return QuoteResponse.model_validate(new_quote)
