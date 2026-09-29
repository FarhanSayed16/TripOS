import json
from openai import AsyncOpenAI
import structlog
from datetime import datetime
from typing import List

from app.core.config import settings
from app.schemas.ai import ParsedIntent, QuoteDraft
from app.schemas.inventory import NormalizedOffer

logger = structlog.get_logger()

# We'll initialize the client lazily if AI is enabled
_client = None

def get_ai_client():
    global _client
    if not settings.AI_COPILOT_ENABLED or not settings.OPENAI_API_KEY:
        raise ValueError("AI Copilot is disabled or OPENAI_API_KEY is not set.")
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client

async def parse_travel_intent(user_message: str, locale: str = "en") -> dict:
    """
    Uses LLM to extract structured search params from natural language.
    MUST NOT invent prices or availability.
    """
    client = get_ai_client()

    today_str = datetime.now().strftime("%Y-%m-%d")
    locale_note = (
        "The agent may write in Hindi or English; understand either. "
        "Always return JSON field values in English codes (IATA, dates)."
        if locale == "hi"
        else "Understand English queries. Return JSON field values in English codes."
    )

    system_prompt = f"""
    You are an AI assistant for a travel agent. Your job is to extract search intent from user queries.
    Today's date is {today_str}.
    Locale preference: {locale}. {locale_note}
    Extract the following fields into JSON format:
    - type: "flight", "hotel", or "package"
    - origin: 3-letter IATA code if flight, else string (optional)
    - destination: 3-letter IATA code if flight, else string (optional)
    - departure_date: YYYY-MM-DD (optional)
    - return_date: YYYY-MM-DD (optional)
    - passengers: integer (default 1)
    - budget_max: integer in INR (optional)

    Do NOT invent information that is not present in the user's message.
    """

    response = await client.chat.completions.create(
        model=settings.AI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error("ai_intent_parse_failed", error=str(e), content=content)
        raise ValueError("Failed to parse AI intent response.")
    data["raw_message"] = user_message
    return data

async def format_quote_draft(offers: List[NormalizedOffer], intent: dict, locale: str = "en") -> dict:
    """
    Uses LLM to select best matching offers and format a human-readable summary.
    Offer IDs MUST be a subset of the actual search results.
    """
    client = get_ai_client()

    compact_offers = []
    for o in offers:
        compact_offers.append(
            {
                "id": o.id,
                "title": o.title,
                "description": o.description,
                "supplier_price": o.total_amount,
                "currency": o.currency,
            }
        )

    summary_lang = (
        "Write the customer-facing summary in Hindi (Devanagari)."
        if locale == "hi"
        else "Write the customer-facing summary in English."
    )

    system_prompt = f"""
    You are an AI assistant for a travel agent.
    You are given a list of REAL inventory search results and the user's original intent.
    Locale preference: {locale}. {summary_lang}
    Your task is to:
    1. Select the best 1 to 3 offers from the provided list that match the intent.
    2. Write a short, persuasive summary of the selected options for the customer.
    3. Suggest a reasonable markup in paise (INR * 100). E.g. 500 INR = 50000 paise.

    Output strictly in JSON format with these exact keys:
    - selected_offer_ids: list of string IDs that EXACTLY match the provided offer IDs. Do NOT invent IDs.
    - summary: a short string message for the customer.
    - suggested_markup_paise: integer.
    """

    user_prompt = f"Intent:\n{json.dumps(intent)}\n\nOffers:\n{json.dumps(compact_offers)}"

    response = await client.chat.completions.create(
        model=settings.AI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        valid_ids = {o.id for o in offers}
        selected = data.get("selected_offer_ids", [])
        clean_selected = [sid for sid in selected if sid in valid_ids]
        data["selected_offer_ids"] = clean_selected
        return data
    except json.JSONDecodeError as e:
        logger.error("ai_draft_parse_failed", error=str(e), content=content)
        raise ValueError("Failed to parse AI draft response.")
