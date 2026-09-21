# Phase 4 — Schema decisions (Sprint C)

**Date:** 2026-09-16  
**Status:** Locked for V1 honesty (Phases 0–10 close)

---

## Decisions

| Item | Decision | Rationale |
|---|---|---|
| **Email verification** | **JWT-only** verify tokens (no `email_verifications` table) | Enough for V1; Resend delivers link; token type=`verify` + short TTL. Revisit if we need audit of unused invites. |
| **`refresh_tokens` table** | **Deferred** | Sprint B: rotate JWT + clear cookie on logout. Add DB revoke when multi-device / force-logout is required. |
| **`booking_passengers`** | **Deferred to Phase 19–21** | `quote_passengers` exists now; copy into booking passengers when booking confirm lands. Master plan checkbox was premature. |
| **`quotes.public_token` generator** | Helper added: `app.utils.tokens.generate_public_token()` | Wire when Quotes module starts (Phase 14). |
| **Customer phone uniqueness** | **Unique `(organization_id, phone_e164)` where `deleted_at IS NULL`** | Migration `b2c3d4e5f6a7`. Soft-deleted phones can be reused. |
| **`User.active_organization_id`** | **Not a DB column** — dynamic on request from first membership | V1 = single org per user. Documented in `deps.py`. |
| **Org context (FIX-15)** | Single-org-per-user for V1; `/me` returns `active_organization_id` + `org_role` | Signup creates membership before verify/login. |

---

## Migrations to run

```bash
cd apps/api
alembic upgrade head   # includes b2c3d4e5f6a7 phone unique
```

---

## Explicitly not Phase-4-complete until

- Live booking passenger table at Phase 21 (or earlier if booking confirm needs it)
- Optional: `refresh_tokens` if security review demands server-side revoke
