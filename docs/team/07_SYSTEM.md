# TripOS — System Document (Hardware & Software)

**Document type:** System requirements & runtime environment  
**Prepared / researched by:** Farhan Sayed  
**Date:** 2026-10-05  

---

## 1. System overview

TripOS runs as three logical runtime pieces:

1. **Web** — Next.js UI  
2. **API** — FastAPI HTTP service  
3. **Worker** — Background booking/outbox processor  

Plus data services: **PostgreSQL** and **Redis**.

---

## 2. Software requirements

### 2.1 Developer workstation

| Software | Version / note |
|---|---|
| OS | Windows 10/11, macOS, or Linux |
| Docker Desktop / Engine | Required for Postgres + Redis via Compose |
| Python | **3.12+** |
| Node.js | **LTS 20+** |
| Git | Required |
| Optional | Postman (API review), Poetry/uv/venv for Python deps |

### 2.2 Local containers (`docker-compose.yml`)

| Service | Image | Host port | Container |
|---|---|---|---|
| PostgreSQL | `postgres:16-alpine` | **5433** | 5432 |
| Redis | `redis:7-alpine` | **6380** | 6379 |

Default DB: user/db `tripos`, password `password` (local only).

### 2.3 Application processes

| Process | Command (typical) | Port |
|---|---|---|
| API | `uvicorn … --port 8000` (from `apps/api`) | 8000 |
| Worker | `python worker.py` (from `apps/api`) | — |
| Web | `npm run dev` (from `apps/web`) | 3000 |

Worker V1 does **not** require Redis for outbox draining (Postgres locks). Redis is required for shopping cache / some rate-limit paths when enabled.

---

## 3. Hardware guidance

No formal cloud sizing document exists yet. Practical guidance:

### 3.1 Local development

| Resource | Minimum comfortable |
|---|---|
| CPU | 4 cores |
| RAM | 8 GB (16 GB recommended with Docker Desktop) |
| Disk | 10+ GB free for images, `node_modules`, venv, DB volume |

### 3.2 Staging / small pilot (target hosted)

| Component | Suggested starting point |
|---|---|
| API (Render Web) | 1 instance, ≥512 MB–1 GB RAM |
| Worker (Render Background) | 1 instance, same class as API |
| Postgres | Managed Postgres (Render/Neon/etc.) sized for pilot traffic |
| Redis | Managed Redis / Upstash when cache & rate limits needed |
| Web | Vercel hobby/pro project |

Scale up when L2B, concurrent searches, or document storage grow. Exact SKUs are ops decisions after hosted smoke.

---

## 4. Network & ports

| Port | Service |
|---|---|
| 3000 | Next.js |
| 8000 | FastAPI |
| 5433 | Postgres (local publish) |
| 6380 | Redis (local publish) |

Frontend → API: same-origin BFF proxy and/or `FRONTEND_URL` CORS configuration for hosted.

---

## 5. Environment configuration

Canonical template: `apps/api/.env.example`.

### 5.1 Must-set for local

- `DATABASE_URL` → `postgresql+psycopg://tripos:password@localhost:5433/tripos`  
- `REDIS_URL` → `redis://localhost:6380/0`  
- `JWT_SECRET` (non-placeholder)  
- `FRONTEND_URL=http://localhost:3000`  
- `PAYMENTS_MODE=mock`  
- `INVENTORY_SUPPLIERS=mock_supplier`  

### 5.2 Staging / production additions

- Strong `JWT_SECRET`, `ENCRYPTION_KEY`  
- `ENV=production` when hosted (cookie Secure / guards)  
- Razorpay live/test keys + webhook secret  
- `DOCUMENT_STORAGE_BACKEND=s3|r2` + bucket credentials (**not** local)  
- `SENTRY_DSN`  
- Optional: `TBO_LIVE_ENABLED=true` + TBO credentials  
- Optional: `FC_PARTNER_API_ENABLED=true`  
- `SEARCH_CACHE_ENABLED=true` for live browse  

Checklist: `docs/ops/FC_STAGING_SECRETS_CHECKLIST.md`.

---

## 6. Local bring-up procedure

```bash
# 1) Infra
docker compose up -d

# 2) API
cd apps/api
# activate venv, install deps
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --port 8000   # or project’s module path

# 3) Worker (second terminal)
python worker.py

# 4) Web
cd apps/web
npm install
npm run dev
```

Seed login: `admin@tripos.in` / `password123` — **change before shared environments**.

---

## 7. Hosted topology

**PlantUML:** [`diagrams/04_deployment.puml`](./diagrams/04_deployment.puml)

| Piece | Platform (planned/documented) |
|---|---|
| Web | Vercel (`docs/ops/VERCEL_RUNBOOK.md`) |
| API + Worker | Render (`docs/ops/RENDER_RUNBOOK.md`) |
| Smoke | `docs/ops/HOSTED_SMOKE.md` |

```text
Users → Vercel (web) → Render (API)
                     → Render (worker)
                     → Managed Postgres / Redis
Suppliers ← API adapters (TBO when live)
Payments  ← Razorpay webhooks → API
```

---

## 8. Dependencies outside TripOS code

| Dependency | Purpose | Required for |
|---|---|---|
| TBO Holidays API | Live flights | Live commerce |
| Razorpay | Collect payments | Live pay |
| Resend | Transactional email | Signup/reset in real env |
| OpenAI | AI copilot | Only if flag on |
| S3/R2 | Document vault | Production tickets/PDFs |
| Travclan Volt | — | **Not used** (parked) |

---

## 9. Backup & resilience

- DB backup/restore: `docs/ops/BACKUP_RESTORE.md`  
- Incident template: `docs/ops/INCIDENT_TEMPLATE.md`  
- L2B survival: soft-brakes before hard outage  

---

## 10. Security baseline (system)

- No secrets in git  
- Production JWT secret must not be placeholder  
- Webhook signatures required in production  
- Document storage must not be local in production  
- Partner API off until intentionally enabled  

---

*Prepared and researched by Farhan Sayed.*
