"""Pytest: cross-org cancel IDOR — Org A cannot cancel Org B's quote (FIX-P21-02)."""
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tenancy import User, Organization, OrganizationMember
from app.models.enums import OrgStatus, UserRole, QuoteStatus
from app.models.commercial import Quote
from main import app


@pytest.mark.asyncio
async def test_cross_org_cancel_returns_404(
    api_client: AsyncClient, test_org_and_user, db: AsyncSession
):
    """
    Create a quote under Org A (test_org_and_user), then attempt to cancel it
    while authenticated as Org B. Must get 404, not 200.
    """
    from tests.e2e.helpers import create_customer, create_quote, search_flights

    # --- Org A: create a quote ---
    search_id, offer = await search_flights(api_client)
    customer_id = await create_customer(api_client)
    quote = await create_quote(
        api_client, customer_id=customer_id, search_id=search_id, offer=offer
    )
    quote_id = quote["id"]
    assert quote["status"] == "draft"

    # --- Create Org B user ---
    org_b_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    org_b = Organization(
        id=org_b_id,
        slug=f"e2e-orgb-{org_b_id}",
        brand_name=f"E2E Org B {org_b_id}",
        status=OrgStatus.active,
    )
    user_b = User(
        id=user_b_id,
        email=f"orgb_{user_b_id}@example.com",
        hashed_password="fakehash",
        first_name="OrgB",
        last_name="User",
        is_verified=True,
    )
    member_b = OrganizationMember(
        organization_id=org_b_id,
        user_id=user_b_id,
        role=UserRole.admin,
    )
    db.add(org_b)
    db.add(user_b)
    db.add(member_b)
    await db.commit()

    # --- Build a client authenticated as Org B ---
    from app.api.deps import get_current_user
    from app.db.session import get_db

    user_b.active_organization_id = org_b_id

    async def override_get_current_user_b():
        return user_b

    async def override_get_db_b():
        yield db

    app.dependency_overrides[get_current_user] = override_get_current_user_b
    app.dependency_overrides[get_db] = override_get_db_b

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client_b:
        # Org B tries to cancel Org A's quote → must be 404
        res = await client_b.post(f"/api/v1/quotes/{quote_id}/cancel")
        assert res.status_code == 404, (
            f"Expected 404 for cross-org cancel, got {res.status_code}: {res.text}"
        )

    # Verify Org A's quote was NOT cancelled
    quote_row = (
        await db.execute(select(Quote).where(Quote.id == quote_id))
    ).scalar_one()
    assert quote_row.status == QuoteStatus.draft, (
        f"Quote should still be draft, but was {quote_row.status}"
    )

    # --- Cleanup Org B ---
    from sqlalchemy import text

    await db.execute(text(f"DELETE FROM organization_members WHERE user_id = '{user_b_id}'"))
    await db.execute(text(f"DELETE FROM users WHERE id = '{user_b_id}'"))
    await db.execute(text(f"DELETE FROM organizations WHERE id = '{org_b_id}'"))
    await db.commit()

    # Restore original overrides (will be cleared by api_client fixture teardown)
    app.dependency_overrides.clear()
