import phonenumbers
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.core.exceptions import AppError
from app.db.session import get_db
from app.models import User, Customer
from app.schemas.crm import CustomerCreate, CustomerResponse, CustomerUpdate, CustomerTimelineItem
from app.api.deps import require_active_org
from app.utils.pagination import PageParams, PaginatedResponse

router = APIRouter(prefix="/customers", tags=["customers"])


def normalize_phone(phone: str, region: str = "IN") -> str:
    try:
        parsed = phonenumbers.parse(phone, region)
        if not phonenumbers.is_valid_number(parsed):
            raise AppError("Invalid phone number", status_code=400, error_code="INVALID_PHONE")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        raise AppError("Could not parse phone number", status_code=400, error_code="INVALID_PHONE")


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(
    data: CustomerCreate,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    phone_e164 = normalize_phone(data.phone)

    stmt = select(Customer).where(
        Customer.phone_e164 == phone_e164,
        Customer.organization_id == current_user.active_organization_id,
        Customer.deleted_at.is_(None),
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise AppError(
            "Customer with this phone already exists in your organization",
            status_code=400,
            error_code="DUPLICATE_PHONE",
        )

    customer = Customer(
        organization_id=current_user.active_organization_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone_e164=phone_e164,
    )

    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.get("", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    search: str | None = None,
    params: PageParams = Depends(),
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    filters = [
        Customer.organization_id == current_user.active_organization_id,
        Customer.deleted_at.is_(None),
    ]

    if search:
        search_term = f"%{search}%"
        filters.append(
            or_(
                Customer.first_name.ilike(search_term),
                Customer.last_name.ilike(search_term),
                Customer.phone_e164.ilike(search_term),
                Customer.email.ilike(search_term),
            )
        )

    count_stmt = select(func.count()).select_from(Customer).where(*filters)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(Customer)
        .where(*filters)
        .order_by(Customer.created_at.desc())
        .offset(params.offset)
        .limit(params.limit)
    )
    result = await db.execute(stmt)
    customers = result.scalars().all()

    return PaginatedResponse(
        items=customers,
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organization_id == current_user.active_organization_id,
        Customer.deleted_at.is_(None),
    )
    customer = (await db.execute(stmt)).scalar_one_or_none()

    if not customer:
        raise AppError("Customer not found", status_code=404, error_code="NOT_FOUND")

    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organization_id == current_user.active_organization_id,
        Customer.deleted_at.is_(None),
    )
    customer = (await db.execute(stmt)).scalar_one_or_none()

    if not customer:
        raise AppError("Customer not found", status_code=404, error_code="NOT_FOUND")

    if data.first_name is not None:
        customer.first_name = data.first_name
    if data.last_name is not None:
        customer.last_name = data.last_name
    if data.email is not None:
        customer.email = data.email
    if data.phone is not None:
        phone_e164 = normalize_phone(data.phone)
        if phone_e164 != customer.phone_e164:
            dup_stmt = select(Customer).where(
                Customer.phone_e164 == phone_e164,
                Customer.organization_id == current_user.active_organization_id,
                Customer.deleted_at.is_(None),
            )
            if (await db.execute(dup_stmt)).scalar_one_or_none():
                raise AppError("Customer with this phone already exists", status_code=400, error_code="DUPLICATE_PHONE")
        customer.phone_e164 = phone_e164

    await db.commit()
    await db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=204)
async def soft_delete_customer(
    customer_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organization_id == current_user.active_organization_id,
        Customer.deleted_at.is_(None),
    )
    customer = (await db.execute(stmt)).scalar_one_or_none()
    if not customer:
        raise AppError("Customer not found", status_code=404, error_code="NOT_FOUND")

    customer.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return None


@router.get("/{customer_id}/timeline", response_model=List[CustomerTimelineItem])
async def get_customer_timeline(
    customer_id: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """ISSUE-04: Populate timeline with quotes and bookings for this customer."""
    from app.models.commercial import Quote, Booking
    from app.models.enums import QuoteStatus
    from sqlalchemy.orm import selectinload

    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organization_id == current_user.active_organization_id,
        Customer.deleted_at.is_(None),
    )
    if not (await db.execute(stmt)).scalar_one_or_none():
        raise AppError("Customer not found", status_code=404, error_code="NOT_FOUND")

    # Fetch quotes for this customer (org-scoped via customer ownership)
    quotes = (
        await db.execute(
            select(Quote)
            .options(selectinload(Quote.items), selectinload(Quote.booking))
            .where(
                Quote.customer_id == customer_id,
                Quote.organization_id == current_user.active_organization_id,
            )
            .order_by(Quote.created_at.desc())
        )
    ).scalars().all()

    timeline: List[CustomerTimelineItem] = []

    for q in quotes:
        total = sum(item.customer_total for item in q.items) / 100 if q.items else 0
        status_label = q.status.value if hasattr(q.status, "value") else str(q.status)

        timeline.append(
            CustomerTimelineItem(
                id=str(q.id),
                type="quote",
                title=f"Quote — ₹{total:,.0f}",
                description=f"Status: {status_label}",
                created_at=q.created_at,
            )
        )

        if q.booking:
            b = q.booking
            booking_status = b.status.value if hasattr(b.status, "value") else str(b.status)
            desc = f"PNR: {b.supplier_pnr}" if b.supplier_pnr else f"Status: {booking_status}"
            if b.failure_reason:
                reason = b.failure_reason.value if hasattr(b.failure_reason, "value") else str(b.failure_reason)
                desc += f" — {reason}"

            timeline.append(
                CustomerTimelineItem(
                    id=str(b.id),
                    type="booking",
                    title=f"Booking — {booking_status.title()}",
                    description=desc,
                    created_at=b.created_at,
                )
            )

    timeline.sort(key=lambda x: x.created_at, reverse=True)
    return timeline
