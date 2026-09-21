# TripOS — Phase 0→10 Audit & Required Fixes

### Code + docs audit against `tripos-master-plan.md` Phases 0–10

**Audit date:** 2026-09-16  
**Re-audit (post Sprint A–C):** 2026-09-16  
**Original claimed status:** Development complete through Phase 10 (overstated)  
**Current verdict:** **Engineering gates for Phases 1–10 are closed** after Sprints A–C.  
**Phase 0** remains **PARTIAL** until Nilesh signs commercial + credential values exist.  
**Safe to start Phase 11 (mock adapters/search).** Do **not** treat Phase 0 or Phase 18 payments as done.

---

## Executive scorecard (post Sprint A–C)

| Phase | After sprints | One-line |
|---|---|---|
| **0** | **PARTIAL** | Engineering locks done; commercial checklist + live creds still open (Nilesh/Sahil/Farhan accounts) |
| **1** | **DONE** | Monorepo + real `.gitignore` secrets rules |
| **2** | **DONE** | Docker + env examples + runbooks |
| **3** | **DONE** | App boots; argon2; `/ready` 503; JWT fail-fast in prod |
| **4** | **DONE*** | Schema + phone unique; deferred items documented (`booking_passengers`, `refresh_tokens`) |
| **5** | **DONE** | Signup/login/verify/refresh aligned with models |
| **6** | **DONE** | Org APIs; reject → `inactive`; single-org V1 documented |
| **7** | **DONE** | Fonts, tokens, Toaster, EmptyState, motion |
| **8** | **DONE** | Shells, placeholders, route IA (`/app/customers`, `/q/[token]`) |
| **9** | **DONE** | Auth pages; platform-admin guards; BFF + credentials refresh |
| **10** | **DONE** | CRM at correct path; debounce; timeline shape; wa.me; COUNT total |

\*Phase 4 “DONE” for V1 honesty = required decisions written + phone unique shipped; deferred tables are explicit, not forgotten.

### Still open (not Phase 1–10 engineering blockers)

| Item | Status | Blocks |
|---|---|---|
| FIX-06 commercial + credential **values** | PENDING Nilesh/Sahil/Farhan accounts | Phase 0 DONE; Phase 18 live pay |
| FIX-19 encryption / idempotency real impl | Deferred | Before live supplier secrets / Phase 18 |
| FIX-21 CORS Vercel preview patterns | Deferred | Deploy / preview |
| ENH-* (pytest CI, resend UX, stub READMEs) | Optional | Nice-to-have |

---

## Original scorecard (pre-fix — historical)

| Phase | Master plan marks | Audit result | One-line |
|---|---|---|---|
| **0** | PARTIAL | **PARTIAL** | Templates exist; commercial + creds still open |
| **1** | DONE | **DONE*** | Monorepo OK; `.gitignore` secrets rules are broken |
| **2** | DONE | **DONE** | Docker + env examples + runbooks OK |
| **3** | DONE | **PARTIAL** | App boots; argon2, `/ready` semantics, CORS breadth incomplete |
| **4** | DONE | **PARTIAL** | Most tables exist; missing pieces + signup/model mismatch |
| **5** | DONE | **BROKEN / PARTIAL** | **Signup incompatible with models** — critical |
| **6** | DONE | **PARTIAL** | Org APIs exist; reject uses invalid status |
| **7** | DONE | **PARTIAL** | Primitives exist; Inter + incomplete tokens/motion |
| **8** | DONE | **PARTIAL** | Shells exist; dual `/`, missing placeholder pages, route drift |
| **9** | DONE | **PARTIAL** | Pages exist; role redirect bug; cookie/BFF fragile |
| **10** | DONE | **PARTIAL** | CRM usable at wrong path; timeline stub; debounce bug |

\*Phase 1 “DONE” only after `.gitignore` fix.

---

## Priority legend

| Priority | Meaning |
|---|---|
| **P0** | Fix before any further feature work — broken or security-critical |
| **P1** | Required to honestly close Phases 0–10 |
| **P2** | Important polish / plan alignment before Phase 11+ |
| **P3** | Enhancement / nice-to-have |

---

## Sprint A status (2026-09-16)

| Fix | Status |
|---|---|
| FIX-02 `.gitignore` | **Done** |
| FIX-01 Signup ↔ models | **Done** (+ migration `a1b2c3d4e5f6`, `is_platform_admin`) |
| FIX-03 Org reject → `inactive` | **Done** |
| FIX-04 Admin via `is_platform_admin` | **Done** (API + FE guards) |
| FIX-05 Dual `/` removed; marketing CTA | **Done** |
| FIX-11 Auth test script paths + happy path | **Done** (`scripts/test_auth.py`) |

**After pull:** run `alembic upgrade head` then re-seed if needed (`poetry run python scripts/seed.py`). Existing admin row needs `is_platform_admin=true` — re-seed on empty DB or update manually.

---

## Sprint B status (2026-09-16)

| Fix | Status |
|---|---|
| FIX-12 `/app/customers` + `/q/[token]` | **Done** (legacy `/app/crm` and `/quote/[id]` redirect) |
| FIX-13 Placeholder pages | **Done** (agent + admin nav targets) |
| FIX-14 CRM debounce / timeline / sand / total / wa.me | **Done** (+ soft-delete DELETE) |
| FIX-08 Refresh rotate + Secure cookie + 401 retry | **Done** (V1: rotate JWT + clear cookie; no `refresh_tokens` table yet) |
| FIX-09 `/ready` → 503 when DB down | **Done** |

**V1 refresh decision:** rotate refresh JWT (`jti`) on every `/refresh`, `Secure` when `ENV=production`, logout clears cookie; RTK `baseQueryWithReauth` retries once on 401. DB-backed revoke deferred until multi-device revoke is required.

---

## Sprint C status (2026-09-16)

| Fix | Status |
|---|---|
| FIX-07 argon2 | **Done** (`argon2-cffi`; bcrypt verify + rehash on login) |
| FIX-16 Design tokens/fonts | **Done** (Newsreader + Manrope + JetBrains Mono; Toaster; EmptyState; motion) |
| FIX-17 Layouts / marketing / public / mobile More | **Done** |
| FIX-18 Health / env wiring | **Done** (require `NEXT_PUBLIC_API_URL` for health; proxy via env) |
| FIX-10 Schema decisions + phone unique | **Done** — see `docs/architecture/phase-4-schema-decisions.md` + migration `b2c3d4e5f6a7` |
| FIX-06 Phase 0 commercial chase | **Chased** — pilot defaults assumed for mock only; Nilesh still PENDING |
| FIX-20 Flat API layout | **Done** — `docs/architecture/v1-api-layout.md` (accept flat for V1) |

**After pull:** `alembic upgrade head` (phone unique index). Re-seed or login once to rehash any legacy bcrypt passwords to argon2.

---

# P0 — Critical blockers (fix first)

---

### FIX-01 — Signup is broken against the database models

**Phase:** 5  
**Files:** `apps/api/app/api/auth.py`, `apps/api/app/models/tenancy.py`, `apps/api/app/models/__init__.py`

**Problem:**
- Imports `Membership` — model is `OrganizationMember` (ImportError / AttributeError)
- Sets `User(first_name=…, last_name=…)` — **User has no name columns**
- Creates `Organization(name=…)` — field is **`brand_name`**
- Sets `user.active_organization_id` — **not a DB column** (only attached dynamically in `deps.py`)

**Required fix:**
- [ ] Use `OrganizationMember` with `UserRole`
- [x] Store display name: either add `full_name` / `first_name`+`last_name` on `User` + migration, **or** drop from User and keep only on signup response / org `brand_name`
- [x] `Organization(brand_name=…, slug=…, status=pending_approval)`
- [ ] Do not persist `active_organization_id` on User unless added to schema
- [ ] Ensure signup org status = `pending_approval`
- [x] Manual/API test: signup → verify → login → `/me` → create customer

**Acceptance:** Full signup happy path works against migrated DB.

---

### FIX-02 — `.gitignore` does not actually ignore secrets / `.env`

**Phase:** 0 / 1  
**File:** `.gitignore`

**Problem:** Secrets section is markdown bullets with backticks (`- \`secrets/\``). Git will **not** ignore `secrets/` or `.env`.

**Required fix:**
- [x] Replace with valid patterns:

```gitignore
secrets/**
!.secrets/README.md
.env
.env.*
!.env.example
apps/*/.env
apps/*/.env.local
**/*.pem
**/credentials.json
```

- [ ] Verify with `git check-ignore -v secrets/foo.md` once repo is initialized
- [ ] If any `.env` was already committed, rotate secrets

**Acceptance:** Real env files and credential packs cannot be committed.

---

### FIX-03 — Org reject writes invalid enum value `"suspended"`

**Phase:** 6  
**File:** `apps/api/app/api/organizations.py`

**Problem:** Reject sets `org.status = "suspended"` but `OrgStatus` is `pending_approval | active | inactive`.

**Required fix:**
- [ ] Reject → `OrgStatus.inactive` (or add explicit `rejected` to enum + migration)
- [x] Align seed/admin docs with chosen statuses
- [ ] Add `invited` only if still required by plan; otherwise document V1 = pending/active/inactive only

**Acceptance:** Approve/reject never raises DB enum errors.

---

### FIX-04 — Admin access control is insecure (email substring)

**Phase:** 9 (+ 6 deps)  
**Files:** `apps/web/src/contexts/AuthContext.tsx`, `apps/api/app/api/deps.py`

**Problem:**
- Frontend: `data.email.includes("admin")` → `/admin`
- Backend platform admin hardcoded to `admin@tripos.in`
- Any authenticated user can open `/admin` client route (layout only checks “logged in”)

**Required fix:**
- [ ] Return roles / `is_platform_admin` from `/auth/me`
- [ ] Redirect and guard `/admin` using role flags, not email string
- [x] Prefer platform role or membership flag over hardcoded email (email OK as seed bootstrap only)
- [ ] Optional: Next.js `middleware.ts` for `/app` and `/admin`

**Acceptance:** Non-platform users cannot use Admin OS; agents land on `/app`.

---

### FIX-05 — Dual `/` pages conflict

**Phase:** 8 / 9  
**Files:** `apps/web/src/app/page.tsx`, `apps/web/src/app/(marketing)/page.tsx`

**Problem:** Next starter page and marketing page both map to `/` — wrong landing / build ambiguity.

**Required fix:**
- [ ] Delete or redirect `app/page.tsx`
- [x] Marketing page: brand-first TripOS + **one CTA** (Login / Request access)

**Acceptance:** `/` shows TripOS marketing only.

---

# P1 — Required to close Phases 0–10 honestly

---

### FIX-06 — Phase 0 commercial + credentials still open

**Phase:** 0  
**Files:** `docs/phase-0/COMMERCIAL_CHECKLIST.md`, `docs/phase-0/PHASE_0_DECISIONS.md`, `secrets/`

**Required:**
- [ ] Nilesh fills commercial checklist (merchant, invoice, settlement, supplier TBO/TripJack, platform fee)
- [x] At least decide pilot defaults in writing if delayed (e.g. platform fee ₹0) — engineering assumes; Nilesh must confirm
- [ ] Farhan: Resend + Vercel + Render accounts when ready
- [ ] Sahil/Nilesh: supplier sandbox pack (needed before Phase 25; not blocking Phase 11 mock)
- [ ] Mark Phase 0 DONE in master plan only when 0.2 written answers exist

**Sprint C:** Chase logged in `PHASE_0_DECISIONS.md`. Phase 11 mock OK; Phase 18 blocked on merchant answers.

---

### FIX-07 — Password hashing: plan = argon2, code = bcrypt

**Phase:** 3 / 5  
**Files:** `apps/api/app/core/security.py`, `apps/api/pyproject.toml`

**Required:**
- [x] Switch to argon2 (e.g. `argon2-cffi`) **or** formally amend master plan to allow bcrypt
- [x] If switching after users exist: migration/rehash strategy on login

**Recommendation:** Implement argon2 now while user count is ~0.

---

### FIX-08 — Refresh token lifecycle incomplete

**Phase:** 5 / 9  
**Files:** `apps/api/app/api/auth.py`, `apps/web/src/lib/apiSlice.ts`, AuthContext

**Gaps:**
- No refresh rotation
- No `refresh_tokens` table / revoke on logout
- Cookie `secure=False` hardcoded
- FE may need explicit `credentials: 'include'` for cookie refresh via proxy
- No 401 → refresh → retry baseQuery wrapper

**Required:**
- [x] Document and implement V1 minimum: rotate refresh on `/refresh`, revoke on logout (cookie clear; DB table deferred)
- [x] Set cookie Secure based on env (`ENV=production`)
- [x] Confirm BFF/rewrite forwards cookies; add `credentials: 'include'` if needed
- [x] RTK baseQuery: on 401 try refresh once, else logout

**Acceptance:** Page reload restores session; logout invalidates refresh; stolen cookie window is limited.

---

### FIX-09 — `/ready` returns HTTP 200 when DB is down

**Phase:** 3  
**File:** `apps/api/app/api/health.py`

**Required:**
- [x] Return **503** when DB check fails
- [x] Keep `/health` as liveness (can stay 200)

---

### FIX-10 — Schema gaps vs Phase 4 checklist

**Phase:** 4  
**Files:** models + Alembic

| Item | Status | Action |
|---|---|---|
| `booking_passengers` | Missing | Add table + migration (needed before Phase 21) |
| `email_verifications` | Missing | Optional if JWT-verify is accepted — **document decision** or add table |
| `refresh_tokens` | Missing | Add if choosing DB-backed revoke (FIX-08) |
| `quotes.public_token` generator | Column only | Add `secrets.token_urlsafe(32)` helper when quotes module starts |
| Unique `(organization_id, phone_e164)` on customers | Missing | Add unique constraint / index |
| `User.active_organization_id` | Not in schema | Either add column + migration or keep dynamic-only and stop assigning on signup |

**Required before claiming Phase 4 complete:**
- [x] Migration for `booking_passengers` (deferred in writing to Phase 19–21 — see schema decisions)
- [x] Customer phone uniqueness per org
- [x] Written decision: JWT-only verify vs `email_verifications` table

See: `docs/architecture/phase-4-schema-decisions.md`

---

### FIX-11 — Auth / CRM tests are not real Phase exit tests

**Phase:** 5 / 10  
**Files:** `apps/api/scripts/test_auth.py`, `test_crm.py`

**Problems:**
- Auth script hits `/auth/login` instead of `/api/v1/auth/login`
- No signup → verify → login path
- No bad-password case
- No pytest suite

**Required:**
- [x] Fix script paths
- [x] Add signup→verify→login + bad password
- [ ] Prefer `pytest` under `apps/api/tests/` for CI later

---

### FIX-12 — Route IA drift (frontend vs plan)

**Phase:** 8 / 10 / 17  
**Files:** agent layout, CRM pages, public quote

| Plan | Implemented | Fix |
|---|---|---|
| `/app/customers` | `/app/crm` | Rename routes + nav to `/app/customers` (keep redirect from `/app/crm` if needed) |
| `/q/[token]` | `/quote/[id]` | Use `/q/[token]` per plan (token ≠ id) |

**Required:**
- [x] Align paths before Quotes/Search pages proliferate wrong links

---

### FIX-13 — Phase 8 placeholder pages missing (nav 404s)

**Phase:** 8  
**Agent nav targets without pages:** `/app/search`, `/app/quotes`, `/app/bookings`, `/app/payments`, `/app/settings`  
**Admin:** only `/admin` exists — agents/bookings/failures/payments/suppliers 404

**Required:**
- [x] Add empty placeholder pages (“Coming in Phase X”) for every nav href
- [x] Or disable/hide nav items until built

**Acceptance:** No dead nav links in Agent/Admin shells.

---

### FIX-14 — CRM Phase 10 incompleteness

**Phase:** 10  
**Files:** `apps/web/.../crm/*`, `apps/api/app/api/customers.py`

**Required:**
- [x] Timeline endpoint returns real structure (empty lists OK) — not only a hardcoded stub note
- [x] Fix search debounce (cleanup timer properly)
- [x] Wire WhatsApp button to `wa.me` with E.164 digits (or hide until Phase 16)
- [x] Remove / define `bg-sand` token
- [x] Soft-delete API or drop soft-delete pretence
- [x] Fix list `total` to be real COUNT for pagination
- [ ] Optional: PATCH UI for customer update (API exists)

---

### FIX-15 — Org context / membership loading

**Phase:** 6  
**File:** `apps/api/app/api/deps.py`

**Gaps:**
- Picks `memberships[0]` as active org — fragile with multi-org later
- Platform admin check hardcoded

**Required for V1 honesty:**
- [x] Document single-org-per-user V1 assumption
- [x] Ensure signup creates membership before `/me` works
- [x] Return org id + role on `/me`

---

# P2 — Plan alignment & quality (before Phase 11+)

---

### FIX-16 — Design system incomplete (Phase 7)

**Files:** `globals.css`, `layout.tsx`, UI primitives

- [x] Replace **Inter** with planned UI + display fonts (not Inter/Roboto/Arial)
- [x] Load mono font referenced by tokens (or remove dead `--font-geist-mono`)
- [x] Set `--focus` to teal family
- [x] Add space scale + motion duration/easing tokens
- [x] Mount global `<Toaster />` in Providers
- [x] Reusable `EmptyState` component
- [x] Use `PageTransition` on Agent/Auth routes (respect `prefers-reduced-motion` explicitly)
- [x] Remove purple-leaning dark sidebar leftovers if unused; avoid dark-mode-first product UI

---

### FIX-17 — Layouts / marketing / public polish (Phase 8–9)

- [x] AuthLayout: brand + centered atmosphere (not empty fragment)
- [x] Marketing: real CTA
- [x] PublicLayout: agency-ready header/footer shell
- [x] Mobile tabs: Home · Search · Quotes · Bookings · More (or match plan)

---

### FIX-18 — Health / env wiring (Phase 8)

**Files:** `apps/web/src/app/api/health/route.ts`, `next.config.ts`

- [x] Health check must fail clearly if `NEXT_PUBLIC_API_URL` missing/wrong (no silent wrong default in prod)
- [x] Proxy rewrite should use env, not only hardcoded `127.0.0.1:8000`

---

### FIX-19 — Encryption & idempotency stubs are dangerous if used early

**Files:** `apps/api/app/utils/encryption.py`, `idempotency.py`

- [ ] Do not store real supplier secrets until Fernet/KMS encryption is real
- [ ] Idempotency helper currently always `True` — implement before Phase 18 payments

---

### FIX-20 — Structure drift from backend plan (`modules/*`)

**Observation:** Code uses flat `app/api`, `app/schemas`, `app/models` instead of `modules/*/`.

**Required decision (pick one):**
- [x] **A.** Amend docs to accept flat layout for V1 (faster) — `docs/architecture/v1-api-layout.md`
- [ ] **B.** Refactor toward `modules/*` before more features  

**Recommendation:** Accept flat layout for V1 in writing; enforce module boundaries by import rules.

---

### FIX-21 — CORS / DATABASE_URL small mismatches

- [ ] Expand CORS allowlist pattern for Vercel previews when deploying
- [x] Align `.env.example` `postgresql://` vs app `postgresql+psycopg://`
- [x] Ensure default `JWT_SECRET` cannot ship to production (fail fast if placeholder)

---

### FIX-22 — Seed / platform bootstrap

**File:** `apps/api/scripts/seed.py`

- [x] Confirm seed creates platform admin usable with FIX-04 role model
- [x] Document default password change requirement
- [x] Link seed admin to platform-admin flag used by deps

---

# P3 — Enhancements (optional now)

---

### ENH-01 — Proper pytest + CI lint

- [ ] Replace CI echo placeholder with ruff + eslint when stable
- [ ] Add note in CI: never echo secrets

### ENH-02 — Customer soft-delete + merge

- [ ] Soft-delete endpoint; phone uniqueness with soft-delete awareness

### ENH-03 — Request email verification resend endpoint UX

- [ ] Explicit “resend verification” API + button (if not already complete)

### ENH-04 — Forgot/reset already built

- [ ] Keep; mark as ahead of plan (good) — ensure tokens expire and are single-use if possible

### ENH-05 — Empty `apps/worker`, `apps/ai`, `adapters`

- [ ] OK as stubs until Phases 11/20/35 — add README stubs explaining purpose

---

# Risks (if ignored)

| Risk | Impact |
|---|---|
| Signup broken | No real agents can register — Phase 5/9/10 invalid |
| `.gitignore` broken | Accidental secret commit |
| Email-based admin | Privilege escalation / wrong redirects |
| No refresh revoke | Stolen session until JWT expiry |
| Wrong CRM/quote routes | Rework when Quotes/WhatsApp land |
| Claiming Phase 10 done | Technical debt compounds in Phase 11–18 |
| Stub encryption used for supplier creds | Credential leakage |

---

# Suggested fix order (execution sprint)

### Sprint A — Unblock auth (1–2 days)
1. FIX-02 `.gitignore`  
2. FIX-01 Signup ↔ models  
3. FIX-03 Org reject status  
4. FIX-04 Admin roles  
5. FIX-05 Dual `/`  
6. FIX-11 Auth tests paths + happy path  

### Sprint B — Close Phase 8–10 honestly (2–3 days) — **DONE 2026-09-16**
7. FIX-12 Route rename customers + `/q/[token]` prep  
8. FIX-13 Placeholder pages  
9. FIX-14 CRM bugs (debounce, timeline shape, sand, total)  
10. FIX-08 Refresh/credentials minimum  
11. FIX-09 `/ready` 503  

### Sprint C — Foundations polish (2 days) — **DONE 2026-09-16**
12. FIX-07 argon2  
13. FIX-16 Design tokens/fonts  
14. FIX-17–18 Layouts/health/env  
15. FIX-10 Schema decisions + phone unique  
16. FIX-06 Phase 0 commercial chase (parallel with Nilesh)  
17. FIX-20 Document flat API layout acceptance  

**Then:** Re-audit Phases 0–10 → update master plan checkboxes truthfully → start Phase 11.

### Re-audit result (2026-09-16)

- Sprints **A + B + C** executed.
- Phases **1–10 engineering:** closed for V1 honesty.
- Phase **0:** still PARTIAL (commercial + credential values).
- **Next:** Phase 11 mock adapters/search. Keep chasing Nilesh on `COMMERCIAL_CHECKLIST.md` in parallel.

---

# What is actually in good shape

- Monorepo layout (`apps/web`, `apps/api`, stubs for worker/ai/adapters)
- Docker Compose Postgres (+ optional Redis)
- Env examples + root README runbooks
- FastAPI boots with middleware, errors, health
- Alembic initial migration covering most V1 commercial/inventory tables
- Seed script for platform admin + mock supplier
- Login/me/verify/forgot-reset surface area
- Org get/update/members/pending/approve APIs (with FIX-03)
- CRM create/list/search + E.164 normalize (India)
- Frontend shells (Agent/Admin), Lucide icons, many shadcn primitives
- Auth pages (login/signup/verify/forgot/reset)
- CRM list/detail UI with phone hints

---

# Master plan honesty patch (recommended)

After Sprint A–B, update `tripos-master-plan.md`:

- Re-open checkboxes that were marked `[x]` but are only PARTIAL
- Or add a note under Phases 3–10: “Scaffolded; see `docs/phase-0-10-audit-fixes.md`”

Do **not** treat current `[x]` marks as exit-complete.

---

## Sign-off

| Role | Action |
|---|---|
| Farhan | Sprints A–C done; Phase 11 may start (mock) |
| Nilesh | Complete commercial checklist (FIX-06) — still required for Phase 0 DONE / Phase 18 |
| Sahil | Supplier sandbox pack when available |

**Next document after fixes:** optional `docs/phase-0-10-reaudit.md` — superseded by scorecard update at top of this file (2026-09-16).
