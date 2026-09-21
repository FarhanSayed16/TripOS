import asyncio
import uuid
import structlog
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.core.config import settings
from app.models import Base, UserRole, User, Organization, OrganizationMember, Supplier

logger = structlog.get_logger()

async def run_seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            logger.info("Database already seeded. Skipping.")
            return

        logger.info("Starting seed...")

        # Create Platform Root Org
        root_org = Organization(
            slug="tripos-platform",
            brand_name="TripOS HQ",
            status="active"
        )
        session.add(root_org)
        await session.flush()

        # Create Admin User
        # Default password: password123 — CHANGE before any shared/prod environment
        from app.core.security import get_password_hash
        admin_user = User(
            email="admin@tripos.in",
            hashed_password=get_password_hash("password123"),
            first_name="Platform",
            last_name="Admin",
            is_verified=True,
            is_platform_admin=True,
        )
        session.add(admin_user)
        await session.flush()

        # Create Membership
        member = OrganizationMember(
            user_id=admin_user.id,
            organization_id=root_org.id,
            role=UserRole.admin
        )
        session.add(member)

        # Create Mock Supplier
        mock_supplier = Supplier(
            code="mock_supplier",
            name="Mock Flight Supplier API",
            is_active=True
        )
        session.add(mock_supplier)

        await session.commit()
        logger.info("Seed completed successfully.")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_seed())
