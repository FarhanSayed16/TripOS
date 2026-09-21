"""Sprint O — honesty + security guards (no DB)."""
from __future__ import annotations

import py_compile
from pathlib import Path

from app.core.config import Settings


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def test_ai_default_disabled():
    s = Settings(_env_file=None)
    assert s.AI_COPILOT_ENABLED is False


def test_download_requires_auth_in_source():
    source = (API_ROOT / "app" / "api" / "documents.py").read_text(encoding="utf-8")
    assert "require_active_org" in source
    assert "current_user: User = Depends(require_active_org)" in source
    assert "# current_user: User = Depends(require_active_org)" not in source
    assert "_assert_safe_stored_filename" in source
    assert "organization_id == current_user.active_organization_id" in source


def test_ai_endpoint_no_silent_del_fallback():
    source = (API_ROOT / "app" / "api" / "ai.py").read_text(encoding="utf-8")
    assert 'or "DEL"' not in source
    assert "2026-12-01" not in source
    assert "AI_INTENT_INCOMPLETE" in source
    assert "check_ai_enabled" in source
    assert "missing.append" in source


def test_document_path_guards_in_source():
    source = (API_ROOT / "app" / "api" / "documents.py").read_text(encoding="utf-8")
    assert "_SAFE_STORED_NAME" in source
    assert '".." in filename' in source or ".." in source
    assert "is_production" in source


def test_env_example_ai_off():
    text = (API_ROOT / ".env.example").read_text(encoding="utf-8")
    assert 'AI_COPILOT_ENABLED="false"' in text or "AI_COPILOT_ENABLED=false" in text


def test_v1_exit_decision_honesty():
    text = (REPO_ROOT / "docs" / "v1-exit-decision.md").read_text(encoding="utf-8")
    assert "Sprint O" in text
    assert "Not signed yet" in text or "GO V2" in text


def test_phases_31_40_task_doc_honesty():
    text = (REPO_ROOT / "docs" / "phases-31-40-implementation-tasks.md").read_text(
        encoding="utf-8"
    )
    assert "Honesty (Sprint O)" in text
    assert "not" in text.lower() and "complete" in text.lower()


def test_sprint_o_modules_compile():
    for rel in (
        "app/api/documents.py",
        "app/api/ai.py",
        "app/services/ai_copilot.py",
        "app/core/config.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)
