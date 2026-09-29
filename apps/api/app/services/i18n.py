"""Locale helpers + error message catalogs (FC Phase 5)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.config import settings

SUPPORTED_LOCALES = ("en", "hi")
DEFAULT_LOCALE = "en"

# error_code → locale → message (fallback: en, then original AppError.message)
ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    "BAD_REQUEST": {
        "en": "Bad request",
        "hi": "अमान्य अनुरोध",
    },
    "UNAUTHORIZED": {
        "en": "Authentication required",
        "hi": "प्रमाणीकरण आवश्यक है",
    },
    "FORBIDDEN": {
        "en": "You do not have permission to perform this action",
        "hi": "आपको यह क्रिया करने की अनुमति नहीं है",
    },
    "NOT_FOUND": {
        "en": "Resource not found",
        "hi": "संसाधन नहीं मिला",
    },
    "INVALID_CREDENTIALS": {
        "en": "Invalid email or password",
        "hi": "अमान्य ईमेल या पासवर्ड",
    },
    "TOKEN_REVOKED": {
        "en": "Session expired or revoked. Please sign in again.",
        "hi": "सत्र समाप्त या रद्द हो गया। कृपया फिर से साइन इन करें।",
    },
    "INVALID_CURRENCY": {
        "en": "Invalid currency code",
        "hi": "अमान्य मुद्रा कोड",
    },
    "INVALID_LOCALE": {
        "en": "Unsupported locale. Use en or hi.",
        "hi": "असमर्थित भाषा। en या hi का उपयोग करें।",
    },
    "FX_RATE_MISSING": {
        "en": "No FX rate configured for the preferred display currency",
        "hi": "पसंदीदा प्रदर्शन मुद्रा के लिए FX दर उपलब्ध नहीं है",
    },
    "PAX_REQUIRED": {
        "en": "Passenger/guest details are required",
        "hi": "यात्री/अतिथि विवरण आवश्यक हैं",
    },
    "PAX_INCOMPLETE": {
        "en": "Not enough passengers/guests on this quote",
        "hi": "इस कोट पर पर्याप्त यात्री/अतिथि नहीं हैं",
    },
    "PAX_NAME_REQUIRED": {
        "en": "All passengers must have a first and last name",
        "hi": "सभी यात्रियों का पहला और अंतिम नाम आवश्यक है",
    },
    "MIXED_PRODUCT_TYPE": {
        "en": "A quote can only contain one product type",
        "hi": "एक कोट में केवल एक उत्पाद प्रकार हो सकता है",
    },
    "INVALID_SUPPLIER": {
        "en": "Invalid supplier code",
        "hi": "अमान्य सप्लायर कोड",
    },
    "INVALID_STATUS": {
        "en": "Invalid status for this action",
        "hi": "इस क्रिया के लिए स्थिति अमान्य है",
    },
    "QUOTE_EXPIRED": {
        "en": "Quote has expired",
        "hi": "कोट की अवधि समाप्त हो गई है",
    },
    "ALREADY_PAID": {
        "en": "Quote is already paid",
        "hi": "कोट का भुगतान पहले ही हो चुका है",
    },
    "NO_ITEMS": {
        "en": "Quote has no items",
        "hi": "कोट में कोई आइटम नहीं है",
    },
    "SEARCH_THROTTLED_L2B": {
        "en": "Live search temporarily limited due to high look-to-book ratio",
        "hi": "उच्च लुक-टू-बुक अनुपात के कारण लाइव खोज अस्थायी रूप से सीमित है",
    },
    "AI_SEARCH_THROTTLED_L2B": {
        "en": "AI search is paused while look-to-book is critical",
        "hi": "लुक-टू-बुक गंभीर होने पर AI खोज रोक दी गई है",
    },
    "INVENTORY_UNAVAILABLE": {
        "en": "Inventory is no longer available or price cannot be refreshed",
        "hi": "इन्वेंटरी उपलब्ध नहीं है या मूल्य ताज़ा नहीं किया जा सकता",
    },
    "SUPPLIER_ERROR": {
        "en": "Supplier request failed",
        "hi": "सप्लायर अनुरोध विफल रहा",
    },
    "REVALIDATE_UNSUPPORTED": {
        "en": "Supplier does not support revalidation",
        "hi": "सप्लायर पुन:सत्यापन का समर्थन नहीं करता",
    },
    "INVALID_AMOUNT": {
        "en": "Quote total must be positive",
        "hi": "कोट कुल राशि धनात्मक होनी चाहिए",
    },
}


def normalize_locale(value: Optional[str]) -> str:
    raw = (value or "").strip().lower().replace("_", "-")
    if not raw:
        return getattr(settings, "DEFAULT_LOCALE", DEFAULT_LOCALE) or DEFAULT_LOCALE
    # Accept-Language style: hi-IN → hi
    primary = raw.split(",")[0].split("-")[0].strip()
    if primary in SUPPORTED_LOCALES:
        return primary
    # full tag match
    if raw in SUPPORTED_LOCALES:
        return raw
    return DEFAULT_LOCALE


def parse_accept_language(header: Optional[str]) -> Optional[str]:
    if not header:
        return None
    # Prefer first supported tag by q-order (simple parse)
    parts = []
    for chunk in header.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ";q=" in chunk:
            tag, q = chunk.split(";q=", 1)
            try:
                weight = float(q)
            except ValueError:
                weight = 0.0
        else:
            tag, weight = chunk, 1.0
        parts.append((tag.strip(), weight))
    parts.sort(key=lambda x: x[1], reverse=True)
    for tag, _ in parts:
        loc = normalize_locale(tag)
        if loc in SUPPORTED_LOCALES and tag.lower().startswith(loc):
            return loc
        primary = tag.split("-")[0].lower()
        if primary in SUPPORTED_LOCALES:
            return primary
    return None


def localize_error(error_code: str, locale: str, fallback: str) -> str:
    loc = normalize_locale(locale)
    by_code = ERROR_MESSAGES.get(error_code) or {}
    if loc in by_code:
        return by_code[loc]
    if DEFAULT_LOCALE in by_code:
        return by_code[DEFAULT_LOCALE]
    return fallback


async def resolve_locale(
    *,
    query_locale: Optional[str] = None,
    accept_language: Optional[str] = None,
    user: Any = None,
    organization: Any = None,
    db=None,
) -> str:
    """
    Priority: explicit query/body → user.locale → org.default_locale → Accept-Language → default.
    """
    if query_locale:
        return normalize_locale(query_locale)

    if user is not None:
        user_loc = getattr(user, "locale", None)
        if user_loc:
            return normalize_locale(user_loc)
        org_id = getattr(user, "active_organization_id", None)
        if organization is None and org_id is not None and db is not None:
            from app.models.tenancy import Organization

            organization = await db.get(Organization, org_id)

    if organization is not None:
        org_loc = getattr(organization, "default_locale", None)
        if org_loc:
            return normalize_locale(org_loc)

    parsed = parse_accept_language(accept_language)
    if parsed:
        return parsed

    return normalize_locale(getattr(settings, "DEFAULT_LOCALE", DEFAULT_LOCALE))
