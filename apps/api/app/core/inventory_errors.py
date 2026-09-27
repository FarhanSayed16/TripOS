"""Inventory / adapter domain errors with stable error codes."""

from typing import Optional


class InventoryRevalidateError(Exception):
    """Raised when revalidate fails with a known commercial reason."""

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        previous_total_paise: Optional[int] = None,
        new_total_paise: Optional[int] = None,
    ):
        self.error_code = error_code  # fare_changed | sold_out | supplier_timeout | supplier_error
        self.message = message
        self.previous_total_paise = previous_total_paise
        self.new_total_paise = new_total_paise
        super().__init__(message)
