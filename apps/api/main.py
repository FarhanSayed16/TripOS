from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware
import sentry_sdk
import structlog

from app.core.config import settings
from app.core.exceptions import AppError, app_error_handler
from app.core.middleware import LoggingMiddleware
from app.core.locale_middleware import LocaleMiddleware
from app.db.session import engine
from app.api import health, auth, customers, organizations, inventory, quotes, public, webhooks, payments, bookings, admin, packages, wallet, followups, documents, ai, partner

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        environment="production" if settings.is_production else "development"
    )

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", message="TripOS API starting up")
    yield
    logger.info("shutdown", message="TripOS API shutting down")
    await engine.dispose()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(LocaleMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # Exception Handlers
    app.add_exception_handler(AppError, app_error_handler)

    # Routers
    app.include_router(health.router, tags=["health"])
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(customers.router, prefix="/api/v1")
    app.include_router(organizations.router, prefix="/api/v1")
    app.include_router(inventory.router, prefix="/api/v1")
    app.include_router(quotes.router, prefix="/api/v1")
    app.include_router(public.router, prefix="/api/v1")
    app.include_router(webhooks.router, prefix="/api/v1")
    app.include_router(payments.router, prefix="/api/v1")
    app.include_router(bookings.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(packages.router, prefix="/api/v1")
    app.include_router(wallet.router, prefix="/api/v1")
    app.include_router(followups.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(documents.doc_router, prefix="/api/v1")
    app.include_router(ai.router, prefix="/api/v1")
    app.include_router(partner.router, prefix="/api/v1")

    return app

app = create_app()
