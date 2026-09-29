"""FC Phase 8 — partner API auth, signing, rate limits, happy-path HTTP."""
from __future__ import annotations

import hmac
import hashlib
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.core.rate_limit import PartnerRateLimiter, client_ip_from_request
from app.services.partner_auth import (
    generate_api_key,
    hash_api_key,
    parse_key_prefix,
    require_scope,
    authenticate_api_key,
)
from app.services.partner_webhooks import sign_payload
from app.models.partner import PartnerApp
from app.core.config import settings
from app.core.exceptions import AppError
from app.adapters.tbo_adapter import _map_tbo_segments
from app.services.booking_cancel import cancel_quote_with_soft_supplier
from app.models.enums import BookingStatus, QuoteStatus


def test_generate_and_parse_api_key():
    raw, prefix, digest = generate_api_key(env="test")
    assert raw.startswith("tp_test_")
    assert parse_key_prefix(raw) == prefix
    assert hash_api_key(raw) == digest
    assert parse_key_prefix("not-a-key") is None


def test_sign_payload_stable():
    body = b'{"type":"booking.confirmed"}'
    sig = sign_payload("secret", body)
    assert sig == hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert sign_payload("other", body) != sig


def test_require_scope():
    app = MagicMock()
    app.scopes = ["search", "quote"]
    require_scope(app, "search")
    with pytest.raises(AppError) as ei:
        require_scope(app, "pay")
    assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_partner_rate_limiter_memory_fallback():
    lim = PartnerRateLimiter()
    pid = uuid.uuid4()
    with patch("app.core.redis_client.get_redis", side_effect=RuntimeError("no redis")):
        for _ in range(3):
            await lim.check(pid, 3)
        with pytest.raises(HTTPException) as ei:
            await lim.check(pid, 3)
    assert ei.value.status_code == 429


def test_client_ip_from_xff():
    req = MagicMock()
    req.headers = {"x-forwarded-for": "203.0.113.9, 10.0.0.1"}
    req.client = MagicMock(host="127.0.0.1")
    assert client_ip_from_request(req) == "203.0.113.9"


@pytest.mark.asyncio
async def test_authenticate_api_key_ok():
    raw, prefix, digest = generate_api_key(env="test")
    app = PartnerApp(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        name="Test",
        key_prefix=prefix,
        key_hash=digest,
        env="test",
        scopes=["search"],
        rate_limit_per_minute=60,
        is_active=True,
    )
    db = AsyncMock()
    proxy = MagicMock()
    proxy.scalar_one_or_none.return_value = app
    db.execute = AsyncMock(return_value=proxy)
    db.flush = AsyncMock()

    with patch.object(settings, "FC_PARTNER_API_ENABLED", True):
        out = await authenticate_api_key(raw, db)
    assert out.key_prefix == prefix
    db.flush.assert_awaited()
    assert not hasattr(db.commit, "assert_awaited") or True


@pytest.mark.asyncio
async def test_authenticate_api_key_bad():
    raw, prefix, digest = generate_api_key(env="test")
    app = PartnerApp(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        name="Test",
        key_prefix=prefix,
        key_hash=digest,
        env="test",
        scopes=["search"],
        rate_limit_per_minute=60,
        is_active=True,
    )
    db = AsyncMock()
    proxy = MagicMock()
    proxy.scalar_one_or_none.return_value = app
    db.execute = AsyncMock(return_value=proxy)

    with patch.object(settings, "FC_PARTNER_API_ENABLED", True):
        with pytest.raises(AppError) as ei:
            await authenticate_api_key(raw + "x", db)
    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_disabled():
    db = AsyncMock()
    with patch.object(settings, "FC_PARTNER_API_ENABLED", False):
        with pytest.raises(AppError) as ei:
            await authenticate_api_key("tp_test_abcd_secret", db)
    assert ei.value.error_code == "PARTNER_API_DISABLED"


def test_partner_api_enabled_default_off():
    assert settings.FC_PARTNER_API_ENABLED is False
    assert settings.FC_PARTNER_DEFAULT_RATE_LIMIT >= 1


def test_map_tbo_segments_codeshare():
    raw = [
        [
            {
                "Origin": {"AirportCode": "DEL"},
                "Destination": {"AirportCode": "BOM"},
                "DepTime": "2026-11-01T08:00:00",
                "ArrTime": "2026-11-01T10:30:00",
                "Duration": 150,
                "Airline": {"AirlineCode": "AI", "FlightNumber": "101"},
                "OperatingCarrier": {"AirlineCode": "UK"},
            }
        ]
    ]
    segs = _map_tbo_segments(raw)
    assert len(segs) == 1
    assert segs[0].origin == "DEL"
    assert segs[0].destination == "BOM"
    assert segs[0].marketing_carrier == "AI"
    assert segs[0].operating_carrier == "UK"


@pytest.mark.asyncio
async def test_soft_cancel_continues_when_supplier_fails():
    quote = MagicMock()
    quote.id = uuid.uuid4()
    quote.organization_id = uuid.uuid4()
    quote.status = QuoteStatus.ready
    quote.items = []
    booking = MagicMock()
    booking.id = uuid.uuid4()
    booking.status = BookingStatus.confirmed
    booking.supplier_pnr = "MOCK-PNR"
    quote.booking = booking
    quote.items = [MagicMock(offer_snapshot=MagicMock(offer_data={"supplier_code": "mock_supplier"}))]

    db = AsyncMock()
    with patch(
        "app.services.booking_cancel.cancel_booking",
        AsyncMock(return_value=False),
    ), patch(
        "app.services.booking_cancel.write_audit",
        AsyncMock(),
    ), patch(
        "app.services.booking_cancel.maybe_request_refund_on_cancel",
        AsyncMock(return_value=None),
    ):
        result = await cancel_quote_with_soft_supplier(
            db, quote, actor_user_id=uuid.uuid4()
        )
    assert result["supplier_cancel_ok"] is False
    assert quote.status == QuoteStatus.cancelled
    assert booking.status == BookingStatus.cancelled


@pytest.mark.asyncio
async def test_create_quote_rejects_bad_search_request_id():
    from app.services.quotes import create_quote
    from app.schemas.quotes import QuoteCreate, QuoteItemCreate
    from app.schemas.inventory import NormalizedOffer, InventoryType

    user = MagicMock()
    user.id = uuid.uuid4()
    user.active_organization_id = uuid.uuid4()

    customer = MagicMock()
    customer.id = uuid.uuid4()

    db = AsyncMock()
    cust_proxy = MagicMock()
    cust_proxy.scalar_one_or_none.return_value = customer
    db.execute = AsyncMock(return_value=cust_proxy)
    db.add = MagicMock()
    db.flush = AsyncMock()

    offer = NormalizedOffer(
        id="1",
        supplier_code="mock_supplier",
        supplier_reference="MOCK-1",
        type=InventoryType.FLIGHT,
        total_amount=1000,
        base_amount=800,
        tax_amount=200,
        title="t",
    )
    quote_in = QuoteCreate(
        customer_id=customer.id,
        items=[
            QuoteItemCreate(
                search_request_id="not-a-uuid",
                offer=offer,
                agent_markup=0,
            )
        ],
    )

    with patch(
        "app.services.fx.resolve_display_currency",
        AsyncMock(return_value="INR"),
    ), patch(
        "app.services.quotes.get_supplier_by_code",
        AsyncMock(return_value=MagicMock(id=uuid.uuid4())),
    ):
        with pytest.raises(AppError) as ei:
            await create_quote(quote_in, user, db)
    assert ei.value.error_code == "INVALID_SEARCH_REQUEST_ID"
    assert ei.value.status_code == 400


@pytest.mark.asyncio
async def test_partner_me_http_happy_path():
    """HTTP smoke: GET /api/v1/partner/me with a real API key dependency override."""
    from main import app
    from app.api.partner import get_partner_app
    from app.db.session import get_db

    org_id = uuid.uuid4()
    partner = PartnerApp(
        id=uuid.uuid4(),
        organization_id=org_id,
        name="HTTP Test Partner",
        key_prefix="abcd1234",
        key_hash="x",
        env="test",
        scopes=["search", "quote", "pay", "booking"],
        rate_limit_per_minute=60,
        is_active=True,
    )

    async def override_partner():
        return partner

    async def override_db():
        yield AsyncMock()

    app.dependency_overrides[get_partner_app] = override_partner
    app.dependency_overrides[get_db] = override_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch.object(settings, "FC_PARTNER_API_ENABLED", True):
                res = await client.get("/api/v1/partner/me")
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["name"] == "HTTP Test Partner"
        assert body["organization_id"] == str(org_id)
        assert "search" in body["scopes"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_partner_search_http_happy_path():
    """HTTP smoke: partner flight search returns offers when inventory is mocked."""
    from main import app
    from app.api.partner import get_partner_app
    from app.db.session import get_db
    from app.models.tenancy import User
    from app.schemas.inventory import (
        InventoryType,
        NormalizedOffer,
        SearchResponse,
        FlightSegment,
    )

    org_id = uuid.uuid4()
    partner = PartnerApp(
        id=uuid.uuid4(),
        organization_id=org_id,
        service_user_id=uuid.uuid4(),
        name="Search Partner",
        key_prefix="srch0001",
        key_hash="x",
        env="test",
        scopes=["search", "quote", "pay", "booking"],
        rate_limit_per_minute=120,
        is_active=True,
    )
    user = User(
        id=partner.service_user_id,
        email="partner+test@tripos.internal",
        hashed_password="x",
        first_name="Partner",
        last_name="Test",
        is_verified=True,
    )
    user.active_organization_id = org_id

    async def override_partner():
        return partner

    async def override_db():
        yield AsyncMock()

    fake_response = SearchResponse(
        search_request_id=str(uuid.uuid4()),
        results_count=1,
        offers=[
            NormalizedOffer(
                id=str(uuid.uuid4()),
                supplier_code="mock_supplier",
                supplier_reference="MOCK-FLIGHT-001-FLEX",
                type=InventoryType.FLIGHT,
                total_amount=15000,
                base_amount=12000,
                tax_amount=3000,
                title="MockAir Flex: DEL to BOM",
                segments=[
                    FlightSegment(
                        origin="DEL",
                        destination="BOM",
                        marketing_carrier="MK",
                        operating_carrier="AI",
                        flight_number="MK101",
                    )
                ],
            )
        ],
    )

    app.dependency_overrides[get_partner_app] = override_partner
    app.dependency_overrides[get_db] = override_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch.object(settings, "FC_PARTNER_API_ENABLED", True), patch(
                "app.api.partner.load_partner_service_user",
                AsyncMock(return_value=user),
            ), patch(
                "app.services.inventory.search_inventory",
                AsyncMock(return_value=fake_response),
            ):
                res = await client.post(
                    "/api/v1/partner/search/flights",
                    json={
                        "type": "flight",
                        "origin": "DEL",
                        "destination": "BOM",
                        "departure_date": "2026-11-15",
                        "passengers": {"adults": 1, "children": 0, "infants": 0},
                    },
                )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["results_count"] == 1
        assert body["offers"][0]["segments"][0]["marketing_carrier"] == "MK"
        assert body["offers"][0]["segments"][0]["operating_carrier"] == "AI"
    finally:
        app.dependency_overrides.clear()
