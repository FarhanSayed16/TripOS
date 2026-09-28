"""Normalized booking result from adapters (FC Phase 1)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BookResult(BaseModel):
    """
    Richer than a bare PNR string so we can persist ticket numbers,
    supplier booking ids, and optional ticket document URLs for vault upload.
    """

    pnr: str
    supplier_booking_id: Optional[str] = None
    ticket_numbers: List[str] = Field(default_factory=list)
    ticket_document_url: Optional[str] = None
    raw: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_pnr(cls, pnr: str, **kwargs: Any) -> "BookResult":
        return cls(pnr=pnr, **kwargs)
