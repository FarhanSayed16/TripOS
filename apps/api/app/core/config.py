from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List, Self, Optional


_PLACEHOLDER_JWT = "generate_a_strong_secret_key_here"


class Settings(BaseSettings):
    # Base
    PROJECT_NAME: str = "TripOS API"
    ENV: str = "development"  # development | production

    # Database
    DATABASE_URL: str = "postgresql+psycopg://tripos:password@localhost:5433/tripos"
    REDIS_URL: str = "redis://localhost:6380/0"

    # Security
    JWT_SECRET: str = _PLACEHOLDER_JWT
    JWT_ALGORITHM: str = "HS256"
    MOCK_SUPPLIER_LATENCY_MS: int = 1500
    MOCK_SUPPLIER_FAIL_RATE: float = 0.05
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Phase 35: AI Copilot
    AI_COPILOT_ENABLED: bool = False  # FIX-P35-01: opt-in only
    OPENAI_API_KEY: Optional[str] = None
    AI_MODEL: str = "gpt-4o-mini"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Services
    RESEND_API_KEY: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    # mock = deterministic links; razorpay = live Payment Links when keys set
    PAYMENTS_MODE: str = "mock"
    FRONTEND_URL: str = "http://localhost:3000"
    # Pilot default ₹0 — Nilesh may override via env (AUDIT-009 / Sprint I)
    PLATFORM_FEE_PAISE: int = 0

    # Inventory suppliers (comma-separated). Default mock-only for pilot honesty (Sprint L).
    # Set INVENTORY_SUPPLIERS=mock_supplier,tbo to include simulated TBO offers.
    INVENTORY_SUPPLIERS: str = "mock_supplier"
    SUPPLIER_STRATEGY: str = "all"  # all | primary_only | failover

    # Hierarchy: master override share of sub-agent commission (basis points). Default 2000 = 20%.
    MASTER_COMMISSION_OVERRIDE_BPS: int = 2000

    # Document vault (FIX-P34-02). local = uploads/; s3/r2 requires bucket + credentials.
    DOCUMENT_STORAGE_BACKEND: str = "local"  # local | s3 | r2
    DOCUMENT_S3_BUCKET: Optional[str] = None
    DOCUMENT_S3_ENDPOINT: Optional[str] = None  # R2/S3-compatible endpoint
    DOCUMENT_S3_ACCESS_KEY: Optional[str] = None
    DOCUMENT_S3_SECRET_KEY: Optional[str] = None
    DOCUMENT_S3_REGION: str = "auto"
    DOCUMENT_MAX_BYTES: int = 10 * 1024 * 1024
    DOCUMENT_ALLOWED_MIME: str = "application/pdf,image/jpeg,image/png,image/webp"

    # Sentry Configuration
    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1 # Reduced from 1.0 for production

    # Worker Tuning
    WORKER_POLL_INTERVAL_SECONDS: int = 5

    # Encryption
    ENCRYPTION_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def inventory_supplier_codes(self) -> List[str]:
        codes = [c.strip() for c in self.INVENTORY_SUPPLIERS.split(",") if c.strip()]
        return codes or ["mock_supplier"]

    @property
    def cookie_secure(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @model_validator(mode="after")
    def reject_placeholder_jwt_in_production(self) -> Self:
        if self.is_production and self.JWT_SECRET in ("", _PLACEHOLDER_JWT):
            raise ValueError(
                "JWT_SECRET must be set to a strong secret when ENV=production"
            )
        return self


settings = Settings()
