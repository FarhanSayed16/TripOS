"""
Email delivery (Resend or mock).

AUDIT-019: never log full JWTs / magic links — redact token query params.
"""
import os
import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger(__name__)


def _get_resend():
    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        return None, ""
    try:
        import resend
    except ImportError:
        logger.warning("resend package not installed; falling back to mock email")
        return None, ""
    resend.api_key = api_key
    return resend, api_key


def _frontend_base() -> str:
    try:
        from app.core.config import settings

        return (settings.FRONTEND_URL or "").rstrip("/") or "http://localhost:3000"
    except Exception:
        return os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/") or "http://localhost:3000"


def redact_url_for_logs(url: str) -> str:
    """Replace token=... query values with a short suffix for safe logging."""
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        if "token" in qs and qs["token"]:
            raw = qs["token"][0]
            qs["token"] = [f"REDACTED_{raw[-6:]}" if len(raw) > 6 else "REDACTED"]
        redacted_query = urlencode({k: v[0] for k, v in qs.items()})
        return urlunparse(parsed._replace(query=redacted_query))
    except Exception:
        return "[redacted-url]"


async def send_verification_email(email: str, token: str):
    verification_url = f"{_frontend_base()}/verify?token={token}"
    resend, api_key = _get_resend()
    safe_url = redact_url_for_logs(verification_url)

    if not api_key or resend is None:
        logger.info("========== MOCK EMAIL ==========")
        logger.info("To: %s", email)
        logger.info("Subject: Verify your TripOS Account")
        logger.info("Link: %s", safe_url)
        logger.info("================================")
        return True

    try:
        r = resend.Emails.send({
            "from": "TripOS <onboarding@resend.dev>",
            "to": email,
            "subject": "Verify your TripOS Account",
            "html": f"<p>Please verify your TripOS account by clicking <a href='{verification_url}'>here</a>.</p>",
        })
        logger.info("Sent verification email to %s (link=%s): %s", email, safe_url, r)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", email, e)
        return False


async def send_password_reset_email(email: str, token: str):
    reset_url = f"{_frontend_base()}/reset-password?token={token}"
    resend, api_key = _get_resend()
    safe_url = redact_url_for_logs(reset_url)

    if not api_key or resend is None:
        logger.info("========== MOCK EMAIL ==========")
        logger.info("To: %s", email)
        logger.info("Subject: Reset your TripOS Password")
        logger.info("Link: %s", safe_url)
        logger.info("================================")
        return True

    try:
        r = resend.Emails.send({
            "from": "TripOS <onboarding@resend.dev>",
            "to": email,
            "subject": "Reset your TripOS Password",
            "html": f"<p>Please reset your TripOS password by clicking <a href='{reset_url}'>here</a>.</p>",
        })
        logger.info("Sent password reset email to %s (link=%s): %s", email, safe_url, r)
        return True
    except Exception as e:
        logger.error("Failed to send reset email to %s: %s", email, e)
        return False
