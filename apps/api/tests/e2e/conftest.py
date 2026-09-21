import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, select
from sqlalchemy.pool import NullPool

import sys
import asyncio
import selectors

# psycopg async requires SelectorEventLoop on Windows (not Proactor).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from main import app
from app.db.session import get_db
from app.core.config import settings
from app.models.tenancy import User, Organization, OrganizationMember
from app.models.enums import OrgStatus, UserRole
from app.models.inventory import Supplier

# For E2E tests, we will create a dedicated test database or use a transaction rollback mechanism.
# Since we might rely on background workers which use their own sessions, we will use a separate test db.
# Wait, for simplicity in sandbox hardening, we'll just insert test data and clean it up.

TEST_DB_URL = settings.DATABASE_URL + "_test" # Assuming a _test DB exists or we just use the dev db
# Let's just use the dev db for sandbox hardening but isolate via unique UUIDs.

@pytest_asyncio.fixture
async def db_engine():
    print("Setting up db_engine")
    # Use the same driver as the app (psycopg). Do NOT rewrite to asyncpg —
    # asyncpg is not in pyproject.toml and breaks E2E when Postgres is up.
    engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        await engine.dispose()
        pytest.skip(f"Postgres unavailable for E2E ({e})")
    yield engine
    print("Tearing down db_engine")
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session_maker(db_engine):
    print("Setting up db_session_maker")
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture
async def db(db_session_maker):
    print("Setting up db session")
    async with db_session_maker() as session:
        yield session
    print("Tearing down db session")

@pytest_asyncio.fixture
async def test_org_and_user(db: AsyncSession):
    print("Setting up test_org_and_user")
    # Create isolated test org and user
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    org = Organization(
        id=org_id,
        slug=f"e2e-{org_id}",
        brand_name=f"E2E Test Org {org_id}",
        status=OrgStatus.active
    )
    user = User(
        id=user_id,
        email=f"test_{user_id}@example.com",
        hashed_password="fakehash",
        first_name="Test",
        last_name="User",
        is_verified=True,
    )
    member = OrganizationMember(
        organization_id=org_id,
        user_id=user_id,
        role=UserRole.admin,
    )
    
    db.add(org)
    db.add(user)
    db.add(member)
    await db.commit()
    
    yield {"org": org, "user": user}

    # Best-effort cleanup (E2E creates related rows; FK order varies by scenario)
    for sql in (
        f"DELETE FROM audit_events WHERE actor_user_id = '{user_id}'",
        f"DELETE FROM search_requests WHERE user_id = '{user_id}' OR organization_id = '{org_id}'",
        f"DELETE FROM organization_members WHERE user_id = '{user_id}'",
        f"DELETE FROM users WHERE id = '{user_id}'",
        f"DELETE FROM organizations WHERE id = '{org_id}'",
    ):
        try:
            await db.execute(text(sql))
            await db.commit()
        except Exception:
            await db.rollback()

@pytest_asyncio.fixture
async def ensure_mock_supplier(db: AsyncSession):
    """Quote creation requires a Supplier row for offer.supplier_code."""
    existing = (
        await db.execute(select(Supplier).where(Supplier.code == "mock_supplier"))
    ).scalar_one_or_none()
    if not existing:
        db.add(Supplier(code="mock_supplier", name="Mock Flight Supplier API", is_active=True))
        await db.commit()
    yield


@pytest_asyncio.fixture
async def api_client(test_org_and_user, db: AsyncSession, ensure_mock_supplier):
    # Create an API client authenticated as the test user
    from app.api.deps import get_current_user
    from app.db.session import get_db
    
    user = test_org_and_user["user"]
    user.active_organization_id = test_org_and_user["org"].id
    
    async def override_get_current_user():
        return user
        
    async def override_get_db():
        yield db
        
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()
