"""Sprint K — admin dead-letters / reject / booking DTO (no DB)."""
from __future__ import annotations

import ast
import py_compile
from pathlib import Path

from app.models.enums import JobStatus, OrgStatus
from app.schemas.bookings import FAILURE_LABELS, failure_label


API_ROOT = Path(__file__).resolve().parents[1]


def test_org_status_has_inactive_not_suspended():
    assert hasattr(OrgStatus, "inactive")
    assert not hasattr(OrgStatus, "suspended")


def test_job_status_has_dead_not_failed():
    assert JobStatus.dead.value == "dead"
    assert not hasattr(JobStatus, "failed")


def test_admin_dead_letters_uses_dead_and_error_details():
    source = (API_ROOT / "app" / "api" / "admin.py").read_text(encoding="utf-8")
    assert "JobStatus.dead" in source
    assert "error_details" in source
    assert "JobStatus.failed" not in source
    assert "error_msg" not in source
    assert "OrgStatus.inactive" in source
    assert "OrgStatus.suspended" not in source


def test_failure_labels_cover_enum():
    for code in (
        "fare_changed",
        "sold_out",
        "supplier_timeout",
        "supplier_error",
        "missing_pax",
        "unknown",
    ):
        assert code in FAILURE_LABELS
        assert failure_label(code)


def test_bookings_api_fe_uses_api_slice():
    web = Path(__file__).resolve().parents[2] / "web" / "src" / "lib" / "api" / "bookingsApi.ts"
    text = web.read_text(encoding="utf-8")
    assert "injectEndpoints" in text
    assert "mock-token" not in text
    assert "localhost:8000" not in text


def test_sprint_k_modules_compile():
    for rel in (
        "app/api/admin.py",
        "app/api/bookings.py",
        "app/schemas/bookings.py",
        "app/schemas/quotes.py",
        "app/services/bookings.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)


def test_admin_failures_page_not_coming_soon():
    page = (
        Path(__file__).resolve().parents[2]
        / "web"
        / "src"
        / "app"
        / "(admin)"
        / "admin"
        / "failures"
        / "page.tsx"
    )
    text = page.read_text(encoding="utf-8")
    assert "ComingSoon" not in text
    assert "getAdminDeadLetters" in text or "useGetAdminDeadLettersQuery" in text
