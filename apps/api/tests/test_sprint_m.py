"""Sprint M — refresh_quote alignment, bookings org gate, deploy blueprint (no DB)."""
from __future__ import annotations

import ast
import py_compile
from pathlib import Path

from app.models.enums import QuoteStatus


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def test_quote_status_has_no_superseded():
    assert not hasattr(QuoteStatus, "superseded")
    assert QuoteStatus.expired.value == "expired"


def test_refresh_quote_source_uses_real_columns():
    source = (API_ROOT / "app" / "services" / "quotes.py").read_text(encoding="utf-8")
    # Locate refresh_quote body
    assert "async def refresh_quote" in source
    assert "QuoteStatus.superseded" not in source
    assert "agent_markup_paise" not in source
    assert "total_sell_price_paise" not in source
    assert "customer_id=quote.customer_id" in source
    assert "QuoteStatus.expired" in source
    assert "customer_total" in source


def test_bookings_api_uses_require_active_org():
    source = (API_ROOT / "app" / "api" / "bookings.py").read_text(encoding="utf-8")
    assert "require_active_org" in source
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name in (
            "list_bookings",
            "api_export_bookings_csv",
        ):
            dumped = ast.dump(node)
            assert "require_active_org" in dumped


def test_render_yaml_has_worker_sentry_and_encryption():
    text = (REPO_ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "SENTRY_DSN" in text
    assert "ENCRYPTION_KEY" in text
    assert "FRONTEND_URL" in text
    # worker block should mirror secrets
    assert text.count("SENTRY_DSN") >= 2


def test_ops_runbooks_exist():
    ops = REPO_ROOT / "docs" / "ops"
    for name in (
        "PAYMENT_CAPTURED_BOOKING_FAILED.md",
        "RAZORPAY_REFUND_SOP.md",
        "PHASE_28_CHECKLIST.md",
        "HOSTED_SMOKE.md",
        "RENDER_RUNBOOK.md",
    ):
        assert (ops / name).is_file(), name


def test_sprint_m_modules_compile():
    for rel in (
        "app/services/quotes.py",
        "app/api/bookings.py",
        "app/api/webhooks.py",
        "worker.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)
