# Hosted deploy smoke (FIX-P27-01)

Complete after Render Blueprint + Vercel project exist. Record URLs in gitignored `secrets/04-hosting-accounts.md` (copy from `docs/phase-0/credential-pack-templates/04-hosting-accounts.md`).

## Sprint P status (2026-09-19)

| Item | Status |
|---|---|
| Blueprint `render.yaml` | Ready |
| Local E2E | Green ×2 — see `docs/e2e-runs.md` |
| Render / Vercel live URLs | **Not available in this workspace** |
| Automated runner | `apps/api/scripts/hosted_smoke.py` |

Until `TRIPOS_API_URL` is set, hosted smoke is **blocked on credentials/accounts** (not on product code).

```powershell
cd apps\api
$env:TRIPOS_API_URL="https://<api>.onrender.com"
$env:TRIPOS_WEB_URL="https://<web>.vercel.app"
.\.venv\Scripts\python.exe scripts\hosted_smoke.py
```

## Preflight

1. Render Blueprint from `render.yaml` → set all `sync: false` secrets on **api and worker**.
2. Vercel project root `apps/web` → set `NEXT_PUBLIC_API_URL`, optional `NEXT_PUBLIC_SENTRY_DSN`.
3. `BACKEND_CORS_ORIGINS` on API as JSON list, e.g. `["https://your-app.vercel.app"]`.
4. `FRONTEND_URL` = Vercel production URL.
5. `ENV=production`, strong `JWT_SECRET`, `ENCRYPTION_KEY` (Fernet).
6. `AI_COPILOT_ENABLED=false` unless intentionally enabling AI with `OPENAI_API_KEY`.

## Smoke checklist

| Step | Command / action | Pass? |
|---|---|---|
| API health | `GET https://<api>/health` → 200 | |
| API ready | `GET https://<api>/ready` → 200 + db connected | |
| Web health | Frontend home loads | |
| Login | Agent login against hosted API | |
| Mock pay loop | Search → quote → send → payment (mock) → webhook or offline pay → worker confirms | |
| Sentry | Platform admin `GET /api/v1/admin/sentry-debug` → event in Sentry | |
| Failures UI | `/admin/failures` loads | |

## Redis note

`tripos-redis` is in the Blueprint but **unused by V1 application code** (outbox is Postgres). Safe to leave on free plan; remove later if cost matters.

## After smoke

Fill `secrets/04-hosting-accounts.md` and tick Phase 27 exit in master plan + `phase-21-30-audit-fixes.md`. Then revisit `docs/v1-exit-decision.md` for possible GO V2.
