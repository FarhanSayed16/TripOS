"""Document vault storage — local disk or S3/R2-compatible (live-inventory Phase 6)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger()

UPLOAD_DIR = Path("uploads")


def backend_name() -> str:
    return (settings.DOCUMENT_STORAGE_BACKEND or "local").lower().strip()


def is_object_backend() -> bool:
    return backend_name() in ("s3", "r2")


def object_key_prefix() -> str:
    """Logical prefix inside the bucket (keeps keys tidy)."""
    return "tripos/documents/"


def full_object_key(stored_filename: str) -> str:
    return f"{object_key_prefix()}{stored_filename}"


def api_download_path(stored_filename: str) -> str:
    """Org-gated API path stored in BookingDocument.storage_url."""
    return f"/api/v1/documents/{stored_filename}/download"


def _require_object_config() -> None:
    if not settings.DOCUMENT_S3_BUCKET:
        raise RuntimeError("DOCUMENT_S3_BUCKET is required for s3/r2 storage")
    if not settings.DOCUMENT_S3_ACCESS_KEY or not settings.DOCUMENT_S3_SECRET_KEY:
        raise RuntimeError(
            "DOCUMENT_S3_ACCESS_KEY and DOCUMENT_S3_SECRET_KEY are required for s3/r2"
        )


def _s3_client():
    import boto3
    from botocore.config import Config

    _require_object_config()
    kwargs = {
        "service_name": "s3",
        "aws_access_key_id": settings.DOCUMENT_S3_ACCESS_KEY,
        "aws_secret_access_key": settings.DOCUMENT_S3_SECRET_KEY,
        "region_name": settings.DOCUMENT_S3_REGION or "auto",
        "config": Config(signature_version="s3v4"),
    }
    endpoint = (settings.DOCUMENT_S3_ENDPOINT or "").strip()
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    return boto3.client(**kwargs)


def local_path_for(stored_filename: str) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = (UPLOAD_DIR / stored_filename).resolve()
    root = UPLOAD_DIR.resolve()
    if not str(path).startswith(str(root) + os.sep) and path != root:
        raise ValueError("Invalid storage path")
    return path


def put_bytes(stored_filename: str, data: bytes, content_type: str) -> str:
    """
    Persist bytes. Returns the API download path for BookingDocument.storage_url
    (always org-gated via our download endpoint).
    """
    backend = backend_name()
    if backend == "local":
        path = local_path_for(stored_filename)
        path.write_bytes(data)
        logger.info("document_stored_local", filename=stored_filename, bytes=len(data))
        return api_download_path(stored_filename)

    if backend in ("s3", "r2"):
        client = _s3_client()
        key = full_object_key(stored_filename)
        client.put_object(
            Bucket=settings.DOCUMENT_S3_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type or "application/octet-stream",
        )
        logger.info(
            "document_stored_object",
            backend=backend,
            bucket=settings.DOCUMENT_S3_BUCKET,
            key=key,
            bytes=len(data),
        )
        return api_download_path(stored_filename)

    raise RuntimeError(f"Unknown DOCUMENT_STORAGE_BACKEND: {backend}")


def get_bytes(stored_filename: str) -> Optional[bytes]:
    backend = backend_name()
    if backend == "local":
        path = local_path_for(stored_filename)
        if not path.is_file():
            return None
        return path.read_bytes()

    if backend in ("s3", "r2"):
        client = _s3_client()
        key = full_object_key(stored_filename)
        try:
            obj = client.get_object(Bucket=settings.DOCUMENT_S3_BUCKET, Key=key)
            return obj["Body"].read()
        except Exception as e:
            logger.warning(
                "document_get_failed",
                key=key,
                error=str(e),
            )
            return None

    raise RuntimeError(f"Unknown DOCUMENT_STORAGE_BACKEND: {backend}")


def delete_object(stored_filename: str) -> None:
    backend = backend_name()
    if backend == "local":
        try:
            path = local_path_for(stored_filename)
            if path.is_file():
                path.unlink()
        except Exception as e:
            logger.warning("document_local_delete_failed", error=str(e))
        return

    if backend in ("s3", "r2"):
        try:
            client = _s3_client()
            key = full_object_key(stored_filename)
            client.delete_object(Bucket=settings.DOCUMENT_S3_BUCKET, Key=key)
        except Exception as e:
            logger.warning("document_object_delete_failed", error=str(e))
        return


def presigned_get_url(stored_filename: str, expires_seconds: int = 3600) -> Optional[str]:
    """Presigned GET for s3/r2 after caller has already enforced org auth."""
    if backend_name() not in ("s3", "r2"):
        return None
    try:
        client = _s3_client()
        key = full_object_key(stored_filename)
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.DOCUMENT_S3_BUCKET, "Key": key},
            ExpiresIn=max(60, min(int(expires_seconds), 86400)),
        )
    except Exception as e:
        logger.warning("document_presign_failed", error=str(e))
        return None


def filename_from_storage_url(storage_url: str | None) -> Optional[str]:
    """Extract stored filename from /api/v1/documents/{name}/download."""
    if not storage_url:
        return None
    parts = storage_url.rstrip("/").split("/")
    if len(parts) >= 2 and parts[-1] == "download":
        return parts[-2]
    return None
