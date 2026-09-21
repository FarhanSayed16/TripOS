import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta
from httpx import AsyncClient

sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings

BASE = "http://127.0.0.1:8000/api/v1"

async def run_tests():
    async with AsyncClient() as ac:
        print("--- Testing Inventory API ---")
        
        # 1. Login to get token
        login = await ac.post(
            f"{BASE}/auth/login",
            json={"email": "admin@tripos.in", "password": "password123"},
        )
        if login.status_code != 200:
            print(f"Login failed: {login.text}. Ensure DB is seeded and server is running.")
            return
            
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Test Flight Search
        print("\nTesting /inventory/search/flights...")
        flight_payload = {
            "type": "flight",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": (date.today() + timedelta(days=7)).isoformat(),
            "passengers": {"adults": 1, "children": 0, "infants": 0}
        }
        
        flight_res = await ac.post(
            f"{BASE}/inventory/search/flights",
            json=flight_payload,
            headers=headers
        )
        assert flight_res.status_code == 200, f"Flight search failed: {flight_res.text}"
        flight_data = flight_res.json()
        assert flight_data["results_count"] == 2
        print(f"Flight search passed. Found {flight_data['results_count']} offers.")
        
        # Save first offer for revalidation
        first_offer = flight_data["offers"][0]
        
        # 3. Test Hotel Search
        print("\nTesting /inventory/search/hotels...")
        hotel_payload = {
            "type": "hotel",
            "origin": "DEL",
            "destination": "GOI",
            "departure_date": (date.today() + timedelta(days=14)).isoformat(),
            "passengers": {"adults": 2, "children": 0, "infants": 0}
        }
        
        hotel_res = await ac.post(
            f"{BASE}/inventory/search/hotels",
            json=hotel_payload,
            headers=headers
        )
        assert hotel_res.status_code == 200, f"Hotel search failed: {hotel_res.text}"
        hotel_data = hotel_res.json()
        assert hotel_data["results_count"] == 1
        print(f"Hotel search passed. Found {hotel_data['results_count']} offers.")
        
        # 4. Test Revalidate
        print("\nTesting /inventory/revalidate...")
        revalidate_payload = {
            "offer": first_offer
        }
        
        rev_res = await ac.post(
            f"{BASE}/inventory/revalidate",
            json=revalidate_payload,
            headers=headers
        )
        assert rev_res.status_code == 200, f"Revalidate failed: {rev_res.text}"
        rev_data = rev_res.json()
        assert rev_data["is_revalidated"] is True
        print("Revalidate passed.")
        
        # 5. Test Rate Limiter (send 30 more requests to hit limit)
        print("\nTesting Rate Limiter (this may take a moment to fire 30 reqs)...")
        tasks = []
        for _ in range(30):
            tasks.append(ac.post(f"{BASE}/inventory/search/flights", json=flight_payload, headers=headers))
            
        responses = await asyncio.gather(*tasks)
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited is True, "Rate limit was not enforced!"
        print("Rate limit passed (received expected 429).")
        
        print("\nAll Inventory API tests passed successfully!")

if __name__ == "__main__":
    if sys.platform == "win32":
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_tests())
