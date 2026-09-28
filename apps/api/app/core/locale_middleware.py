"""Resolve request locale early (FC Phase 5)."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.services.i18n import normalize_locale, parse_accept_language


class LocaleMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        q = request.query_params.get("locale")
        if q:
            request.state.locale = normalize_locale(q)
        else:
            parsed = parse_accept_language(request.headers.get("accept-language"))
            request.state.locale = parsed or "en"
        response = await call_next(request)
        response.headers["Content-Language"] = request.state.locale
        return response
