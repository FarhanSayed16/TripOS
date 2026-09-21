import asyncio
import httpx
import sys

API_URL = "http://127.0.0.1:8000/api/v1"

async def test_webhook(gateway_order_id: str):
    """
    Simulates a Razorpay webhook for a given gateway_order_id.
    """
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_fake_12345",
                    "order_id": gateway_order_id,
                    "status": "captured",
                    "amount": 100000,
                    "currency": "INR"
                }
            }
        }
    }

    async with httpx.AsyncClient() as client:
        print(f"Sending webhook for order {gateway_order_id}...")
        res = await client.post(f"{API_URL}/webhooks/razorpay", json=payload)
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_webhook.py <gateway_order_id>")
        sys.exit(1)
    
    order_id = sys.argv[1]
    asyncio.run(test_webhook(order_id))
