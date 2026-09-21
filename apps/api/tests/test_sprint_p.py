"""Sprint P — V1 leftover gates honesty (no hosted URLs required)."""
from __future__ import annotations

import py_compile
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def test_e2e_runs_recorded_green():
    text = (REPO_ROOT / "docs" / "e2e-runs.md").read_text(encoding="utf-8")
    assert "15 passed" in text
    assert "Sprint P" in text


def test_v1_exit_is_fix_v1():
    text = (REPO_ROOT / "docs" / "v1-exit-decision.md").read_text(encoding="utf-8")
    assert "FIX V1" in text
    assert "GO V2" in text


def test_sprint_p_status_board_exists():
    text = (REPO_ROOT / "docs" / "sprint-p-status.md").read_text(encoding="utf-8")
    assert "E2E green" in text
    assert "BLOCKED" in text or "hosted" in text.lower()


def test_hosted_smoke_script_compiles():
    path = API_ROOT / "scripts" / "hosted_smoke.py"
    assert path.is_file()
    py_compile.compile(str(path), doraise=True)


def test_inventory_default_mock_only():
    from app.core.config import Settings

    s = Settings(_env_file=None)
    assert s.inventory_supplier_codes == ["mock_supplier"]


def test_job_outbox_uses_pg_enum_mapping():
    source = (API_ROOT / "app" / "models" / "commercial.py").read_text(encoding="utf-8")
    assert 'name="jobstatus"' in source
    assert "create_type=False" in source


def test_revalidate_normalized_preserves_inventory_errors():
    source = (API_ROOT / "app" / "services" / "inventory.py").read_text(encoding="utf-8")
    assert "adapter.revalidate(offer)" in source
