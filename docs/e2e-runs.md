# E2E tests (Sprint L / Sprint P)

## Prerequisites

- Postgres reachable via `DATABASE_URL` in `apps/api/.env` (default port **5433**)
- Docker Desktop running, then from repo root: `docker compose up -d`
- Schema migrated: `cd apps/api && alembic upgrade head`
- `mock_supplier` row present (seed or E2E auto-creates it)
- `PAYMENTS_MODE=mock`
- `INVENTORY_SUPPLIERS=mock_supplier` (default)

If Postgres is down, E2E fixtures **skip** (not fail) with `Postgres unavailable for E2E`.

**Windows note:** E2E conftest sets `WindowsSelectorEventLoopPolicy` so psycopg async works.

## Run

From `apps/api`:

```bash
# Unit gates (no DB)
python -m pytest tests/test_sprint_l.py tests/test_tbo_adapter.py -q

# Full E2E against local Postgres
python -m pytest tests/e2e/ -q --tb=short
```

Windows (venv):

```powershell
cd apps\api
$env:PYTHONPATH=(Get-Location).Path
.\.venv\Scripts\python.exe -m pytest tests/e2e/ -q --tb=short
```

Run **twice** on the same tree and paste results into the table below.

## Coverage (aligned routes)

| Scenario | File |
|---|---|
| Search → quote → send → payment → webhook → `poll_outbox` → confirmed | `test_e2e_happy_path.py` |
| Pax gate / expiry / tenant cancel IDOR | `test_e2e_validation_gates.py` |
| Fare-change at pay + after offline pay; supplier timeout | `test_e2e_revalidate_failures.py` |
| Duplicate / late webhook idempotency | `test_e2e_webhook_resilience.py` |
| Search rate limit 429 | `test_e2e_rate_limiting.py` |

## Recorded green runs

| # | Date | SHA / note | Command | Result |
|---|---|---|---|---|
| 1 | 2026-09-19 | Sprint P (local Docker Postgres; workspace not a git repo) | `pytest tests/e2e/ -q` | **15 passed** (~8.2s) |
| 2 | 2026-09-19 | Same tree, back-to-back | `pytest tests/e2e/ -q` | **15 passed** (~8.2s) |

### Sprint P fixes that unblocked greens

- E2E used `psycopg` (not missing `asyncpg`); Windows SelectorEventLoop
- Valid IN mobile phones in helpers; skip MOCK sold-out / fare-chg / timeout offers for happy path
- Quote responses eagerly load `booking` (async MissingGreenlet)
- `jobs_outbox.status` mapped to PG enum `jobstatus`
- Confirm job preserves `InventoryRevalidateError` for commercial failures (no false retry)
- Composite index migration: `jobs_outbox` (not `job_outbox`)
- `SupplierStrategy` / admin use `AdapterRegistry`; `paginate()` helper for packages/wallet
