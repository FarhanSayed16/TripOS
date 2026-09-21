import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_search_rate_limit(api_client: AsyncClient):
    # Limit is 30 searches/min/org — sequential to avoid shared-session commit races in E2E.
    search_payload = {
        "type": "flight",
        "origin": "DEL",
        "destination": "BOM",
        "departure_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "passengers": {"adults": 1, "children": 0, "infants": 0},
    }

    status_codes: list[int] = []
    for _ in range(40):
        res = await api_client.post(
            "/api/v1/inventory/search/flights", json=search_payload
        )
        status_codes.append(res.status_code)

    assert 200 in status_codes
    assert 429 in status_codes
