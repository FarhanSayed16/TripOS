"""FC Phase 1 — TBO live spine + BookResult + mode honesty."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.tbo_adapter import TboAdapter, tbo_live_mode_active
from app.adapters.tbo_simulated_client import TboSimulatedClient
from app.core.config import Settings
from app.schemas.booking_result import BookResult
from app.schemas.inventory import InventoryType, PassengerQuery, SearchQuery
from app.services.inventory import book_offer


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def test_fc_phase1_settings_defaults():
    s = Settings(_env_file=None)
    assert s.TBO_LIVE_ENABLED is False
    assert s.TBO_AUTO_TICKET is True
    assert s.TBO_AUTH_PATH.startswith("/")


def test_tbo_live_mode_requires_creds():
    with patch("app.adapters.tbo_adapter.settings") as mock_s:
        mock_s.TBO_LIVE_ENABLED = True
        mock_s.TBO_BASE_URL = None
        mock_s.TBO_CLIENT_ID = None
        mock_s.TBO_USER_NAME = None
        mock_s.TBO_PASSWORD = None
        with patch("app.adapters.tbo_adapter.TboLiveClient") as MockClient:
            inst = MagicMock()
            inst.credentials_ready.return_value = False
            MockClient.return_value = inst
            assert tbo_live_mode_active() is False


@pytest.mark.asyncio
async def test_tbo_simulated_search_marks_simulated():
    adapter = TboAdapter()
    # Force simulated regardless of env
    adapter._live = False
    adapter.client = TboSimulatedClient()
    q = SearchQuery(
        type=InventoryType.FLIGHT,
        origin="DEL",
        destination="BOM",
        departure_date=date.today() + timedelta(days=14),
        passengers=PassengerQuery(adults=1),
    )
    offers = await adapter.search(q)
    assert offers
    assert all(o.inventory_mode == "simulated" for o in offers)
    assert all("[SIMULATED]" in o.title for o in offers)
    assert all(str(o.raw_data.get("simulated")) == "True" for o in offers)


@pytest.mark.asyncio
async def test_tbo_simulated_book_returns_book_result():
    adapter = TboAdapter()
    adapter._live = False
    adapter.client = TboSimulatedClient()
    from app.schemas.inventory import NormalizedOffer

    offer = NormalizedOffer(
        id="1",
        supplier_code="tbo",
        supplier_reference="trace::TBO-RES-1",
        type=InventoryType.FLIGHT,
        total_amount=5700,
        base_amount=4500,
        tax_amount=1200,
        title="test",
    )
    result = await adapter.book(offer, [{"first_name": "A", "last_name": "B"}])
    assert isinstance(result, BookResult)
    assert result.pnr.startswith("SIM-TBO")
    assert result.supplier_booking_id


@pytest.mark.asyncio
async def test_book_offer_normalizes_str_pnr():
    class FakeAdapter:
        supplier_code = "x"

        async def book(self, offer, passengers):
            return "PLAIN-PNR"

    offer = MagicMock()
    offer.supplier_code = "x"
    with patch(
        "app.services.inventory.AdapterRegistry.get_adapter",
        return_value=FakeAdapter(),
    ):
        result = await book_offer(offer, [])
    assert isinstance(result, BookResult)
    assert result.pnr == "PLAIN-PNR"


def test_fc_phase0_docs_exist():
    assert (REPO_ROOT / "docs" / "phase-0" / "FC_CAPABILITY_MATRIX.md").is_file()
    assert (REPO_ROOT / "docs" / "phase-0" / "FC_PHASE_0_LOCK.md").is_file()
    assert (REPO_ROOT / "docs" / "ops" / "FC_STAGING_SECRETS_CHECKLIST.md").is_file()


def test_idempotency_helpers_exist():
    from app.utils import idempotency

    assert hasattr(idempotency, "claim_idempotency_key")
