"""Booking document upload / download (FIX-P34-01 + Phase 6 vault)."""
from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, require_active_org
from app.core.config import settings
from app.models.commercial import Booking, BookingDocument
from app.models.tenancy import User
from app.schemas.documents import BookingDocumentResponse
from app.services import document_storage as vault

router = APIRouter(prefix="/bookings", tags=["documents"])
doc_router = APIRouter(prefix="/documents", tags=["documents"])

# Disk/object key filenames we create: {booking_id}_{hex}_{sanitized_original}
_SAFE_STORED_NAME = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_[0-9a-f]+_.+$",
    re.IGNORECASE,
)


def _sanitize_original_filename(name: str | None) -> str:
    base = Path(name or "file").name
    base = base.replace("..", "").replace("/", "").replace("\\", "").strip()
    return base[:180] or "file"


def _assert_safe_stored_filename(filename: str) -> None:
    """Reject path traversal and unexpected shapes before touching storage."""
    if not filename or filename != Path(filename).name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not _SAFE_STORED_NAME.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")


@router.post("/{booking_id}/documents", response_model=BookingDocumentResponse)
async def upload_document(
    booking_id: uuid.UUID,
    type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_active_org),
    db: AsyncSession = Depends(get_db),
):
    backend = vault.backend_name()
    if settings.is_production and backend == "local":
        raise HTTPException(
            status_code=503,
            detail=(
                "Local document storage is disabled in production. "
                "Set DOCUMENT_STORAGE_BACKEND=s3|r2 with bucket credentials (FIX-P34-02)."
            ),
        )
    if vault.is_object_backend():
        if not settings.DOCUMENT_S3_BUCKET:
            raise HTTPException(
                status_code=503,
                detail="DOCUMENT_S3_BUCKET is required for s3/r2 document storage.",
            )
        if not settings.DOCUMENT_S3_ACCESS_KEY or not settings.DOCUMENT_S3_SECRET_KEY:
            raise HTTPException(
                status_code=503,
                detail=(
                    "DOCUMENT_S3_ACCESS_KEY and DOCUMENT_S3_SECRET_KEY are required "
                    "for s3/r2 document storage."
                ),
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

    max_bytes = int(settings.DOCUMENT_MAX_BYTES or 10 * 1024 * 1024)
    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds max size of {max_bytes} bytes",
        )

    try:
        storage_url = vault.put_bytes(stored_name, data, mime)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Document storage upload failed: {e}",
        ) from e

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
    redirect: bool = False,
):
    """
    FIX-P34-01: require auth + org ownership.
    Phase 6: local FileResponse, or stream/presign from S3/R2.
    """
    _assert_safe_stored_filename(filename)
    expected_url = vault.api_download_path(filename)

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

    # Optional: after org auth, redirect to short-lived presigned URL (s3/r2 only)
    if redirect and vault.is_object_backend():
        url = vault.presigned_get_url(filename, expires_seconds=900)
        if url:
            return RedirectResponse(url=url, status_code=302)

    if vault.backend_name() == "local":
        try:
            file_path = vault.local_path_for(filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(
            path=file_path,
            filename=doc.filename,
            media_type=doc.mime_type or "application/octet-stream",
        )

    # Object backends: stream through API (keeps auth; no FE change required)
    try:
        data = vault.get_bytes(filename)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if data is None:
        raise HTTPException(status_code=404, detail="File not found")

    headers = {
        "Content-Disposition": f'attachment; filename="{doc.filename}"',
    }
    return Response(
        content=data,
        media_type=doc.mime_type or "application/octet-stream",
        headers=headers,
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

    stored = vault.filename_from_storage_url(doc.storage_url)
    if stored:
        try:
            _assert_safe_stored_filename(stored)
            vault.delete_object(stored)
        except HTTPException:
            pass

    await db.delete(doc)
    await db.commit()
    return {"status": "success"}
