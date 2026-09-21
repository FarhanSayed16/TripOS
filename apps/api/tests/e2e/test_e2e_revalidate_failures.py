"""E2E revalidate failures — mock FARE-CHG / TIMEOUT at pay and confirm."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import BookingFailureReason, BookingStatus
from tests.e2e.helpers import (
    create_customer,
    create_quote,
    drain_outbox,
    get_booking_for_quote,
    mark_ready,
    search_flights,
    send_quote,
    set_passengers,
)


def _fare_chg_offer(base: dict) -> dict:
    offer = dict(base)
    offer["id"] = str(uuid.uuid4())
    offer["supplier_code"] = "mock_supplier"
    offer["supplier_reference"] = f"MOCK-FARE-CHG-{uuid.uuid4().hex[:6]}"
    offer["raw_data"] = {**(offer.get("raw_data") or {}), "simulate": "fare_changed"}
    return offer


@pytest.mark.asyncio
async def test_fare_change_blocks_payment(api_client: AsyncClient):
    search_id, base_offer = await search_flights(api_client)
    offer = _fare_chg_offer(base_offer)
    customer_id = await create_customer(api_client, suffix="farepay")
    quote = await create_quote(
        api_client, customer_id=customer_id, search_id=search_id, offer=offer
    )
    quote_id = quote["id"]
    await set_passengers(api_client, quote_id)
    await mark_ready(api_client, quote_id)
    await send_quote(api_client, quote_id)

    pay_res = await api_client.post(f"/api/v1/quotes/{quote_id}/payment")
    assert pay_res.status_code == 409
    assert pay_res.json().get("error_code") == "FARE_CHANGED"


@pytest.mark.asyncio
async def test_supplier_timeout_blocks_payment(api_client: AsyncClient):
    """Mock TIMEOUT offer → payment revalidate → supplier_timeout / 409."""
    search_id, base_offer = await search_flights(api_client)
    offer = dict(base_offer)
    offer["id"] = str(uuid.uuid4())
    offer["supplier_code"] = "mock_supplier"
    offer["supplier_reference"] = f"MOCK-TIMEOUT-{uuid.uuid4().hex[:6]}"
    offer["raw_data"] = {**(offer.get("raw_data") or {}), "simulate": "timeout"}

    customer_id = await create_customer(api_client, suffix="timeout")
    quote = await create_quote(
        api_client, customer_id=customer_id, search_id=search_id, offer=offer
    )
    quote_id = quote["id"]
    await set_passengers(api_client, quote_id)
    await mark_ready(api_client, quote_id)
    await send_quote(api_client, quote_id)

    pay_res = await api_client.post(f"/api/v1/quotes/{quote_id}/payment")
    assert pay_res.status_code == 409
    assert pay_res.json().get("error_code") in ("SUPPLIER_TIMEOUT", "TIMEOUT")


@pytest.mark.asyncio
async def test_fare_change_after_offline_pay(
    api_client: AsyncClient, db: AsyncSession
):
    """Offline pay skips revalidate; confirm job catches fare_changed."""
    search_id, base_offer = await search_flights(api_client)
    offer = _fare_chg_offer(base_offer)
    customer_id = await create_customer(api_client, suffix="farejob")
    quote = await create_quote(
        api_client, customer_id=customer_id, search_id=search_id, offer=offer
    )
    quote_id = quote["id"]
    await set_passengers(api_client, quote_id)
    await mark_ready(api_client, quote_id)
    await send_quote(api_client, quote_id)

    offline = await api_client.post(f"/api/v1/quotes/{quote_id}/mark-paid-offline")
    assert offline.status_code == 200, offline.text

    processed = await drain_outbox(db, max_jobs=20, quote_id=quote_id)
    assert processed >= 1

    booking = await get_booking_for_quote(db, quote_id)
    assert booking is not None
    assert booking.status == BookingStatus.failed
    assert booking.failure_reason == BookingFailureReason.fare_changed
