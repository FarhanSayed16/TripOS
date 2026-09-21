import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import settings
from app.schemas.inventory import InventoryType, NormalizedOffer
from app.services import ai_copilot
from app.services.ai_copilot import format_quote_draft, parse_travel_intent


@pytest.fixture(autouse=True)
def reset_ai_client():
    ai_copilot._client = None
    yield
    ai_copilot._client = None


@pytest.fixture
def mock_openai():
    with patch("app.services.ai_copilot.AsyncOpenAI") as mock:
        yield mock


@pytest.mark.asyncio
async def test_parse_travel_intent(mock_openai):
    mock_instance = mock_openai.return_value
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"type": "flight", "origin": "DEL", "destination": "BOM", "passengers": 2, "budget_max": 10000}'
            )
        )
    ]
    mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)

    settings.AI_COPILOT_ENABLED = True
    settings.OPENAI_API_KEY = "test"

    intent = await parse_travel_intent(
        "Delhi to Mumbai flight for 2 adults next Friday under 10k"
    )

    assert intent["type"] == "flight"
    assert intent["origin"] == "DEL"
    assert intent["destination"] == "BOM"
    assert intent["passengers"] == 2
    assert intent["budget_max"] == 10000
    assert "raw_message" in intent


@pytest.mark.asyncio
async def test_format_quote_draft_no_invented_ids(mock_openai):
    offers = [
        NormalizedOffer(
            id="offer1",
            supplier_code="mock_supplier",
            supplier_reference="MOCK-1",
            type=InventoryType.FLIGHT,
            title="Flight 1",
            description="Morning",
            total_amount=5000.0,
            base_amount=4000.0,
            tax_amount=1000.0,
            currency="INR",
        ),
        NormalizedOffer(
            id="offer2",
            supplier_code="mock_supplier",
            supplier_reference="MOCK-2",
            type=InventoryType.FLIGHT,
            title="Flight 2",
            description="Evening",
            total_amount=6000.0,
            base_amount=5000.0,
            tax_amount=1000.0,
            currency="INR",
        ),
    ]

    mock_instance = mock_openai.return_value
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"selected_offer_ids": ["offer1", "offer3"], "summary": "Here", "suggested_markup_paise": 50000}'
            )
        )
    ]
    mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)

    settings.AI_COPILOT_ENABLED = True
    settings.OPENAI_API_KEY = "test"

    draft = await format_quote_draft(offers, {"type": "flight"})

    assert draft["selected_offer_ids"] == ["offer1"]
    assert draft["suggested_markup_paise"] == 50000


@pytest.mark.asyncio
async def test_ai_disabled_raises_error(mock_openai):
    settings.AI_COPILOT_ENABLED = False
    settings.OPENAI_API_KEY = "test"

    with pytest.raises(ValueError, match="disabled"):
        await parse_travel_intent("test")


def test_ai_copilot_defaults_off():
    """FIX-P35-01: production-safe default."""
    from app.core.config import Settings

    s = Settings(_env_file=None)
    assert s.AI_COPILOT_ENABLED is False
