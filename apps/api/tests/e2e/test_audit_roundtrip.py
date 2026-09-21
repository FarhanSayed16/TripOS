"""Pytest: AuditEvent roundtrip — write_audit() → query back by entity_id (FIX-P21-01)."""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import AuditEvent
from app.services.audit import write_audit


@pytest.mark.asyncio
async def test_write_audit_roundtrip(test_org_and_user, db: AsyncSession):
    """write_audit() persists an AuditEvent that can be read back by entity_id + entity_type."""
    org = test_org_and_user["org"]
    user = test_org_and_user["user"]
    entity_id = str(uuid.uuid4())

    event = await write_audit(
        db,
        organization_id=org.id,
        actor_user_id=user.id,
        action="test.audit_roundtrip",
        entity_type="quote",
        entity_id=entity_id,
        metadata={"key": "value", "nested": {"a": 1}},
    )
    await db.commit()

    # Query back
    rows = (
        await db.execute(
            select(AuditEvent).where(
                AuditEvent.entity_id == entity_id,
                AuditEvent.entity_type == "quote",
                AuditEvent.organization_id == org.id,
            )
        )
    ).scalars().all()

    assert len(rows) == 1
    row = rows[0]
    assert row.action == "test.audit_roundtrip"
    assert row.actor_user_id == user.id
    assert row.entity_id == entity_id
    assert row.entity_type == "quote"
    assert row.metadata_payload == {"key": "value", "nested": {"a": 1}}


@pytest.mark.asyncio
async def test_audit_events_via_api(
    api_client: AsyncClient, test_org_and_user, db: AsyncSession
):
    """The /quotes/{id}/audit endpoint returns events filtered by entity_id."""
    from tests.e2e.helpers import create_customer, create_quote, search_flights

    search_id, offer = await search_flights(api_client)
    customer_id = await create_customer(api_client)
    quote = await create_quote(
        api_client, customer_id=customer_id, search_id=search_id, offer=offer
    )
    quote_id = quote["id"]

    # Write an audit event for this quote
    org = test_org_and_user["org"]
    await write_audit(
        db,
        organization_id=org.id,
        action="test.api_audit_check",
        entity_type="quote",
        entity_id=quote_id,
        metadata={"source": "pytest"},
    )
    await db.commit()

    # GET /api/v1/quotes/{quote_id}/audit
    res = await api_client.get(f"/api/v1/quotes/{quote_id}/audit")
    assert res.status_code == 200, res.text
    events = res.json()
    assert any(e["action"] == "test.api_audit_check" for e in events)
