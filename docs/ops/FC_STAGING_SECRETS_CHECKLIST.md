# FC Staging secrets checklist (Flight Commerce Phase 0–1)

**Purpose:** Names of secrets/env required for staging live spine.  
**Values:** password manager / Render dashboard — **never commit**.  
**Related:** `apps/api/.env.example`, `docs/phase-0/FC_CAPABILITY_MATRIX.md`

---

## Always (API + worker)

| Env | Needed for | Set? |
|---|---|---|
| `DATABASE_URL` | Postgres | |
| `JWT_SECRET` | Auth | |
| `ENCRYPTION_KEY` | Fernet (supplier secrets / docs) | |
| `REDIS_URL` | Shopping cache | |
| `FRONTEND_URL` / CORS | Web | |
| `ENV` | `production` on hosted | |

## Live inventory (FC Phase 1)

| Env | Needed for | Set? |
|---|---|---|
| `INVENTORY_SUPPLIERS` | e.g. `tbo` or `mock_supplier,tbo` | |
| `TBO_LIVE_ENABLED` | `true` for real HTTP | |
| `TBO_BASE_URL` | Supplier API base | |
| `TBO_CLIENT_ID` | Auth | |
| `TBO_USER_NAME` | Auth | |
| `TBO_PASSWORD` | Auth | |
| `TBO_END_USER_IP` | Often required by TBO | |
| `SEARCH_CACHE_ENABLED` | `true` on staging | |
| `SEARCH_CACHE_REFRESH_ENABLED` | Optional warm refresh | |
| `SEARCH_CACHE_TTL_SECONDS` | Default 120 | |

## Document vault

| Env | Needed for | Set? |
|---|---|---|
| `DOCUMENT_STORAGE_BACKEND` | `r2` or `s3` (not `local` in prod) | |
| `DOCUMENT_S3_BUCKET` | | |
| `DOCUMENT_S3_ENDPOINT` | | |
| `DOCUMENT_S3_ACCESS_KEY` | | |
| `DOCUMENT_S3_SECRET_KEY` | | |
| `DOCUMENT_S3_REGION` | Often `auto` | |

## Payments (pay → book smoke)

| Env | Needed for | Set? |
|---|---|---|
| `PAYMENTS_MODE` | `razorpay` or `mock` | |
| `RAZORPAY_KEY_ID` / `SECRET` | Live test | |
| `RAZORPAY_WEBHOOK_SECRET` | | |

## Observability

| Env | Needed for | Set? |
|---|---|---|
| `SENTRY_DSN` | Errors + L2B survival alerts | |

## Smoke after secrets

Follow `docs/ops/HOSTED_SMOKE.md` § FC Phase 1 live spine.
