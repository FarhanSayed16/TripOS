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
    # Set INVENTORY_SUPPLIERS=tbo with TBO_LIVE_ENABLED=true for FC Phase 1 live spine.
    INVENTORY_SUPPLIERS: str = "mock_supplier"
    SUPPLIER_STRATEGY: str = "all"  # all | primary_only | failover

    # FC Phase 1 — TBO live HTTP (off by default; simulated adapter when false/missing creds)
    TBO_LIVE_ENABLED: bool = False
    TBO_BASE_URL: Optional[str] = None
    TBO_CLIENT_ID: Optional[str] = None
    TBO_USER_NAME: Optional[str] = None
    TBO_PASSWORD: Optional[str] = None
    TBO_END_USER_IP: str = "127.0.0.1"
    TBO_HTTP_TIMEOUT_SECONDS: float = 60.0
    TBO_AUTO_TICKET: bool = True  # call Ticket after Book when live
    # Overridable Rest paths (Sahil adjusts if supplier version differs)
    TBO_AUTH_PATH: str = "/SharedData.svc/rest/Authenticate"
    TBO_SEARCH_PATH: str = "/BookingEngineService_Air/AirService.svc/rest/Search"
    TBO_FARE_QUOTE_PATH: str = "/BookingEngineService_Air/AirService.svc/rest/FareQuote"
    TBO_BOOK_PATH: str = "/BookingEngineService_Air/AirService.svc/rest/Book"
    TBO_TICKET_PATH: str = "/BookingEngineService_Air/AirService.svc/rest/Ticket"
    TBO_CANCEL_PATH: str = "/BookingEngineService_Air/AirService.svc/rest/ReleasePNR"
    TBO_BOOKING_DETAILS_PATH: str = (
        "/BookingEngineService_Air/AirService.svc/rest/GetBookingDetails"
    )

    # Look-to-book thresholds (provisional Phase 0 defaults until Sahil overrides)
    L2B_WARN_RATIO: float = 80.0
    L2B_CRITICAL_RATIO: float = 120.0
    # Phase 4 — per-org brakes
    L2B_THROTTLE_MIN_CONFIRMED: int = 1  # critical + confirmed < this → 429
    L2B_ORG_CACHE_ONLY: bool = False  # warn/critical → cache hits only (no live miss fill)
    L2B_AI_BLOCK_ON_CRITICAL: bool = True  # AI cannot fire live when org L2B critical
    # Phase 7 — platform survival soft-brakes when global L2B is critical
    L2B_SURVIVAL_ENABLED: bool = True
    L2B_SURVIVAL_TTL_MULTIPLIER: float = 2.0
    L2B_SURVIVAL_TTL_CAP_SECONDS: int = 900  # 15 min
    L2B_SURVIVAL_PAUSE_WARM_REFRESH: bool = True
    # Phase 2 shopping cache — off by default; enable in staging with Redis up
    SEARCH_CACHE_ENABLED: bool = False
    SEARCH_CACHE_TTL_SECONDS: int = 120
    # Phase 5 — background refresh + TTL bands
    SEARCH_CACHE_REFRESH_ENABLED: bool = False
    SEARCH_CACHE_REFRESH_INTERVAL_SECONDS: int = 60
    SEARCH_CACHE_HOT_TTL_SECONDS: int = 90
    SEARCH_CACHE_WARM_TTL_SECONDS: int = 600
    SEARCH_CACHE_TOP_N: int = 50
    SEARCH_CACHE_HOT_TOP_N: int = 10  # first N of top list use hot TTL

    # Quote validity (Phase 3 — configurable; tighten for live later)
    QUOTE_FLIGHT_TTL_HOURS: int = 4
    QUOTE_HOTEL_TTL_HOURS: int = 12

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

    # FC Phase 4 — display FX (charge/settle currency for Razorpay stays INR until multi-currency pay approved)
    CHARGE_CURRENCY: str = "INR"
    FX_PROVIDER_ENABLED: bool = False  # optional scheduled pull; manual rates are default

    # FC Phase 5 — i18n
    DEFAULT_LOCALE: str = "en"
    SUPPORTED_LOCALES: str = "en,hi"

    # FC Phase 6 — rich offers (mock on; live adapters opt-in via capabilities)
    FC_ANCILLARIES_ENABLED: bool = True
    FC_SEAT_MAP_ENABLED: bool = True

    # FC Phase 7 — servicing / richer content (gated until Phase 0 matrix says yes)
    FC_REISSUE_ENABLED: bool = True  # mock reissue path; live needs supplier yes
    FC_NDC_ENABLED: bool = False  # Phase 0 gate — off until contracted
    FC_LCC_ENABLED: bool = False  # Phase 0 gate — off until contracted
    FC_AI_PREFERENCES_ENABLED: bool = True  # opt-in org.ai_preferences on AI search
    FC_SCHEDULE_CHANGE_WEBHOOK_SECRET: Optional[str] = None

    # FC Phase 8 — partner / B2C-facing API
    FC_PARTNER_API_ENABLED: bool = True
    FC_PARTNER_DEFAULT_RATE_LIMIT: int = 60
    FC_PARTNER_WEBHOOK_TIMEOUT_SECONDS: float = 5.0

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
