import pytest
import asyncio

@pytest.mark.asyncio
async def test_simple():
    print("Test started")
    await asyncio.sleep(1)
    print("Test ended")
