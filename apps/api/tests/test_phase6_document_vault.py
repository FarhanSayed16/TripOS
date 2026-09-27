"""Live-inventory Phase 6 — document vault (local + S3/R2)."""
from __future__ import annotations

import py_compile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.services import document_storage as vault


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent.parent


def test_document_settings_defaults():
    s = Settings(_env_file=None)
    assert s.DOCUMENT_STORAGE_BACKEND == "local"
    assert s.DOCUMENT_MAX_BYTES == 10 * 1024 * 1024


def test_api_download_path_shape():
    assert vault.api_download_path("abc_def_file.pdf").endswith("/download")
    assert "documents/abc_def_file.pdf" in vault.api_download_path("abc_def_file.pdf")


def test_filename_from_storage_url():
    url = "/api/v1/documents/11111111-1111-1111-1111-111111111111_abcdef_ticket.pdf/download"
    assert (
        vault.filename_from_storage_url(url)
        == "11111111-1111-1111-1111-111111111111_abcdef_ticket.pdf"
    )
    assert vault.filename_from_storage_url(None) is None


def test_local_put_get_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(vault, "UPLOAD_DIR", tmp_path)
    with patch("app.services.document_storage.settings") as mock_s:
        mock_s.DOCUMENT_STORAGE_BACKEND = "local"
        name = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee_abcd1234_ticket.pdf"
        url = vault.put_bytes(name, b"%PDF-1.4 test", "application/pdf")
        assert url.endswith(f"{name}/download")
        data = vault.get_bytes(name)
        assert data == b"%PDF-1.4 test"
        vault.delete_object(name)
        assert vault.get_bytes(name) is None


def test_object_put_uses_boto3():
    mock_client = MagicMock()
    with (
        patch("app.services.document_storage.settings") as mock_s,
        patch("app.services.document_storage._s3_client", return_value=mock_client),
    ):
        mock_s.DOCUMENT_STORAGE_BACKEND = "r2"
        mock_s.DOCUMENT_S3_BUCKET = "tripos-docs"
        name = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee_abcd1234_ticket.pdf"
        url = vault.put_bytes(name, b"hello", "application/pdf")
        assert name in url
        mock_client.put_object.assert_called_once()
        kwargs = mock_client.put_object.call_args.kwargs
        assert kwargs["Bucket"] == "tripos-docs"
        assert kwargs["Key"] == f"tripos/documents/{name}"
        assert kwargs["Body"] == b"hello"


def test_object_get_and_presign():
    mock_client = MagicMock()
    body = MagicMock()
    body.read.return_value = b"pdf-bytes"
    mock_client.get_object.return_value = {"Body": body}
    mock_client.generate_presigned_url.return_value = "https://r2.example/presigned"

    with (
        patch("app.services.document_storage.settings") as mock_s,
        patch("app.services.document_storage._s3_client", return_value=mock_client),
    ):
        mock_s.DOCUMENT_STORAGE_BACKEND = "s3"
        mock_s.DOCUMENT_S3_BUCKET = "bucket"
        name = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee_abcd1234_ticket.pdf"
        assert vault.get_bytes(name) == b"pdf-bytes"
        assert vault.presigned_get_url(name) == "https://r2.example/presigned"


def test_production_local_guard_still_in_api():
    source = (API_ROOT / "app" / "api" / "documents.py").read_text(encoding="utf-8")
    assert "is_production" in source
    assert 'status_code=503' in source
    assert "document_storage" in source or "vault" in source
    assert "501" not in source  # Phase 6 removes stub 501


def test_share_link_endpoint_kept():
    source = (API_ROOT / "app" / "api" / "documents.py").read_text(encoding="utf-8")
    assert "share-link" in source
    assert "wa.me" in source


def test_hosted_smoke_documents_vault():
    text = (REPO_ROOT / "docs" / "ops" / "HOSTED_SMOKE.md").read_text(encoding="utf-8")
    assert "Document vault" in text
    assert "DOCUMENT_STORAGE_BACKEND" in text
    assert "503" in text


def test_boto3_in_pyproject():
    text = (API_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "boto3" in text


def test_phase6_modules_compile():
    for rel in (
        "app/services/document_storage.py",
        "app/api/documents.py",
        "app/core/config.py",
    ):
        py_compile.compile(str(API_ROOT / rel), doraise=True)
