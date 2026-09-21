import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta
from httpx import AsyncClient

sys.path.append(str(Path(__file__).parent.parent))

BASE = "http://127.0.0.1:8000/api/v1"

async def run_tests():
    async with AsyncClient() as ac:
        print("--- Testing Quotes API ---")
        
        # 1. Login
        login = await ac.post(f"{BASE}/auth/login", json={"email": "admin@tripos.in", "password": "password123"})
        if login.status_code != 200:
            print(f"Login failed: {login.text}")
            return
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Search to get an offer
        print("\nSearching for an offer to quote...")
        search = await ac.post(f"{BASE}/inventory/search/flights", json={
            "type": "flight", "origin": "DEL", "destination": "BOM",
            "departure_date": (date.today() + timedelta(days=7)).isoformat(),
            "passengers": {"adults": 1, "children": 0, "infants": 0}
        }, headers=headers)
        search_id = search.json()["search_request_id"]
        offer = search.json()["offers"][0]
        
        # 3. Create a Customer
        print("\nCreating a test customer...")
        cust = await ac.post(f"{BASE}/customers", json={
            "first_name": "Quote", "last_name": "Test", "phone_e164": "+919876500000"
        }, headers=headers)
        if cust.status_code == 400 and "Phone number already exists" in cust.text:
            # Fetch existing
            custs = await ac.get(f"{BASE}/customers?search=Quote", headers=headers)
            cust_id = custs.json()["items"][0]["id"]
        else:
            cust_id = cust.json()["id"]

        # 4. Create Quote
        print("\nCreating Quote...")
        quote = await ac.post(f"{BASE}/quotes", json={
            "customer_id": cust_id,
            "items": [{
                "search_request_id": search_id,
                "offer": offer,
                "agent_markup": 50000 # 500 INR
            }]
        }, headers=headers)
        assert quote.status_code == 200, f"Quote creation failed: {quote.text}"
        q_data = quote.json()
        q_id = q_data["id"]
        pub_token = q_data["public_token"]
        print(f"Quote created. ID: {q_id} | Token: {pub_token}")
        
        # 5. Mark Ready (should fail Pax Gate)
        print("\nTesting Pax Gate...")
        ready_fail = await ac.post(f"{BASE}/quotes/{q_id}/ready", headers=headers)
        assert ready_fail.status_code == 400
        assert "Pax Gate" in ready_fail.text
        print("Pax Gate properly blocked transition.")
        
        # 6. Update Passengers
        print("\nUpdating Passengers...")
        pax_update = await ac.put(f"{BASE}/quotes/{q_id}/passengers", json=[
            {"first_name": "John", "last_name": "Doe", "date_of_birth": "1990-01-01"}
        ], headers=headers)
        assert pax_update.status_code == 200
        
        # 7. Mark Ready (should pass now)
        print("\nMarking Ready...")
        ready = await ac.post(f"{BASE}/quotes/{q_id}/ready", headers=headers)
        assert ready.status_code == 200
        assert ready.json()["status"] == "ready"
        print("Quote marked ready successfully.")
        
        # 8. Public Link (No auth)
        print("\nTesting Public Link...")
        public_link = await ac.get(f"{BASE}/public/quotes/{pub_token}")
        assert public_link.status_code == 200
        p_data = public_link.json()
        # Verify internal data is missing
        assert "customer_id" not in p_data
        assert "supplier_cost" not in p_data["items"][0]
        assert "customer_total" in p_data["items"][0]
        print("Public link returned sanitized data.")
        
        print("\nAll Quotes API tests passed successfully!")

if __name__ == "__main__":
    if sys.platform == "win32":
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_tests())
