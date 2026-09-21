"""Sprint N — pilot pack files exist (no DB)."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_pilot_pack_files_exist():
    docs = REPO / "docs"
    for name in (
        "pilot-onboarding-tracker.md",
        "agent-quickstart.md",
        "pilot-demo-script.md",
        "pilot-support-channel.md",
    ):
        path = docs / name
        assert path.is_file(), name
        text = path.read_text(encoding="utf-8")
        assert len(text) > 200


def test_tracker_links_quickstart_and_friction():
    text = (REPO / "docs" / "pilot-onboarding-tracker.md").read_text(encoding="utf-8")
    assert "Friction" in text
    assert "agent-quickstart" in text
    assert "Nilesh" in text


def test_quickstart_does_not_promise_auto_refund():
    text = (REPO / "docs" / "agent-quickstart.md").read_text(encoding="utf-8")
    assert "manual" in text.lower() or "Support" in text
    assert "never see your net" in text.lower() or "never see your net costs" in text.lower() or "net cost" in text.lower()
