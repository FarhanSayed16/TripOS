# TripOS API — Postman Handoff Pack

Single folder for reviewers to import into **Postman** and exercise the live TripOS API.

## Contents

| File | What it is |
|---|---|
| `TripOS.env.local.postman_environment.json` | Environment (`baseUrl`, tokens, IDs) |
| `02_TripOS_Happy_Path_Runner.postman_collection.json` | **Start here** — ordered demo story |
| `01_TripOS_Core_Agent.postman_collection.json` | Full agent API (auth → inventory → quotes → bookings → wallet…) |
| `03_TripOS_Admin.postman_collection.json` | Platform admin (L2B, suppliers, partners, FX…) |
| `04_TripOS_Partner_API.postman_collection.json` | B2C Partner API (`X-API-Key`) — FC Phase 8 |
| `05_TripOS_Public_Webhooks.postman_collection.json` | Public quote + webhook stubs |
| `_generate.py` | Regenerates collections (optional; for maintainers) |

OpenAPI (always up to date with the running server): `http://localhost:8000/docs` · `http://localhost:8000/openapi.json`

---

## Prerequisites (local)

1. **Infra**
   ```bash
   docker compose up -d
   ```
2. **API** (from `apps/api`, venv active)
   ```bash
   alembic upgrade head
   python scripts/seed.py
   uvicorn app.main:app --reload --port 8000
   ```
3. **Worker** (second terminal — needed after pay/book)
   ```bash
   python worker.py
   ```
4. **Recommended env for demos**
   - `PAYMENTS_MODE=mock`
   - `INVENTORY_SUPPLIERS=mock_supplier`
   - Partner tests: `FC_PARTNER_API_ENABLED=true`

### Seed credentials

| Role | Email | Password |
|---|---|---|
| Platform admin (+ org member) | `admin@tripos.in` | `password123` |

Change before any shared/staging environment.

---

## Import into Postman (for your sir)

1. Open **Postman** → **Import** → select this entire folder (or the JSON files).
2. Import / activate environment **TripOS Local**.
3. Confirm variables:
   - `baseUrl` = `http://localhost:8000`
   - `apiBase` = `http://localhost:8000/api/v1`
   - `agentEmail` / `agentPassword` = seed values above
4. Open collection **02 TripOS Happy Path Runner**.
5. Click **Run** (Collection Runner) → run **in folder order**.
6. Green checks = happy path OK. Failed step = expand Tests / response body.

Tokens and IDs (`accessToken`, `customerId`, `quoteId`, `publicToken`, …) are written automatically by Test scripts into the **environment**.

---

## Suggested review order

1. **Happy Path Runner** — login → customer → flight search → quote → ready → pay link → public quote → mark paid offline → bookings/wallet  
2. **Core Agent** — spot-check any extra endpoints  
3. **Admin** — analytics / L2B / suppliers / create partner key  
4. **Partner** — set `partnerApiKey` from Admin → create partner response (shown once)  
5. **Public & Webhooks** — public quote with `publicToken` from Happy Path  

---

## Auth cheat sheet

| Surface | Auth |
|---|---|
| Agent / most `/api/v1/*` | `Authorization: Bearer {{accessToken}}` |
| Admin `/api/v1/admin/*` | `Authorization: Bearer {{adminAccessToken}}` (same seed user works) |
| Partner `/api/v1/partner/*` | `X-API-Key: {{partnerApiKey}}` |
| Public quote | Path token `{{publicToken}}` (no JWT) |
| Health | None |

Login returns `access_token` in JSON. Refresh uses an HttpOnly cookie (browser/app); Postman demos use the Bearer access token from login.

---

## Notes / honesty

- Default inventory is **mock** (`mock_supplier`). Live TBO needs credentials + `TBO_LIVE_ENABLED=true`.
- Prefer **mark-paid-offline** for demos over crafting Razorpay webhook payloads.
- After mark-paid / webhook, **worker must be running** for booking confirm.
- Partner collection needs `FC_PARTNER_API_ENABLED=true` and a key from `POST /admin/partners`.
- Regenerating collections: `python _generate.py` (keeps Partner file as copied).

---

## Handoff checklist

- [ ] Docker Postgres + Redis up  
- [ ] Migrations + seed run  
- [ ] API on `:8000`  
- [ ] Worker running  
- [ ] Postman: environment **TripOS Local** selected  
- [ ] Happy Path Runner all green  
