import pytest
from datetime import datetime, timezone
from app.adapters.tbo_adapter import TboAdapter
from app.schemas.inventory import SearchQuery, InventoryType

@pytest.mark.asyncio
async def test_tbo_search():
    adapter = TboAdapter()
    query = SearchQuery(
        origin="DEL",
        destination="BOM",
        departure_date=datetime.strptime("2026-10-01", "%Y-%m-%d").date(),
        passengers={"adults": 1, "children": 0, "infants": 0},
        type=InventoryType.FLIGHT,
    )
    
    offers = await adapter.search(query)
    
    assert len(offers) == 2
    assert offers[0].supplier_code == "tbo"
    assert "TBO-RES-1" in offers[0].supplier_reference
    assert offers[0].title.startswith("[SIMULATED]")
    assert offers[0].total_amount == 5700.0
    assert offers[0].currency == "INR"

@pytest.mark.asyncio
async def test_tbo_revalidate_success():
    adapter = TboAdapter()
    query = SearchQuery(
        origin="DEL",
        destination="BOM",
        departure_date=datetime.strptime("2026-10-01", "%Y-%m-%d").date(),
        passengers={"adults": 1, "children": 0, "infants": 0},
        type=InventoryType.FLIGHT,
    )
    
    offers = await adapter.search(query)
    offer = offers[0]
    
    revalidated = await adapter.revalidate(offer)
    assert revalidated.total_amount == 5700.0

@pytest.mark.asyncio
async def test_tbo_book_success():
    adapter = TboAdapter()
    query = SearchQuery(
        origin="DEL",
        destination="BOM",
        departure_date=datetime.strptime("2026-10-01", "%Y-%m-%d").date(),
        passengers={"adults": 1, "children": 0, "infants": 0},
        type=InventoryType.FLIGHT,
    )
    
    offers = await adapter.search(query)
    offer = offers[0]
    
    pnr = await adapter.book(offer, [{"first_name": "Test", "last_name": "User"}])
    assert pnr.startswith("SIM-TBO")
