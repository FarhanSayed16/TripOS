"""AI Copilot HTTP API (FIX-P35-01: fail closed, no silent search fallbacks)."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_active_org
from app.core.config import settings
from app.models.tenancy import User
from app.schemas.ai import (
    ParseIntentRequest,
    ParsedIntent,
    QuoteDraft,
    SearchAndDraftRequest,
    SearchAndDraftResponse,
)
from app.schemas.inventory import InventoryType, PassengerQuery, SearchQuery
from app.services.ai_copilot import format_quote_draft, parse_travel_intent
from app.services.inventory import search_inventory
from app.core.exceptions import AppError

router = APIRouter(prefix="/ai", tags=["ai"])


def check_ai_enabled():
    if not settings.AI_COPILOT_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="AI Copilot is disabled on this environment.",
        )
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured.",
        )


def _intent_to_search_query(intent: ParsedIntent) -> SearchQuery:
    """
    Build SearchQuery only from explicit intent fields.
    Never invent origin/destination/date (FIX-P35-01).
    """
    missing: list[str] = []
    inv_type = intent.type if intent.type in ("flight", "hotel") else "flight"

    if inv_type == "flight" and not intent.origin:
        missing.append("origin")
    if not intent.destination:
        missing.append("destination")
    if not intent.departure_date:
        missing.append("departure_date")

    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "AI_INTENT_INCOMPLETE",
                "message": "Could not extract required search fields from the message.",
                "missing": missing,
            },
        )

    try:
        dep = date.fromisoformat(intent.departure_date)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "AI_INTENT_INVALID_DATE",
                "message": f"Invalid departure_date: {intent.departure_date}",
            },
        ) from e

    ret = None
    if intent.return_date:
        try:
            ret = date.fromisoformat(intent.return_date)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "AI_INTENT_INVALID_DATE",
                    "message": f"Invalid return_date: {intent.return_date}",
                },
            ) from e

    adults = max(int(intent.passengers or 1), 1)
    origin = intent.origin or intent.destination  # hotels: SearchQuery still requires origin

    return SearchQuery(
        type=InventoryType(inv_type),
        origin=origin,
        destination=intent.destination,
        departure_date=dep,
        return_date=ret,
        passengers=PassengerQuery(adults=adults, children=0, infants=0),
    )


@router.post("/parse-intent", response_model=ParsedIntent)
async def parse_intent_endpoint(
    request: ParseIntentRequest,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    check_ai_enabled()
    try:
        from app.services.i18n import resolve_locale

        locale = await resolve_locale(user=current_user, db=db)
        intent = await parse_travel_intent(request.message, locale=locale)
        return intent
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI provider error: {e}") from e


@router.post("/search-and-draft", response_model=SearchAndDraftResponse)
async def search_and_draft_endpoint(
    request: SearchAndDraftRequest,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    check_ai_enabled()
    try:
        from app.services.i18n import resolve_locale

        locale = await resolve_locale(user=current_user, db=db)
        intent_dict = await parse_travel_intent(request.message, locale=locale)
        intent = ParsedIntent(**intent_dict)
        sq = _intent_to_search_query(intent)

        search_resp = await search_inventory(
            sq, current_user, db, usage_source="ai_search"
        )
        offers = search_resp.offers

        draft_dict = await format_quote_draft(offers, intent_dict, locale=locale)
        draft = QuoteDraft(**draft_dict)

        return SearchAndDraftResponse(
            intent=intent,
            search_results=[o.model_dump(mode="json") for o in offers],
            draft=draft,
        )
    except AppError:
        raise
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI search-and-draft failed: {e}") from e
