# TripOS — Technical Document

**Document type:** Technical specification  
**Prepared / researched by:** Farhan Sayed  
**Date:** 2026-10-05  

---

## 1. Stack overview

| Layer | Technology | Notes |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind | React 19.x; deploy target Vercel |
| Backend | FastAPI (Python 3.12+) | Modular monolith; deploy target Render |
| Database | PostgreSQL 16 | Async SQLAlchemy + Alembic |
| Cache / meters | Redis 7 | Shopping cache, rate limits, L2B helpers |
| Background jobs | DB outbox worker (`python worker.py`) | `FOR UPDATE SKIP LOCKED`; Celery later if needed |
| Payments | Razorpay (+ `PAYMENTS_MODE=mock`) | Webhooks + mark-paid-offline for demos |
| Email | Resend | Verify / reset |
| AI (optional) | OpenAI via feature flag | `AI_COPILOT_ENABLED=false` by default |
| Auth | JWT access + HttpOnly refresh cookie | Next.js BFF can proxy Bearer |
| Observability | Sentry (API / worker / web) | Optional DSN |

---

## 2. Engineering standards

- Python: `ruff` + `black`  
- Node: LTS 20+, ESLint / Prettier  
- Secrets never committed (see `secrets/README.md`, `.env.example`)  
- Commits: short, focused on **why**  

---

## 3. Key backend modules (`apps/api`)

| Path | Purpose |
|---|---|
| `app/api/` | HTTP routers (`/api/v1/...`) |
| `app/schemas/` | Pydantic request/response models |
| `app/models/` | SQLAlchemy ORM |
| `app/services/` | Business logic (quotes, payments, inventory, L2B, partner…) |
| `app/adapters/` | Supplier adapters (`mock_supplier`, `tbo`) |
| `app/core/` | Config, security, errors, middleware |
| `alembic/` | Migrations |
| `worker.py` | Booking confirm / outbox consumer |

---

## 4. Key frontend modules (`apps/web`)

| Area | Routes / notes |
|---|---|
| Agent shell | `(agent)/app/*` — Home, Search, Quotes, Bookings, Wallet, Settings, CRM, AI… |
| Public quote | `/q/[token]` — customer pay view (no agent economics) |
| Admin | `(admin)/admin/*` — L2B, partners, suppliers, FX, orgs… |
| Marketing | `(marketing)/` landing |
| Auth | `(auth)/login|signup|…` |
| Design system | Tokens in `globals.css` (Ink / Paper / Teal / Coral / Amber / Mint) |
| API client | RTK Query slices under `src/lib/api/` |

---

## 5. Inventory technical model

```text
SearchQuery → AdapterRegistry → SupplierStrategy (all | primary_only | failover)
           → NormalizedOffer[] (+ search_request_id)
Quote item snapshots offer → revalidate on pay / book
Worker: revalidate → book → PNR / ticket refs
```

| Supplier code | Modes | Flights | Hotels |
|---|---|---|---|
| `mock_supplier` | mock (default) | Yes | Yes |
| `tbo` | simulated **or** live HTTP | Yes | No (`[]`) |

Honesty field: `inventory_mode` = `live` | `simulated` | `mock`.

---

## 6. Money & FX technical rules

- Supplier / charge amounts stay on charge currency (typically INR).  
- Display FX writes only to the `money` envelope (`display_currency`, `display_amount`, `fx_rate`).  
- Agent markup in V1: **flat paise** (not % yet).  
- Platform fee: `PLATFORM_FEE_PAISE`.  

---

## 7. Security technical notes

| Topic | Implementation |
|---|---|
| Passwords | Argon2 (legacy bcrypt verify + rehash) |
| Access JWT | `Authorization: Bearer` |
| Refresh | Cookie `refresh_token`; rotation bumps `token_version` |
| Partner API | `X-API-Key` (`tp_…`); opt-in `FC_PARTNER_API_ENABLED` |
| Webhooks | Razorpay HMAC when secret set; unsigned only local mock |
| Documents | Local vault in dev; prod must be S3/R2 |

---

## 8. Feature flags & important env (summary)

See `apps/api/.env.example` for full list. Critical:

- `INVENTORY_SUPPLIERS` (default `mock_supplier`)  
- `TBO_LIVE_ENABLED` + `TBO_*` credentials  
- `PAYMENTS_MODE` = `mock` \| `razorpay`  
- `SEARCH_CACHE_ENABLED`, `L2B_WARN_RATIO`, `L2B_CRITICAL_RATIO`  
- `AI_COPILOT_ENABLED`  
- `FC_PARTNER_API_ENABLED`  
- `DOCUMENT_STORAGE_BACKEND`  

---

## 9. Testing & quality

- Pytest suite under `apps/api/tests/` (FC phases, L2B, auth, inventory honesty…)  
- Postman pack: `docs/postman/TripOS_API_Handoff/`  
- Live OpenAPI: `http://localhost:8000/docs`  

---

## 10. Deployment topology (target)

```text
Browser ──► Vercel (Next.js) ──BFF/proxy──► Render (FastAPI)
                                              │
                                         Postgres + Redis
                                              │
                                         Render Worker (worker.py)
```

---

*Prepared and researched by Farhan Sayed.*
