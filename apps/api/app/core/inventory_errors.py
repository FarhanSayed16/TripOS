"""Inventory / adapter domain errors with stable error codes."""


class InventoryRevalidateError(Exception):
    """Raised when revalidate fails with a known commercial reason."""

    def __init__(self, error_code: str, message: str):
        self.error_code = error_code  # fare_changed | sold_out | supplier_timeout | supplier_error
        self.message = message
        super().__init__(message)
