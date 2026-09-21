"""E2E validation gates — pax, expiry, tenant isolation."""
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import Quote
from app.models.crm import Customer
from app.models.enums import OrgStatus, QuoteStatus
from app.models.tenancy import Organization
from tests.e2e.helpers import (
    create_customer,
    create_quote,
    mark_ready,
    search_flights,
    send_quote,
    set_passengers,
)


@pytest.mark.asyncio
async def test_quote_without_pax_blocks_ready_and_payment(api_client: AsyncClient):
    search_id, offer = await search_flights(api_client)
    customer_id = await create_customer(api_client, suffix="nopax")
    quote = await create_quote(
        api_client, customer_id=customer_id, search_id=search_id, offer=offer
    )
    quote_id = quote["id"]

    ready_res = await api_client.post(f"/api/v1/quotes/{quote_id}/ready")
    assert ready_res.status_code == 400
    body = ready_res.json()
    assert body.get("error_code") in ("PAX_REQUIRED", "PAX_INCOMPLETE")

    pay_res = await api_client.post(f"/api/v1/quotes/{quote_id}/payment")
    assert pay_res.status_code == 400


@pytest.mark.asyncio
async def test_expired_quote_blocks_payment(api_client: AsyncClient, db: AsyncSession):
    search_id, offer = await search_flights(api_client)
    customer_id = await create_customer(api_client, suffix="expired")
    quote = await create_quote(
        api_client, customer_id=customer_id, search_id=search_id, offer=offer
    )
    quote_id = quote["id"]
    await set_passengers(api_client, quote_id)
    await mark_ready(api_client, quote_id)
    await send_quote(api_client, quote_id)

    row = await db.get(Quote, quote_id)
    assert row is not None
    row.valid_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db.commit()

    pay_res = await api_client.post(f"/api/v1/quotes/{quote_id}/payment")
    assert pay_res.status_code == 400
    assert pay_res.json().get("error_code") == "QUOTE_EXPIRED"


@pytest.mark.asyncio
async def test_tenant_isolation(api_client: AsyncClient, db: AsyncSession, test_org_and_user):
    org_b_id = uuid.uuid4()
    cust_b_id = uuid.uuid4()
    quote_id = uuid.uuid4()

    db.add(
        Organization(
            id=org_b_id,
            slug=f"org-b-{org_b_id.hex[:8]}",
            brand_name="Org B E2E",
            status=OrgStatus.active,
        )
    )
    db.add(
        Customer(
            id=cust_b_id,
            organization_id=org_b_id,
            first_name="Other",
            last_name="Org",
            phone_e164=f"+9197{uuid.uuid4().int % 10_000_000:07d}",
        )
    )
    db.add(
        Quote(
            id=quote_id,
            organization_id=org_b_id,
            customer_id=cust_b_id,
            created_by_user_id=test_org_and_user["user"].id,
            public_token=secrets.token_urlsafe(24),
            status=QuoteStatus.draft,
            valid_until=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )
    await db.commit()

    res = await api_client.get(f"/api/v1/quotes/{quote_id}")
    assert res.status_code == 404

    cancel = await api_client.post(f"/api/v1/quotes/{quote_id}/cancel")
    assert cancel.status_code == 404
