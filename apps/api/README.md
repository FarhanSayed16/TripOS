# TripOS API

FastAPI app + DB-polling outbox worker.

## Local

```bash
# From repo root or apps/api — use Poetry env if available
cd apps/api
cp .env.example .env   # edit DATABASE_URL, JWT_SECRET, etc.

alembic upgrade head
python scripts/seed.py

# Terminal 1 — API
uvicorn main:app --reload --port 8000

# Terminal 2 — Worker (required for booking_confirm after pay)
python worker.py
```

## Worker (Render)

Create a **Background Worker** service on Render with:

| Setting | Value |
|---|---|
| Root directory | `apps/api` |
| Start command | `python worker.py` |
| Env | Same `DATABASE_URL` (and secrets) as the API web service |

No Redis required for V1. Multiple workers are safe on Postgres via `FOR UPDATE SKIP LOCKED`.

Upgrade path later: Celery + Upstash if volume needs it.

## Payments

Default `PAYMENTS_MODE=mock`. See `docs/architecture/payments-v1-mock.md`.

## Tests

```bash
cd apps/api
pytest tests/ -q
```
