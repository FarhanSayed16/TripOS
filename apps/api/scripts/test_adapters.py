import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from app.schemas.inventory import SearchQuery, PassengerQuery, InventoryType
from app.adapters.registry import AdapterRegistry

async def run_tests():
    print("Testing AdapterRegistry...")
    
    # 1. Resolve mock adapter
    adapter = AdapterRegistry.get_adapter("mock_supplier")
    assert adapter.supplier_code == "mock_supplier", "Supplier code mismatch"
    print(f"Successfully resolved adapter: {adapter.__class__.__name__}")
    
    # 2. Test capabilities
    caps = adapter.capabilities
    assert caps.can_book is True
    assert caps.can_revalidate is True
    print("Capabilities check passed.")
    
    # 3. Test Flight Search
    print("\nTesting Flight Search...")
    flight_query = SearchQuery(
        type=InventoryType.FLIGHT,
        origin="DEL",
        destination="BOM",
        departure_date=date.today() + timedelta(days=7),
        passengers=PassengerQuery(adults=1)
    )
    
    flight_offers = await adapter.search(flight_query)
    assert len(flight_offers) == 4, f"Expected 4 flight offers, got {len(flight_offers)}"
    assert flight_offers[0].type == InventoryType.FLIGHT
    assert flight_offers[0].currency == "INR"
    print(f"Flight search passed. Found {len(flight_offers)} offers.")
    print(f"First offer: {flight_offers[0].title} - {flight_offers[0].total_amount} {flight_offers[0].currency}")

    # status / map_error contract
    pnr_probe = "MOCK-PNR-TEST"
    st = await adapter.status(pnr_probe)
    assert st["status"] == "confirmed"
    mapped = adapter.map_error(RuntimeError("x"))
    assert mapped.error_code == "supplier_error"
    
    # 4. Test Hotel Search
    print("\nTesting Hotel Search...")
    hotel_query = SearchQuery(
        type=InventoryType.HOTEL,
        origin="DEL",  # Origin ignored for hotels in our mock
        destination="GOI",
        departure_date=date.today() + timedelta(days=14),
        passengers=PassengerQuery(adults=2)
    )
    
    hotel_offers = await adapter.search(hotel_query)
    assert len(hotel_offers) == 2, f"Expected 2 hotel offers, got {len(hotel_offers)}"
    assert hotel_offers[0].type == InventoryType.HOTEL
    print(f"Hotel search passed. Found {len(hotel_offers)} offers.")
    print(f"First offer: {hotel_offers[0].title} - {hotel_offers[0].total_amount} {hotel_offers[0].currency}")
    
    # 5. Test Revalidate
    print("\nTesting Revalidate...")
    offer_to_revalidate = flight_offers[0]
    assert not offer_to_revalidate.is_revalidated
    revalidated_offer = await adapter.revalidate(offer_to_revalidate)
    assert revalidated_offer.is_revalidated is True
    print("Revalidate passed.")
    
    # 6. Test Book
    print("\nTesting Book...")
    passengers = [{"first_name": "Test", "last_name": "User"}]
    pnr = await adapter.book(revalidated_offer, passengers)
    assert pnr.startswith("MOCK-PNR-")
    print(f"Book passed. PNR: {pnr}")
    
    # 7. Test Cancel
    print("\nTesting Cancel...")
    cancel_status = await adapter.cancel(pnr)
    assert cancel_status is True
    print("Cancel passed.")
    
    print("\nAll Adapter tests passed successfully!")

if __name__ == "__main__":
    if sys.platform == "win32":
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_tests())
