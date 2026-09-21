# Render Operational Runbook

This document describes how to deploy, rollback, and manage the TripOS Backend (API, Worker, DB) on Render.

## 1. Initial Deployment

1. Connect your GitHub/GitLab repository to Render.
2. Under the Render Dashboard, click **New +** and select **Blueprint**.
3. Select the repository. Render will automatically detect the `render.yaml` file at the root.
4. Render will provision:
   - `tripos-db` (Postgres 16)
   - `tripos-redis` (**unused by V1 app code** — reserved for future rate-limit/cache; jobs use Postgres outbox)
   - `tripos-api` (FastAPI)
   - `tripos-worker` (outbox worker)
5. **CRITICAL:** Set every `sync: false` secret on **both** `tripos-api` and `tripos-worker`:

| Variable | Notes |
|---|---|
| `JWT_SECRET` | Strong random; required when `ENV=production` |
| `ENCRYPTION_KEY` | Fernet key for future supplier credentials |
| `SENTRY_DSN` | Same project DSN on API + worker |
| `FRONTEND_URL` | Vercel production URL |
| `BACKEND_CORS_ORIGINS` | JSON list, e.g. `["https://app.vercel.app"]` |
| `RESEND_API_KEY` | Email (API only) |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` / `RAZORPAY_WEBHOOK_SECRET` | Mirror on worker |
| `PAYMENTS_MODE` | Blueprint default `mock`; set `razorpay` when going live |

Also see `docs/ops/HOSTED_SMOKE.md`.

## 2. Deploy & Database Migrations

Deployments are triggered automatically when you push to the connected branch (e.g., `main`).
- Migrations (`alembic upgrade head`) run as part of the `tripos-api` start command.
- If a deployment fails during start, traffic stays on the previous instance.

## 3. Rollback Procedure

1. Log in to the [Render Dashboard](https://dashboard.render.com/).
2. Select `tripos-api` or `tripos-worker`.
3. **Events** → previous successful deploy → **Rollback to this deploy**.
4. Schema rollbacks are **not** automatic — if needed, Render Shell: `alembic downgrade -1`.

## 4. Backups and Restore (Postgres)

Render performs daily logical backups on managed Postgres (Starter+). Retention ~7 days on Starter.

### Validate backups
1. `tripos-db` → **Backups** → confirm daily backups listed.

### Point-in-Time Recovery
1. `tripos-db` → **Settings** → Point-in-Time Recovery → choose timestamp.
2. Render creates a **new** DB instance (does not overwrite).
3. Point `DATABASE_URL` on API + worker to the new instance and restart.

Dry-run restore: schedule within 1 week of first hosted deploy (Phase 28 checklist).

Official docs: [Render Postgres backups](https://render.com/docs/databases#backups).

## 5. Health & Sentry

- `GET /health` — liveness
- `GET /ready` — DB connectivity (503 if down)
- Platform admin: `GET /api/v1/admin/sentry-debug` — intentional exception for Sentry smoke
