"""FC Phase 7 — reissue, segments, deal codes, schedule change, commissions."""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from app.adapters.mock_adapter import MockAdapter
from app.core.config import settings
from app.models.servicing import BookingChangeRequest
from app.schemas.inventory import InventoryType, PassengerQuery, SearchQuery
from app.schemas.servicing import ReissueConfirmRequest, ReissueQuoteRequest, ScheduleChangeIngest
from app.services.commissions import export_commission_statement_csv
from app.services.reissue import confirm_reissue, quote_reissue
from app.services.schedule_change import ingest_schedule_change
from app.services.search_cache import cache_key


@pytest.mark.asyncio
async def test_mock_search_includes_segments_and_deal_code():
    adapter = MockAdapter()
    offers = await adapter.search(
        SearchQuery(
            type=InventoryType.FLIGHT,
            origin="DEL",
            destination="BOM",
            departure_date=date(2026, 10, 1),
            passengers=PassengerQuery(adults=1),
            deal_code="CORP10",
        )
    )
    flex = next(o for o in offers if o.fare_family == "Flex")
    assert flex.segments
    assert flex.segments[0].marketing_carrier == "MK"
    assert flex.segments[0].operating_carrier == "AI"
    assert flex.deal_code == "CORP10"
    # Deal discount applied vs undiscounted Flex (15000)
    plain = await adapter.search(
        SearchQuery(
            type=InventoryType.FLIGHT,
            origin="DEL",
            destination="BOM",
            departure_date=date(2026, 10, 1),
            passengers=PassengerQuery(adults=1),
        )
    )
    plain_flex = next(o for o in plain if o.fare_family == "Flex")
    assert flex.total_amount < plain_flex.total_amount


def test_cache_key_includes_deal_code():
    q1 = SearchQuery(
        type=InventoryType.FLIGHT,
        origin="DEL",
        destination="BOM",
        departure_date=date(2026, 10, 1),
        passengers=PassengerQuery(adults=1),
    )
    q2 = SearchQuery(
        type=InventoryType.FLIGHT,
        origin="DEL",
        destination="BOM",
        departure_date=date(2026, 10, 1),
        passengers=PassengerQuery(adults=1),
        deal_code="CORP10",
    )
    assert cache_key("mock_supplier", q1) != cache_key("mock_supplier", q2)
    assert "deal:CORP10" in cache_key("mock_supplier", q2)


def test_ndc_lcc_flags_default_off():
    assert settings.FC_NDC_ENABLED is False
    assert settings.FC_LCC_ENABLED is False


@pytest.mark.asyncio
async def test_quote_and_confirm_reissue_mock():
    org_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.active_organization_id = org_id

    item = MagicMock()
    item.customer_total = 1_500_000  # ₹15,000

    quote = MagicMock()
    quote.items = [item]
    quote.organization_id = org_id

    booking = MagicMock()
    booking.id = booking_id
    booking.quote = quote
    booking.status = MagicMock()
    # BookingStatus.confirmed comparison in service uses enum
    from app.models.enums import BookingStatus

    booking.status = BookingStatus.confirmed

    db = AsyncMock()
    # quote_reissue flow: execute -> scalar, add, commit, refresh
    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = booking
    db.execute = AsyncMock(return_value=result_proxy)
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def refresh(obj):
        if isinstance(obj, BookingChangeRequest):
            obj.created_at = obj.updated_at = MagicMock()
            # TimestampMixin usually set by DB — assign fake
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)
            obj.created_at = now
            obj.updated_at = now

    db.refresh = AsyncMock(side_effect=refresh)

    with patch.object(settings, "FC_REISSUE_ENABLED", True):
        quoted = await quote_reissue(
            booking_id,
            ReissueQuoteRequest(change_type="date", request_payload={"new_departure_date": "2026-11-01"}),
            user,
            db,
        )
    assert quoted.status == "quoted"
    assert quoted.supplier_diff_paise == 150000
    assert quoted.manual_sop is False

    # confirm with payment
    change_row = BookingChangeRequest(
        id=quoted.id,
        booking_id=booking_id,
        organization_id=org_id,
        change_type="date",
        status="quoted",
        request_payload={},
        supplier_diff_paise=150000,
        new_total_paise=1_650_000,
        currency="INR",
        manual_sop=False,
    )
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    change_row.created_at = now
    change_row.updated_at = now

    result_proxy2 = MagicMock()
    result_proxy2.scalar_one_or_none.return_value = change_row
    db.execute = AsyncMock(return_value=result_proxy2)

    confirmed = await confirm_reissue(
        quoted.id,
        ReissueConfirmRequest(payment_collected=True),
        user,
        db,
    )
    assert confirmed.status == "confirmed"


@pytest.mark.asyncio
async def test_reissue_manual_sop_when_disabled():
    org_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.active_organization_id = org_id

    item = MagicMock()
    item.customer_total = 1_000_000
    quote = MagicMock()
    quote.items = [item]
    booking = MagicMock()
    booking.id = booking_id
    booking.quote = quote
    from app.models.enums import BookingStatus

    booking.status = BookingStatus.confirmed

    db = AsyncMock()
    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = booking
    db.execute = AsyncMock(return_value=result_proxy)
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def refresh(obj):
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        obj.created_at = now
        obj.updated_at = now

    db.refresh = AsyncMock(side_effect=refresh)

    with patch.object(settings, "FC_REISSUE_ENABLED", False):
        quoted = await quote_reissue(
            booking_id,
            ReissueQuoteRequest(change_type="date"),
            user,
            db,
        )
    assert quoted.manual_sop is True
    assert quoted.status == "manual_sop"
    assert quoted.sop_hint


@pytest.mark.asyncio
async def test_schedule_change_ingest_notifies():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def refresh(obj):
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        obj.created_at = now
        obj.updated_at = now

    db.refresh = AsyncMock(side_effect=refresh)

    # First execute: booking lookup by PNR — none
    # Second execute: users for notify — empty so notified stays false path with org
    booking_proxy = MagicMock()
    booking_proxy.scalar_one_or_none.return_value = None
    users_proxy = MagicMock()
    users_proxy.scalars.return_value.all.return_value = []

    db.execute = AsyncMock(side_effect=[booking_proxy, users_proxy])

    event = await ingest_schedule_change(
        ScheduleChangeIngest(
            supplier_pnr="MOCK-PNR-TEST",
            supplier_code="mock_supplier",
            organization_id=uuid.uuid4(),
            message="Departure delayed 40 minutes",
            changes={"new_depart": "09:40"},
        ),
        db,
    )
    assert event.supplier_pnr == "MOCK-PNR-TEST"
    assert event.notified is False


@pytest.mark.asyncio
async def test_commission_statement_csv_headers():
    db = AsyncMock()
    proxy = MagicMock()
    proxy.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=proxy)
    csv_body = await export_commission_statement_csv(db)
    assert "entry_id" in csv_body
    assert "amount_paise" in csv_body
    assert "exported_at" in csv_body
