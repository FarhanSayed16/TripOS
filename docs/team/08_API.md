# TripOS — API Document

**Document type:** API reference summary for the team  
**Prepared / researched by:** Farhan Sayed  
**Date:** 2026-10-05  

---

## 1. How to consume this API

| Item | Value |
|---|---|
| Local base | `http://localhost:8000` |
| Version prefix | `/api/v1` |
| Interactive docs | `http://localhost:8000/docs` (Swagger) |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |
| Postman pack | `docs/postman/TripOS_API_Handoff/` |
| Health (no prefix) | `GET /health`, `GET /ready` |

**For reviewers:** import the Postman folder, select **TripOS Local**, run **02 Happy Path Runner**.

---

## 2. Authentication models

| Audience | Mechanism |
|---|---|
| Agent / Admin user | `Authorization: Bearer <access_token>` from `POST /auth/login` |
| Refresh | HttpOnly cookie `refresh_token` → `POST /auth/refresh` |
| Partner apps | `X-API-Key: tp_…` (or Bearer with same key) — requires `FC_PARTNER_API_ENABLED=true` |
| Public customer | Path token on `/public/quotes/{token}` |
| Razorpay webhook | `X-Razorpay-Signature` (HMAC); unsigned allowed only local mock |

Seed (local): `admin@tripos.in` / `password123` (platform admin + org member).

---

## 3. API domains (summary)

### 3.1 Auth — `/api/v1/auth`
`POST /signup`, `/verify`, `/login`, `/refresh`, `/logout`, `/forgot-password`, `/reset-password`  
`GET|PATCH /me`

### 3.2 Organizations — `/api/v1/organizations`
`GET|PATCH /me`, members, pending/approve/reject (platform), domains + verify, white-label checklist, network, sub-agents

### 3.3 Customers — `/api/v1/customers`
CRUD + `GET /{id}/timeline`

### 3.4 Inventory — `/api/v1/inventory`
`POST /search/flights`, `/search/hotels`, `/revalidate`, `/fare-rules`, `/ancillaries`, `/seat-map`

**Flight search body (example):**
```json
{
  "type": "flight",
  "origin": "DEL",
  "destination": "BOM",
  "departure_date": "2026-11-15",
  "passengers": { "adults": 1, "children": 0, "infants": 0 }
}
```

### 3.5 Quotes — `/api/v1/quotes`
`POST /`, `GET /`, `GET /{id}`  
`PUT /{id}/passengers`  
`POST /{id}/ready`, `/send`, `/payment`, `/refresh`, `/mark-paid-offline`, `/cancel`  
`GET /{id}/whatsapp-preview`, `/fare-rules`, `/refunds`, `/audit`  
`PUT /{id}/items/{item_id}/extras`

**Create quote:** `customer_id` + `items[{ search_request_id, offer, agent_markup }]`  
`agent_markup` is **paise**.

### 3.6 Bookings — `/api/v1/bookings`
List/get/export CSV  
`POST /{id}/changes/quote`, `POST /changes/{change_id}/confirm`, `GET /{id}/changes`  
Documents nested under bookings / documents routes

### 3.7 Payments — `/api/v1/payments`
`GET /` (list). Create pay link lives on quotes: `POST /quotes/{id}/payment`.

### 3.8 Public — `/api/v1/public`
`GET /quotes/{token}`, `GET /theme/{domain}`

### 3.9 Webhooks — `/api/v1/webhooks`
`POST /razorpay`, `POST /schedule-change`

### 3.10 Wallet — `/api/v1/wallet`
`GET /summary`, `/ledger`, `/ledger/export`

### 3.11 Packages — `/api/v1/packages`
Create/list/get/patch/publish/delete, items, `POST /{id}/to-quote`

### 3.12 AI — `/api/v1/ai` (flag-gated)
`POST /parse-intent`, `/search-and-draft`

### 3.13 Followups & notifications
Followups: list, snooze, dismiss, send-reminder  
Notifications: list, unread-count, mark read / read-all

### 3.14 Admin — `/api/v1/admin` (platform admin)
Analytics, L2B (+ survival, orgs), organizations, bookings, payments, commissions (+ settle/statement/rules), suppliers (+ health/toggle), refunds, audit export, FX (+ seed), partners (+ rotate/usage), dead-letters

### 3.15 Partner — `/api/v1/partner` (API key)
`GET /me`  
`POST /search/flights|hotels`, `/revalidate`  
`POST /customers`  
Quotes: create, passengers, ready, pay-link, cancel, get, booking status  

Sandbox guide: `docs/ops/FC_PARTNER_API_SANDBOX.md`.

---

## 4. Recommended test sequence (Happy Path)

1. `POST /auth/login` → save `access_token`  
2. `POST /customers`  
3. `POST /inventory/search/flights` → save `search_request_id` + first `offer`  
4. `POST /quotes` with markup  
5. `PUT /quotes/{id}/passengers`  
6. `POST /quotes/{id}/ready`  
7. `POST /quotes/{id}/payment`  
8. `GET /public/quotes/{public_token}`  
9. `POST /quotes/{id}/mark-paid-offline` (demo)  
10. `GET /bookings` + `GET /wallet/summary`  

Ensure **worker** is running for booking confirm after pay.

---

## 5. Error & honesty conventions

- App errors use structured codes where implemented (`AppError`).  
- Inventory responses include `inventory_mode` for Live/Simulated/Mock.  
- Public quote responses **omit** supplier cost / markup.  
- Partner API is **opt-in** via env flag.  

---

## 6. Postman artifacts (handoff)

| File | Purpose |
|---|---|
| `02_TripOS_Happy_Path_Runner…` | Ordered Collection Runner |
| `01_TripOS_Core_Agent…` | Broad agent surface |
| `03_TripOS_Admin…` | Platform admin |
| `04_TripOS_Partner_API…` | Partner key flow |
| `05_TripOS_Public_Webhooks…` | Public + webhook stubs |
| `TripOS.env.local…` | Environment variables |

Path: `docs/postman/TripOS_API_Handoff/`.

---

## 7. Versioning & change control

- Current public API surface is **v1** under `/api/v1`.  
- Breaking changes should bump version or be gated by flags.  
- OpenAPI from a running server is the schema source of truth.  

---

*Prepared and researched by Farhan Sayed.*
