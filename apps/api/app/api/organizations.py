import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.db.session import get_db
from app.models import User, Organization, OrganizationMember, OrgStatus
from app.schemas.organizations import OrganizationResponse, OrganizationUpdate, MemberResponse
from app.api.deps import get_current_user, require_org_admin, require_platform_admin

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.get("/me", response_model=OrganizationResponse)
async def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.active_organization_id:
        raise AppError("No active organization", status_code=404)
        
    stmt = select(Organization).where(Organization.id == current_user.active_organization_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    
    if not org:
        raise AppError("Organization not found", status_code=404)
        
    return org

@router.patch("/me", response_model=OrganizationResponse)
async def update_my_organization(
    data: OrganizationUpdate,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Organization).where(Organization.id == current_user.active_organization_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    
    if not org:
        raise AppError("Organization not found", status_code=404)
        
    if data.brand_name is not None:
        org.brand_name = data.brand_name
    if data.logo_url is not None:
        org.logo_url = data.logo_url
    if data.primary_color is not None:
        org.primary_color = data.primary_color
        
    await db.commit()
    await db.refresh(org)
    return org

@router.get("/members", response_model=List[MemberResponse])
async def list_organization_members(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.active_organization_id:
        raise AppError("No active organization", status_code=404)
        
    stmt = select(OrganizationMember).options(selectinload(OrganizationMember.user)).where(
        OrganizationMember.organization_id == current_user.active_organization_id
    )
    result = await db.execute(stmt)
    members = result.scalars().all()
    
    return members

@router.get("/pending", response_model=List[OrganizationResponse])
async def list_pending_organizations(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Organization).where(Organization.status == OrgStatus.pending_approval)
    result = await db.execute(stmt)
    orgs = result.scalars().all()
    return orgs

@router.post("/{org_id}/approve", response_model=OrganizationResponse)
async def approve_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Organization).where(Organization.id == org_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    
    if not org:
        raise AppError("Organization not found", status_code=404)
        
    org.status = OrgStatus.active
    await db.commit()
    await db.refresh(org)
    return org

@router.post("/{org_id}/reject", response_model=OrganizationResponse)
async def reject_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Organization).where(Organization.id == org_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    
    if not org:
        raise AppError("Organization not found", status_code=404)
        
    org.status = OrgStatus.inactive
    await db.commit()
    await db.refresh(org)
    return org

from app.models.tenancy import OrganizationDomain
from pydantic import BaseModel

class DomainCreate(BaseModel):
    domain: str

@router.post("/domains")
async def add_domain(
    data: DomainCreate,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    # Check if domain already exists
    stmt = select(OrganizationDomain).where(OrganizationDomain.domain == data.domain)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Domain already registered")
        
    domain_record = OrganizationDomain(
        organization_id=current_user.active_organization_id,
        domain=data.domain,
        is_verified=False,
        verification_token=uuid.uuid4().hex
    )
    db.add(domain_record)
    await db.commit()
    await db.refresh(domain_record)
    
    return {
        "id": str(domain_record.id),
        "domain": domain_record.domain,
        "is_verified": domain_record.is_verified,
        "verification_token": domain_record.verification_token
    }

@router.get("/domains")
async def list_domains(
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(OrganizationDomain).where(OrganizationDomain.organization_id == current_user.active_organization_id)
    domains = (await db.execute(stmt)).scalars().all()
    
    return [
        {
            "id": str(d.id),
            "domain": d.domain,
            "is_verified": d.is_verified,
            "verification_token": d.verification_token
        } for d in domains
    ]

@router.delete("/domains/{domain_id}")
async def delete_domain(
    domain_id: str,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(OrganizationDomain).where(
        OrganizationDomain.id == domain_id,
        OrganizationDomain.organization_id == current_user.active_organization_id
    )
    domain_record = (await db.execute(stmt)).scalar_one_or_none()
    if not domain_record:
        raise HTTPException(status_code=404, detail="Domain not found")
        
    await db.delete(domain_record)
    await db.commit()
    
    return {"status": "success"}


@router.post("/domains/{domain_id}/verify")
async def verify_domain(
    domain_id: str,
    payload: dict | None = None,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    FIX-P37-01: mark domain verified when TXT token is confirmed.
    Dev: POST {\"force\": true} when ENV!=production.
    """
    from app.core.config import settings

    stmt = select(OrganizationDomain).where(
        OrganizationDomain.id == domain_id,
        OrganizationDomain.organization_id == current_user.active_organization_id,
    )
    domain_record = (await db.execute(stmt)).scalar_one_or_none()
    if not domain_record:
        raise HTTPException(status_code=404, detail="Domain not found")

    force = bool((payload or {}).get("force")) and not settings.is_production
    expected = f"tripos-verify={domain_record.verification_token}"
    found = False

    if force:
        found = True
    else:
        try:
            import dns.resolver

            answers = dns.resolver.resolve(domain_record.domain, "TXT")
            for rdata in answers:
                txt = "".join(
                    [s.decode() if isinstance(s, bytes) else str(s) for s in rdata.strings]
                )
                if expected in txt or domain_record.verification_token in txt:
                    found = True
                    break
        except Exception:
            found = False

    if not found:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "DOMAIN_TXT_MISSING",
                "message": f"Add DNS TXT record: {expected}",
                "domain": domain_record.domain,
                "hint": 'In development, POST {"force": true} to mark verified.',
            },
        )

    domain_record.is_verified = True
    await db.commit()
    return {
        "id": str(domain_record.id),
        "domain": domain_record.domain,
        "is_verified": True,
        "method": "force" if force else "dns_txt",
    }

class SubAgentCreate(BaseModel):
    brand_name: str
    admin_email: str
    admin_first_name: str
    admin_last_name: str

@router.get("/network")
async def list_network(
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    """List sub-agents + paid quote GMV for each (FIX-P38-01)."""
    from sqlalchemy import func
    from app.core.config import settings
    from app.models.commercial import Quote, QuoteItem
    from app.models.enums import QuoteStatus

    stmt = select(Organization).where(
        Organization.parent_organization_id == current_user.active_organization_id
    )
    orgs = (await db.execute(stmt)).scalars().all()

    results = []
    network_gmv = 0
    for org in orgs:
        gmv_stmt = (
            select(func.coalesce(func.sum(QuoteItem.customer_total), 0))
            .select_from(QuoteItem)
            .join(Quote, Quote.id == QuoteItem.quote_id)
            .where(
                Quote.organization_id == org.id,
                Quote.status == QuoteStatus.paid,
            )
        )
        gmv = int((await db.execute(gmv_stmt)).scalar_one() or 0)
        network_gmv += gmv
        results.append(
            {
                "id": str(org.id),
                "brand_name": org.brand_name,
                "status": org.status.value if hasattr(org.status, "value") else org.status,
                "created_at": org.created_at.isoformat() if org.created_at else None,
                "gmv_paise": gmv,
            }
        )

    return {
        "sub_agents": results,
        "network_gmv_paise": network_gmv,
        "master_override_bps": settings.MASTER_COMMISSION_OVERRIDE_BPS,
    }

from app.core.security import get_password_hash

@router.post("/sub-agents")
async def create_sub_agent(
    data: SubAgentCreate,
    current_user: User = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new sub-agent organization under the current user's organization."""
    # 1. Create org
    slug = data.brand_name.lower().replace(" ", "-") + "-" + uuid.uuid4().hex[:6]
    
    new_org = Organization(
        brand_name=data.brand_name,
        slug=slug,
        status=OrgStatus.active, # Auto-activate sub-agents created by a master
        parent_organization_id=current_user.active_organization_id,
        business_type="sub_agent"
    )
    db.add(new_org)
    
    # 2. Check if user exists
    stmt = select(User).where(User.email == data.admin_email)
    existing_user = (await db.execute(stmt)).scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists. Currently only new users can be created for sub-agents.")
        
    # 3. Create user
    new_user = User(
        email=data.admin_email,
        hashed_password=get_password_hash("SubAgent123!"), # Default password, ideally would send an invite email
        first_name=data.admin_first_name,
        last_name=data.admin_last_name,
        is_verified=True,
    )
    db.add(new_user)
    await db.flush() # get user id
    
    # 4. Link user to org
    membership = OrganizationMember(
        user_id=new_user.id,
        organization_id=new_org.id,
        role="admin"
    )
    db.add(membership)
    
    new_user.active_organization_id = new_org.id
    
    await db.commit()
    
    return {
        "status": "success",
        "organization_id": str(new_org.id),
        "admin_email": new_user.email,
        "default_password": "SubAgent123!"
    }
