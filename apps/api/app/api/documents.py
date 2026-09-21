"""Booking document upload / download (FIX-P34-01: auth + path safety)."""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, require_active_org
from app.core.config import settings
from app.models.commercial import Booking, BookingDocument
from app.models.tenancy import User
from app.schemas.documents import BookingDocumentResponse

router = APIRouter(prefix="/bookings", tags=["documents"])
doc_router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path("uploads")
# Disk filenames we create: {booking_id}_{hex}_{sanitized_original}
_SAFE_STORED_NAME = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_[0-9a-f]+_.+$",
    re.IGNORECASE,
)


def _sanitize_original_filename(name: str | None) -> str:
    base = Path(name or "file").name
    base = base.replace("..", "").replace("/", "").replace("\\", "").strip()
    return base[:180] or "file"


def _assert_safe_stored_filename(filename: str) -> None:
    """Reject path traversal and unexpected shapes before touching the filesystem."""
    if not filename or filename != Path(filename).name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not _SAFE_STORED_NAME.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")


def _resolve_upload_path(stored_filename: str) -> Path:
    _assert_safe_stored_filename(stored_filename)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = (UPLOAD_DIR / stored_filename).resolve()
    root = UPLOAD_DIR.resolve()
    if not str(path).startswith(str(root) + os.sep) and path != root:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return path


def _storage_url_for(stored_filename: str) -> str:
    return f"/api/v1/documents/{stored_filename}/download"


@router.post("/{booking_id}/documents", response_model=BookingDocumentResponse)
async def upload_document(
    booking_id: uuid.UUID,
    type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    backend = (settings.DOCUMENT_STORAGE_BACKEND or "local").lower()
    if settings.is_production and backend == "local":
        raise HTTPException(
            status_code=503,
            detail=(
                "Local document storage is disabled in production. "
                "Set DOCUMENT_STORAGE_BACKEND=s3|r2 with bucket credentials (FIX-P34-02)."
            ),
        )
    if backend in ("s3", "r2") and not settings.DOCUMENT_S3_BUCKET:
        raise HTTPException(
            status_code=503,
            detail="DOCUMENT_S3_BUCKET is required for s3/r2 document storage.",
        )

    allowed = {
        m.strip().lower()
        for m in (settings.DOCUMENT_ALLOWED_MIME or "").split(",")
        if m.strip()
    }
    mime = (file.content_type or "application/octet-stream").lower()
    if allowed and mime not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"MIME type not allowed: {mime}",
        )

    stmt = (
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.quote))
    )
    booking = (await db.execute(stmt)).scalar_one_or_none()

    if (
        not booking
        or not booking.quote
        or booking.quote.organization_id != current_user.active_organization_id
    ):
        raise HTTPException(status_code=404, detail="Booking not found")

    original = _sanitize_original_filename(file.filename)
    stored_name = f"{booking_id}_{uuid.uuid4().hex}_{original}"

    # Read with size cap (FIX-P34-02 retention/size)
    max_bytes = int(settings.DOCUMENT_MAX_BYTES or 10 * 1024 * 1024)
    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds max size of {max_bytes} bytes",
        )

    if backend == "local":
        file_path = _resolve_upload_path(stored_name)
        with open(file_path, "wb") as buffer:
            buffer.write(data)
        storage_url = _storage_url_for(stored_name)
    else:
        # Object storage wiring: store key as storage_url; download still org-gated.
        # Full boto3 upload deferred until credentials exist — refuse silent fake success.
        raise HTTPException(
            status_code=501,
            detail=(
                "S3/R2 upload client not wired yet. Keep DOCUMENT_STORAGE_BACKEND=local "
                "for dev, or finish boto3/presign in a follow-up."
            ),
        )

    doc = BookingDocument(
        booking_id=booking_id,
        organization_id=current_user.active_organization_id,
        type=type,
        filename=original,
        storage_url=storage_url,
        mime_type=mime,
        uploaded_by_user_id=current_user.id,
    )

    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/{booking_id}/documents", response_model=List[BookingDocumentResponse])
async def list_documents(
    booking_id: uuid.UUID,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(BookingDocument).where(
        BookingDocument.booking_id == booking_id,
        BookingDocument.organization_id == current_user.active_organization_id,
    )
    return (await db.execute(stmt)).scalars().all()


@doc_router.get("/{filename}/download")
async def download_document(
    filename: str,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """
    FIX-P34-01: require auth + org ownership. Filename must match a stored doc.
    """
    _assert_safe_stored_filename(filename)
    expected_url = _storage_url_for(filename)

    doc = (
        await db.execute(
            select(BookingDocument).where(
                BookingDocument.storage_url == expected_url,
                BookingDocument.organization_id == current_user.active_organization_id,
            )
        )
    ).scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = _resolve_upload_path(filename)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=doc.filename,
        media_type=doc.mime_type or "application/octet-stream",
    )


@doc_router.get("/{doc_id}/share-link")
async def document_share_link(
    doc_id: uuid.UUID,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    """wa.me helper to re-share a ticket/voucher download link (FIX-P34-02)."""
    from urllib.parse import quote as url_quote

    from app.models.commercial import Quote

    doc = await db.get(BookingDocument, doc_id)
    if not doc or doc.organization_id != current_user.active_organization_id:
        raise HTTPException(status_code=404, detail="Document not found")

    booking = await db.get(Booking, doc.booking_id)
    phone = ""
    if booking:
        quote = (
            await db.execute(
                select(Quote)
                .where(Quote.id == booking.quote_id)
                .options(selectinload(Quote.customer))
            )
        ).scalar_one_or_none()
        if quote and quote.customer:
            phone = quote.customer.phone_e164 or ""

    digits = "".join(filter(str.isdigit, phone))
    frontend = (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")
    # Agents open authenticated download; share message points at booking docs UI
    link = f"{frontend}/app/bookings/{doc.booking_id}"
    text = f"Your travel document ({doc.filename}) is ready: {link}"
    wa = f"https://wa.me/{digits}?text={url_quote(text)}" if digits else None
    return {
        "status": "success",
        "document_id": str(doc.id),
        "download_path": doc.storage_url,
        "booking_url": link,
        "wa_link": wa,
    }


@doc_router.delete("/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(BookingDocument, doc_id)
    if not doc or doc.organization_id != current_user.active_organization_id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Best-effort delete of local file from storage_url
    if doc.storage_url:
        parts = doc.storage_url.rstrip("/").split("/")
        if len(parts) >= 2 and parts[-1] == "download":
            try:
                path = _resolve_upload_path(parts[-2])
                if path.is_file():
                    path.unlink()
            except HTTPException:
                pass

    await db.delete(doc)
    await db.commit()
    return {"status": "success"}
