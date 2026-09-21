"""E2E happy path — search → quote → send → pay → webhook → worker → booking."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import Payment, Quote
from app.models.enums import BookingStatus, QuoteStatus
from tests.e2e.helpers import (
    capture_via_webhook,
    create_customer,
    create_payment,
    create_quote,
    drain_outbox,
    get_booking_for_quote,
    mark_ready,
    pending_confirm_jobs,
    search_flights,
    send_quote,
    set_passengers,
)


@pytest.mark.asyncio
async def test_search_to_booking_happy_path(
    api_client: AsyncClient, test_org_and_user, db: AsyncSession
):
    search_id, offer = await search_flights(api_client)
    assert offer["supplier_code"] == "mock_supplier"

    customer_id = await create_customer(api_client)
    quote = await create_quote(
        api_client, customer_id=customer_id, search_id=search_id, offer=offer
    )
    quote_id = quote["id"]

    await set_passengers(api_client, quote_id)
    ready = await mark_ready(api_client, quote_id)
    assert ready["status"] == "ready"

    sent = await send_quote(api_client, quote_id)
    assert sent["status"] == "sent"

    payment = await create_payment(api_client, quote_id)
    payment_id = payment["id"]
    assert payment.get("payment_link_url")

    pay_row = (
        await db.execute(select(Payment).where(Payment.id == payment_id))
    ).scalar_one()
    assert pay_row.gateway_order_id

    await capture_via_webhook(db, pay_row.gateway_order_id, amount=pay_row.amount)

    quote_row = (
        await db.execute(select(Quote).where(Quote.id == quote_id))
    ).scalar_one()
    assert quote_row.status == QuoteStatus.paid

    jobs = await pending_confirm_jobs(db, quote_id)
    assert len(jobs) >= 1

    processed = await drain_outbox(db, max_jobs=20, quote_id=quote_id)
    assert processed >= 1

    booking = await get_booking_for_quote(db, quote_id)
    assert booking is not None
    assert booking.status == BookingStatus.confirmed
    assert booking.supplier_pnr
    assert booking.supplier_pnr.startswith("MOCK-PNR-")
