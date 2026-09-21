"""Shared helpers for Sprint L E2E flows (current API routes)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import Booking, JobOutbox, Payment, Quote
from app.models.enums import JobStatus
from app.schemas.payments import RazorpayWebhookPayload
from app.services.payments import process_razorpay_webhook
from worker import poll_outbox


def flight_search_payload() -> dict[str, Any]:
    return {
        "type": "flight",
        "origin": "DEL",
        "destination": "BOM",
        "departure_date": (datetime.now(timezone.utc) + timedelta(days=30)).strftime(
            "%Y-%m-%d"
        ),
        "passengers": {"adults": 1, "children": 0, "infants": 0},
    }


async def search_flights(api_client: AsyncClient) -> tuple[str, dict]:
    res = await api_client.post(
        "/api/v1/inventory/search/flights", json=flight_search_payload()
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["results_count"] > 0
    assert data["offers"]
    # Prefer bookable mock offers (skip intentional sold-out / fare-change sims)
    offer = next(
        (
            o
            for o in data["offers"]
            if o.get("supplier_code") == "mock_supplier"
            and "SOLD-OUT" not in (o.get("supplier_reference") or "").upper()
            and "FARE-CHG" not in (o.get("supplier_reference") or "").upper()
            and "TIMEOUT" not in (o.get("supplier_reference") or "").upper()
        ),
        None,
    )
    if offer is None:
        offer = next(
            (
                o
                for o in data["offers"]
                if "SOLD-OUT" not in (o.get("supplier_reference") or "").upper()
            ),
            data["offers"][0],
        )
    return data["search_request_id"], offer


async def create_customer(api_client: AsyncClient, suffix: str | None = None) -> str:
    # Indian mobiles need 10 national digits; keep unique per call.
    phone = f"+919876{uuid.uuid4().int % 1_000_000:06d}"
    if suffix:
        phone = f"+919875{abs(hash(suffix)) % 1_000_000:06d}"
    res = await api_client.post(
        "/api/v1/customers",
        json={
            "first_name": "E2E",
            "last_name": "Customer",
            "phone": phone,
            "email": f"e2e_{uuid.uuid4().hex[:8]}@example.com",
        },
    )
    assert res.status_code in (200, 201), res.text
    return res.json()["id"]


async def create_quote(
    api_client: AsyncClient,
    *,
    customer_id: str,
    search_id: str,
    offer: dict,
    agent_markup: int = 50000,
) -> dict:
    res = await api_client.post(
        "/api/v1/quotes",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "search_request_id": search_id,
                    "offer": offer,
                    "agent_markup": agent_markup,
                }
            ],
        },
    )
    assert res.status_code == 200, res.text
    return res.json()


async def set_passengers(api_client: AsyncClient, quote_id: str) -> None:
    res = await api_client.put(
        f"/api/v1/quotes/{quote_id}/passengers",
        json=[
            {
                "first_name": "E2E",
                "last_name": "Pax",
                "date_of_birth": "1990-01-01",
            }
        ],
    )
    assert res.status_code == 200, res.text


async def mark_ready(api_client: AsyncClient, quote_id: str) -> dict:
    res = await api_client.post(f"/api/v1/quotes/{quote_id}/ready")
    assert res.status_code == 200, res.text
    return res.json()


async def send_quote(api_client: AsyncClient, quote_id: str) -> dict:
    res = await api_client.post(
        f"/api/v1/quotes/{quote_id}/send",
        json={"channel": "whatsapp", "content": "E2E test quote"},
    )
    assert res.status_code == 200, res.text
    return res.json()


async def create_payment(api_client: AsyncClient, quote_id: str) -> dict:
    res = await api_client.post(f"/api/v1/quotes/{quote_id}/payment")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data.get("payment_link_url") or data.get("status")
    return data


async def capture_via_webhook(
    db: AsyncSession,
    gateway_order_id: str,
    *,
    amount: int,
    currency: str = "INR",
) -> dict:
    payload = RazorpayWebhookPayload(
        event="payment.captured",
        payload={
            "payment": {
                "entity": {
                    "id": f"pay_e2e_{uuid.uuid4().hex[:8]}",
                    "order_id": gateway_order_id,
                    "status": "captured",
                    "amount": amount,
                    "currency": currency,
                }
            }
        },
    )
    return await process_razorpay_webhook(payload, db)


async def drain_outbox(
    db: AsyncSession, max_jobs: int = 50, *, quote_id: str | None = None
) -> int:
    """Process pending outbox jobs until idle (or max_jobs).

    If quote_id is set, prioritize that quote's booking_confirm jobs first
    so leftover jobs from prior E2E runs cannot starve the current scenario.
    """
    from app.models.enums import JobStatus

    if quote_id:
        # Bump matching jobs to the front by setting run_at to the past
        jobs = (
            await db.execute(
                select(JobOutbox).where(
                    JobOutbox.status == JobStatus.pending,
                    JobOutbox.type == "booking_confirm",
                )
            )
        ).scalars().all()
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        for job in jobs:
            payload = job.payload or {}
            if str(payload.get("quote_id")) == str(quote_id):
                job.run_at = now - timedelta(seconds=1)
            else:
                # Defer unrelated leftovers
                job.run_at = now + timedelta(hours=1)
        await db.commit()

    processed = 0
    for _ in range(max_jobs):
        did = await poll_outbox(db)
        if not did:
            break
        processed += 1
    return processed


async def get_booking_for_quote(db: AsyncSession, quote_id: str) -> Booking | None:
    await db.commit()  # ensure we see worker commits on shared session
    return (
        await db.execute(select(Booking).where(Booking.quote_id == quote_id))
    ).scalar_one_or_none()


async def pending_confirm_jobs(db: AsyncSession, quote_id: str) -> list[JobOutbox]:
    jobs = (
        await db.execute(
            select(JobOutbox).where(
                JobOutbox.type == "booking_confirm",
                JobOutbox.status.in_([JobStatus.pending, JobStatus.running, JobStatus.done]),
            )
        )
    ).scalars().all()
    return [j for j in jobs if (j.payload or {}).get("quote_id") == str(quote_id)]
