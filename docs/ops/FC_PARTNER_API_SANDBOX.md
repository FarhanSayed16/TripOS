# FC Phase 8 — Partner API sandbox guide

**Base URL (local):** `http://localhost:8000/api/v1/partner`  
**Auth:** `X-API-Key: tp_test_<prefix>_<secret>` (or `Authorization: Bearer …`)  
**OpenAPI:** `/docs` → tag **partner**

**Required env:** `FC_PARTNER_API_ENABLED=true` (defaults **off** — opt-in).

## 1. Create a sandbox partner app

Platform admin:

```http
POST /api/v1/admin/partners
Authorization: Bearer <admin_jwt>
Content-Type: application/json

{
  "organization_id": "<active-org-uuid>",
  "name": "Sandbox B2C Brand",
  "env": "test",
  "webhook_url": "https://webhook.site/your-uuid"
}
```

Response includes **`api_key`** and **`webhook_secret` once**. Store them; rotate via `POST /admin/partners/{id}/rotate-key`.

## 2. Happy path (Postman)

1. `GET /partner/me` — confirm key works  
2. `POST /partner/search/flights` — body same as agent search (`type: flight`, origin/dest/date/pax)  
3. `POST /partner/customers` — `{ first_name, last_name, phone }`  
4. `POST /partner/quotes` — `{ customer_id, items: [{ search_request_id, offer, agent_markup }] }`  
5. `POST /partner/quotes/{id}/passengers` — pax list  
6. `POST /partner/quotes/{id}/ready`  
7. `POST /partner/quotes/{id}/pay-link` — returns gateway link + public quote URL  
8. Simulate payment (mock webhook / offline) → booking worker runs  
9. `GET /partner/quotes/{id}/booking` — PNR / status  
10. Webhooks: `booking.confirmed` | `booking.failed` | `booking.cancelled` | `refund.updated`  
    - Verify `X-TripOS-Signature` = HMAC-SHA256(body, webhook_secret)

## 3. Limits

- Per-app **rate_limit_per_minute** (default 60) — Redis-backed when Redis is up; in-memory fallback otherwise  
- Search/revalidate count toward the **org L2B** meters (`usage_source=partner_search`) — one abusive partner cannot silently burn platform L2B without org brakes  
- Optional **ip_allowlist** — uses `X-Forwarded-For` (first hop) when present, else direct client IP (trust your ingress)

## 4. Non-goals

See [`../architecture/FC_PARTNER_NON_GOALS.md`](../architecture/FC_PARTNER_NON_GOALS.md).

## 5. Postman

Import [`FC_PARTNER_API.postman_collection.json`](./FC_PARTNER_API.postman_collection.json).
