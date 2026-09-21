"""
Auth smoke tests against the ASGI app (or a running API).

Requires:
- DB migrated
- Seeded platform admin (admin@tripos.in / password123) OR will create a temp user via signup+verify

Run from apps/api:
  poetry run python scripts/test_auth.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from httpx import AsyncClient, ASGITransport
from main import app
from app.core.security import create_access_token


BASE = "/api/v1"


async def run_tests():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # --- Bad password ---
        print("Testing bad password...")
        bad = await ac.post(
            f"{BASE}/auth/login",
            json={"email": "admin@tripos.in", "password": "wrong-password"},
        )
        assert bad.status_code == 401, f"Expected 401, got {bad.status_code}: {bad.text}"
        print("Bad password rejected.")

        # --- Signup ---
        email = "agent.sprint.a@example.com"
        print("Testing signup...")
        signup = await ac.post(
            f"{BASE}/auth/signup",
            json={
                "email": email,
                "password": "SecurePass123!",
                "first_name": "Sprint",
                "last_name": "Agent",
            },
        )
        # 200 on first run; 400 if already registered from a prior run
        assert signup.status_code in (200, 400), f"Signup failed: {signup.status_code} {signup.text}"
        print("Signup ok:", signup.status_code, signup.json())

        # Simulate email verify with JWT (same as email link)
        from sqlalchemy import select
        from app.db.session import AsyncSessionLocal
        from app.models import User

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            assert user is not None, "Signup user not found in DB"
            user_id = str(user.id)

        verify_token = create_access_token(data={"sub": user_id, "type": "verify"})
        print("Testing verify...")
        verify = await ac.post(f"{BASE}/auth/verify", json={"token": verify_token})
        assert verify.status_code == 200, f"Verify failed: {verify.status_code} {verify.text}"
        print("Verify ok.")

        # --- Login agent ---
        print("Testing agent login...")
        login = await ac.post(
            f"{BASE}/auth/login",
            json={"email": email, "password": "SecurePass123!"},
        )
        assert login.status_code == 200, f"Login failed: {login.status_code} {login.text}"
        agent_token = login.json()["access_token"]
        print("Agent login ok.")

        # --- /me ---
        print("Testing /me...")
        me = await ac.get(
            f"{BASE}/auth/me",
            headers={"Authorization": f"Bearer {agent_token}"},
        )
        assert me.status_code == 200, f"/me failed: {me.status_code} {me.text}"
        me_body = me.json()
        assert me_body["email"] == email
        assert me_body.get("is_platform_admin") is False
        assert me_body.get("org_role") == "admin"
        print("Me ok:", me_body)

        # --- Unauthorized ---
        print("Testing /me without token...")
        unauth = await ac.get(f"{BASE}/auth/me")
        assert unauth.status_code in (401, 403), f"Expected 401/403, got {unauth.status_code}"
        print("Unauthorized check ok.")

        # --- Platform admin login (seed) ---
        print("Testing platform admin login...")
        admin_login = await ac.post(
            f"{BASE}/auth/login",
            json={"email": "admin@tripos.in", "password": "password123"},
        )
        if admin_login.status_code == 200:
            admin_token = admin_login.json()["access_token"]
            admin_me = await ac.get(
                f"{BASE}/auth/me",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert admin_me.status_code == 200
            assert admin_me.json().get("is_platform_admin") is True
            print("Platform admin me ok.")
        else:
            print("SKIP platform admin login (seed not run):", admin_login.status_code)

        print("ALL AUTH TESTS PASSED!")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_tests())
