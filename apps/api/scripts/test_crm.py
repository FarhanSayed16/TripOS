import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from httpx import AsyncClient, ASGITransport
from main import app

async def run_tests():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("1. Authenticating as admin...")
        response = await ac.post("/auth/login", json={
            "email": "admin@tripos.in",
            "password": "password123"
        })
        assert response.status_code == 200, f"Failed to login: {response.text}"
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print("2. Creating customer with valid phone...")
        response = await ac.post("/api/v1/customers", json={
            "first_name": "Test",
            "last_name": "User",
            "phone": "9876543210" # Will be normalized to +919876543210
        }, headers=headers)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        customer = response.json()
        assert customer["phone_e164"] == "+919876543210"
        print(f"Customer created successfully! E164: {customer['phone_e164']}")

        print("3. Testing duplicate phone...")
        response = await ac.post("/api/v1/customers", json={
            "first_name": "Another",
            "last_name": "Duplicate",
            "phone": "+919876543210"
        }, headers=headers)
        assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
        assert response.json()["error_code"] == "DUPLICATE_PHONE"
        print("Duplicate blocked successfully!")

        print("4. Listing customers...")
        response = await ac.get("/api/v1/customers", headers=headers)
        assert response.status_code == 200
        customers = response.json()["items"]
        assert len(customers) > 0
        print(f"List successful! Found {len(customers)} customers.")

        print("ALL CRM TESTS PASSED!")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_tests())
