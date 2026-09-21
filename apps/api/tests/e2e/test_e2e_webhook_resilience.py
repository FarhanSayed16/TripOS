"""E2E webhook resilience — idempotent capture, fast reject, no double queue."""
import time
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import JobOutbox, Payment
from app.models.enums import JobStatus, PaymentStatus
from app.schemas.payments import RazorpayWebhookPayload
from app.services.payments import process_razorpay_webhook
from tests.e2e.helpers import (
    capture_via_webhook,
    create_customer,
    create_payment,
    create_quote,
    mark_ready,
    search_flights,
    send_quote,
    set_passengers,
)


@pytest.mark.asyncio
async def test_duplicate_webhook_no_double_job(
    api_client: AsyncClient, db: AsyncSession
):
    search_id, offer = await search_flights(api_client)
    customer_id = await create_customer(api_client, suffix="dupwh")
    quote = await create_quote(
        api_client, customer_id=customer_id, search_id=search_id, offer=offer
    )
    quote_id = quote["id"]
    await set_passengers(api_client, quote_id)
    await mark_ready(api_client, quote_id)
    await send_quote(api_client, quote_id)
    payment = await create_payment(api_client, quote_id)

    pay_row = (
        await db.execute(select(Payment).where(Payment.id == payment["id"]))
    ).scalar_one()

    await capture_via_webhook(db, pay_row.gateway_order_id, amount=pay_row.amount)
    await capture_via_webhook(db, pay_row.gateway_order_id, amount=pay_row.amount)

    jobs = (
        await db.execute(
            select(JobOutbox).where(JobOutbox.type == "booking_confirm")
        )
    ).scalars().all()
    matching = [
        j for j in jobs if (j.payload or {}).get("quote_id") == str(quote_id)
    ]
    assert len(matching) == 1


@pytest.mark.asyncio
async def test_webhook_responds_quickly_on_bad_json(api_client: AsyncClient):
    start = time.time()
    res = await api_client.post(
        "/api/v1/webhooks/razorpay",
        content=b"not-json",
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "invalid"},
    )
    elapsed = time.time() - start
    assert elapsed < 1.0
    assert res.status_code in (400, 503)


@pytest.mark.asyncio
async def test_late_webhook_after_capture_no_extra_job(
    api_client: AsyncClient, db: AsyncSession
):
    search_id, offer = await search_flights(api_client)
    customer_id = await create_customer(api_client, suffix="latewh")
    quote = await create_quote(
        api_client, customer_id=customer_id, search_id=search_id, offer=offer
    )
    quote_id = quote["id"]
    await set_passengers(api_client, quote_id)
    await mark_ready(api_client, quote_id)
    await send_quote(api_client, quote_id)
    payment = await create_payment(api_client, quote_id)

    pay_row = (
        await db.execute(select(Payment).where(Payment.id == payment["id"]))
    ).scalar_one()
    await capture_via_webhook(db, pay_row.gateway_order_id, amount=pay_row.amount)

    count_before = len(
        [
            j
            for j in (
                await db.execute(
                    select(JobOutbox).where(JobOutbox.type == "booking_confirm")
                )
            )
            .scalars()
            .all()
            if (j.payload or {}).get("quote_id") == str(quote_id)
        ]
    )

    # Late duplicate with different gateway payment id, same order
    payload = RazorpayWebhookPayload(
        event="payment.captured",
        payload={
            "payment": {
                "entity": {
                    "id": f"pay_late_{uuid.uuid4().hex[:6]}",
                    "order_id": pay_row.gateway_order_id,
                    "status": "captured",
                    "amount": pay_row.amount,
                    "currency": "INR",
                }
            }
        },
    )
    await process_razorpay_webhook(payload, db)

    count_after = len(
        [
            j
            for j in (
                await db.execute(
                    select(JobOutbox).where(JobOutbox.type == "booking_confirm")
                )
            )
            .scalars()
            .all()
            if (j.payload or {}).get("quote_id") == str(quote_id)
        ]
    )
    assert count_after == count_before
    assert count_before == 1
