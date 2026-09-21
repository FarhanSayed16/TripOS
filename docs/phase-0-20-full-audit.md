# TripOS — Full Phase 0→20 Re-Audit (Code + Security + Completeness)

**Audit date:** 2026-09-16  
**Scope:** Every phase 0–20 — code, integration, security, scalability, honesty vs master plan  
**Method:** Fresh code review (not trusting prior Sprint A–F “DONE” claims)  
**Companion docs:** `phase-0-10-audit-fixes.md` · `phase-11-20-audit-fixes.md` · `tripos-master-plan.md`

---

## Sprint I status (2026-09-16) — Live money handoff

| Item | Status |
|---|---|
| Handoff + account runbooks | **Done** (`docs/phase-0/SPRINT_I_HANDOFF.md`) |
| Live Razorpay Payment Link code path | **Done** (`razorpay_client.py`; needs keys) |
| `PLATFORM_FEE_PAISE` (default 0) | **Done** |
| Webhook `payment_link.paid` | **Done** |
| Nilesh commercial sign-off | **PENDING EXTERNAL** |
| Resend / Vercel / Render accounts | **PENDING EXTERNAL** (Farhan) |
| One Razorpay test capture in DB | **PENDING EXTERNAL** |
| Phase 21 real booking | **Not started** (next engineering sprint) |

**Honest exit:** Sprint I is **packaged**, not **complete**, until external gates close.

---

## Sprint H status (2026-09-16) — Auth harden + completeness

| Fix | Status |
|---|---|
| AUDIT-004 Refresh revoke via `token_version` | **Done** (migration `e5f6a7b8c9d0`) |
| AUDIT-018 Reset token single-use (bound to `tv`) | **Done** |
| AUDIT-019 Redact email JWT logs | **Done** |
| AUDIT-020 `/ready` generic errors | **Done** |
| AUDIT-014 `FRONTEND_URL` for public/email links | **Done** |
| AUDIT-015 Credential pack webhook URL | **Done** (Sprint G) |
| AUDIT-012/013 Extend / % markup honesty | **Done** (`quotes-v1-markup-expiry.md`) |
| AUDIT-016 Idempotency race-safe | **Done** (IntegrityError catch) |
| AUDIT-017 Durable manual review | **Done** (`audit_events`) |
| AUDIT-022 AppError on quotes service | **Done** |
| AUDIT-023 Pytest + CI | **Done** (`test_sprint_h.py`) |

**After pull:** `alembic upgrade head` (adds `users.token_version`).

**Next:** Manual E2E smoke → Sprint I (Phase 0 commercial) or Phase 21 booking confirm.

---

## Sprint G status (2026-09-16) — Integrity & security

| Fix | Status |
|---|---|
| AUDIT-001 `deps.py` IndentationError | **Done** |
| AUDIT-003 JWT `type=access` enforcement | **Done** |
| AUDIT-002 Quote passengers/ready org-scoped | **Done** |
| AUDIT-005 Customer org bind on create | **Done** |
| AUDIT-006 Commercial APIs require `OrgStatus.active` | **Done** (`require_active_org`) |
| AUDIT-011 Worker reclaim stale `running` | **Done** (15m lease) |
| AUDIT-007 Webhook amount/currency verify | **Done** |
| AUDIT-008 Production never unsigned webhooks | **Done** |
| AUDIT-025 Master plan honesty refresh | **Done** (partial; scorecards updated) |

**Next:** Sprint H (auth harden, AppError, pytest/CI depth) then Phase 21 after mock E2E smoke.

---

## Executive verdict

| Question | Answer |
|---|---|
| Are Sprints A–F “done” as engineering batches? | **Mostly yes** — many features exist |
| Is Sprint G integrity/security done? | **Yes** |
| Is Sprint H auth harden / completeness done? | **Yes** (`token_version`, redact logs, AppError, audit ops) |
| Is Phases 0–20 **exit-complete / foolproof**? | **Almost for mock demo** — live pay + Phase 21 confirm remain |
| Safe to start Phase 21? | **Yes** after `alembic upgrade head` + local smoke |
| Safe for pilot / live money? | **No** — wait for Nilesh sign-off + one Razorpay test capture |

**Bottom line (post Sprint I packaging):** Engineering handoff + live Razorpay code path are ready. **Sprint I is not complete** until Nilesh signs commercial + Farhan records one test capture. Phase 21 mock→real booking can proceed in parallel.

---

## Scorecard (honest)

| Phase | Master plan | Live code verdict | Notes |
|---|---|---|---|
| **0** Commercial / creds | PARTIAL | **EXTERNAL / BLOCKED** | Nilesh checklist empty; secrets templates only |
| **1** Monorepo | DONE | **DONE** | `.gitignore` OK; git may not be initialized |
| **2** Docker / env | DONE | **DONE** | Postgres + Redis compose OK |
| **3** Platform core | DONE | **MOSTLY** | argon2 + `/ready` OK; encryption stub; CORS localhost |
| **4** Schema | DONE* | **DONE for V1** | Deferred tables documented |
| **5** Auth BE | DONE | **FIXED (Sprint G)** | `deps.py` + JWT `type=access` |
| **6** Orgs | DONE | **MOSTLY** | Reject OK; commercial routes gated on active (Sprint G) |
| **7** Design | DONE | **DONE** | Tokens / fonts / EmptyState / motion |
| **8** Layouts / routes | DONE | **DONE** | Route IA fixed |
| **9** Auth FE / BFF | DONE | **MOSTLY** | Auth import fixed; no Next middleware yet |
| **10** CRM | DONE | **MOSTLY** | Scoped CRUD; requires active org |
| **11** Adapters | DONE | **MOSTLY** | Contract + pytest; Retry-After claim false |
| **12** Inventory | DONE | **MOSTLY** | Search + rate limit; Redis skipped; revalidate-before-book → Phase 21 |
| **13** Search FE | DONE | **DONE** | Hub + `search_request_id` wired |
| **14** Quotes BE | DONE | **MOSTLY** | IDOR fixed (Sprint G); no extend |
| **15** Quotes FE | DONE | **MOSTLY** | Builder works; snapshot titles thin |
| **16** wa.me | DONE | **MOSTLY** | Provider port OK; prefers `FRONTEND_URL` |
| **17** Public quote | DONE | **MOSTLY** | Brand + status; no OG image |
| **18** Payments BE | MOCK | **MOCK-COMPLETE** | Link + HMAC + amount verify (Sprint G) |
| **19** Payments UI | PARTIAL | **PARTIAL** | UI + mock status; live E2E open |
| **20** Worker | PARTIAL | **MOSTLY** | SKIP LOCKED + stale reclaim; booking confirm still stub |

\*V1 honesty = deferred tables written down, not forgotten.

---

## Finding counts

| Severity | Open count | Meaning |
|---|---|---|
| **CRITICAL** | 2 | Must fix before any Phase 21 / any demo that needs API |
| **HIGH** | 8 | Security / honesty blockers for pilot |
| **MEDIUM** | 14 | Should fix before claiming 0–20 complete |
| **LOW** | 12 | Polish / DX / optional |
| **EXTERNAL** | 3 | Needs Nilesh / Sahil / Farhan (not code) |
| **DEFERRED OK** | several | Explicitly out of V1 scope if documented |

---

# CRITICAL — fix immediately (Sprint G Day 1)

---

### AUDIT-001 — `get_current_user` IndentationError (API auth broken)

| | |
|---|---|
| **Phase** | 5 / 9 |
| **Category** | completeness / security |
| **Status** | **FIXED (Sprint G)** |
| **Impact** | Protected routes cannot load. Signup/CRM/quotes/payments auth stack is non-functional until fixed. Contradicts all “Phases 1–10 DONE” claims. |
| **Required** | Re-indent body of `get_current_user`; add CI smoke `python -c "from app.api.deps import get_current_user"`; run `scripts/test_auth.py` |

---

### AUDIT-002 — Cross-org quote IDOR (passengers + mark-ready)

| | |
|---|---|
| **Phase** | 14 |
| **Category** | security |
| **Status** | **FIXED (Sprint G)** |
| **Evidence** | `services/quotes.py` `update_quote_passengers` / `mark_quote_ready` filter by `Quote.id` only. `api/quotes.py` does not pass org. Contrast: get/list/payment/send correctly scope by `organization_id`. |
| **Impact** | Any authenticated agent with another org’s quote UUID can rewrite passenger/passport data or mark ready. |
| **Required** | Always `where(Quote.id == …, Quote.organization_id == current_user.active_organization_id)`; 404 on miss. Same for any other unscoped mutation. |

---

# HIGH — security / pilot blockers

---

### AUDIT-003 — JWT purpose confusion (verify / reset usable as access)

| | |
|---|---|
| **Phase** | 5 |
| **Category** | security |
| **Status** | **FIXED (Sprint G)** |
| **Evidence** | `create_access_token` used for login, verify (`type=verify`), reset (`type=reset_password`). `get_current_user` only checks `sub` — does **not** reject non-access types. |
| **Impact** | Holder of email verify/reset link can call authenticated APIs as that user until token expiry. |
| **Required** | Mint login tokens with `type: "access"`; `get_current_user` must require `type == "access"` (or equivalent `aud`). Keep verify/reset on dedicated claims + short TTL. |

---

### AUDIT-004 — Refresh “rotation” is not one-use

| | |
|---|---|
| **Phase** | 5 / 9 |
| **Category** | security / honesty |
| **Status** | OPEN (overstated as fixed in Sprint B) |
| **Evidence** | Refresh JWT gets `jti` but nothing stores/checks/revokes it. Logout only clears browser cookie. |
| **Impact** | Stolen refresh cookie remains valid for full `REFRESH_TOKEN_EXPIRE_DAYS` even after victim refreshes. |
| **Required** | Persist refresh `jti` (or hash) + revoke on rotate/logout; **or** document residual risk honestly and uncheck “one-use” claims. |

---

### AUDIT-005 — Quote create does not bind customer to caller org

| | |
|---|---|
| **Phase** | 14 |
| **Category** | security |
| **Status** | **FIXED (Sprint G)** |
| **Evidence** | `create_quote` sets `customer_id` from payload without `Customer.organization_id` check. |
| **Impact** | Cross-org customer attachment / privacy bleed. |
| **Required** | Load customer with org filter before create; 404 if not owned. |

---

### AUDIT-006 — Pending / inactive orgs can use commercial APIs

| | |
|---|---|
| **Phase** | 6 |
| **Category** | security / completeness |
| **Status** | **FIXED (Sprint G)** |
| **Evidence** | Login does not check `Organization.status`. CRM/inventory/quotes only require membership exists. |
| **Impact** | Unapproved agencies can search / quote / mock-pay. |
| **Required** | Gate commercial routes on `OrgStatus.active` (platform admin exception optional). Return `org_status` on `/me` + FE banner. |

---

### AUDIT-007 — Webhook does not verify payment amount

| | |
|---|---|
| **Phase** | 18 |
| **Category** | security |
| **Status** | **FIXED (Sprint G)** |
| **Evidence** | `process_razorpay_webhook` matches `order_id` and marks captured — no compare of webhook `amount` to `Payment.amount`. |
| **Impact** | With valid signature (or misconfigured mock unsigned), wrong amount can still mark paid. |
| **Required** | Hard-fail on amount/currency mismatch; alert + audit event. |

---

### AUDIT-008 — Mock unsigned webhooks allowed when secret missing

| | |
|---|---|
| **Phase** | 18 |
| **Category** | security |
| **Status** | **FIXED (Sprint G)** — unsigned only if not production + mock + no secret |
| **Evidence** | `webhooks.py` skips HMAC if no secret and `PAYMENTS_MODE=mock`. |
| **Impact** | Mis-deployed mock mode = open capture endpoint. |
| **Required** | Require secret whenever `ENV=production`; local-only flag for unsigned; never ship mock unsigned publicly. |

---

### AUDIT-009 — Phase 0 commercial + credentials still empty

| | |
|---|---|
| **Phase** | 0 |
| **Category** | honesty / EXTERNAL |
| **Status** | EXTERNAL |
| **Evidence** | `docs/phase-0/COMMERCIAL_CHECKLIST.md` brackets; `secrets/` templates only. |
| **Impact** | Blocks honest Phase 18/19 live Razorpay and pilot money. Mock Phase 21 can proceed after Sprint G P0s. |
| **Required** | Nilesh: merchant / settlement / fee; Farhan: Resend/Vercel/Render; Sahil: supplier sandbox when Phase 25. |

---

### AUDIT-010 — Booking confirm is still fake (not Phase 20 exit)

| | |
|---|---|
| **Phase** | 20 → 21 |
| **Category** | honesty |
| **Status** | OPEN (intentional stub — dangerous if treated as real) |
| **Evidence** | `jobs.py` `handle_booking_confirm` sleeps and invents PNR; no adapter revalidate/book. Master plan §12.2 claims revalidate-before-book `[x]`. |
| **Impact** | UI/ops may believe bookings are confirmed with suppliers. |
| **Required** | Label booking `pending` / job `booking_confirm_stub` until Phase 21; uncheck master plan revalidate-before-book; implement real confirm in Phase 21. |

---

### AUDIT-011 — Worker jobs can stick forever in `running`

| | |
|---|---|
| **Phase** | 20 |
| **Category** | scalability / reliability |
| **Status** | **FIXED (Sprint G)** — 15m reclaim |
| **Evidence** | `worker.py` commits `running` then processes; crash leaves row `running`; poll only claims `pending`. |
| **Impact** | Missed booking confirms / refund reviews after worker crash. |
| **Required** | Lease/heartbeat reclaim: stale `running` → `pending` after N minutes. |

---

# MEDIUM — complete before claiming 0–20 done

---

### AUDIT-012 — Quote extend ≤24h + fare-risk warning missing
- **Phase 14–15** · Master plan still `[x]`
- Implement capped extend API+UI **or** uncheck and document “no extend in V1”

### AUDIT-013 — % markup claimed; only flat paise
- **Phase 14** · Document “flat ₹ (paise) only V1” and uncheck `%` in master plan

### AUDIT-014 — `FRONTEND_URL` unused for wa.me public links
- **Phase 16** · `quotes.py` uses `BACKEND_CORS_ORIGINS[0]`; prefer `settings.FRONTEND_URL`

### AUDIT-015 — Credential pack webhook path wrong
- **Phase 18** · Template says `/api/v1/payments/webhook`; real route is `POST /api/v1/webhooks/razorpay`

### AUDIT-016 — Payment-link idempotency is check-then-act
- **Phase 18** · `claim_idempotency_key` SELECTs only; race can 500. Use insert-or-catch unique violation.

### AUDIT-017 — Expired-quote capture is log-only “manual review”
- **Phase 18** · Persist durable ops signal / audit / `needs_manual_support` flag

### AUDIT-018 — Reset-password tokens reusable until expiry
- **Phase 5** · After successful reset, invalidate token (password version / used jti store)

### AUDIT-019 — Mock email logs full JWT links
- **Phase 5** · Redact tokens in logs (email + suffix only)

### AUDIT-020 — `/ready` returns raw exception strings
- **Phase 3** · External body: generic disconnected; log detail server-side

### AUDIT-021 — No Next.js middleware for `/app` / `/admin`
- **Phase 9** · Client-only guards; add middleware soft-gate (API remains source of truth)

### AUDIT-022 — AppError vs HTTPException inconsistency
- **Cross-cut** · Quotes/inventory/public often `{detail}` only; standardize on `AppError` + `error_code`

### AUDIT-023 — Pytest / CI gaps
- **DX** · Adapter tests exist (14 passing); missing public sanitize, webhook HMAC/amount, pax gate, org IDOR tests. CI still echo placeholder — wire `pytest` + ruff/eslint

### AUDIT-024 — In-memory rate limit not multi-instance safe
- **Phase 12** · Document single-process pilot caveat; Redis limiter when scaling API replicas

### AUDIT-025 — Master plan honesty patch incomplete
- Still over-checked: Retry-After, revalidate-before-book, extend ≤24h, % markup, OG image, Razorpay link expiry = `valid_until`  
- Scorecards in `phase-11-20-audit-fixes.md` still say “SKIP LOCKED still Sprint F” — **stale**

---

# LOW — polish / enhancements

| ID | Phase | Item | Action |
|---|---|---|---|
| AUDIT-026 | 17 | No static OG image | Add asset or uncheck |
| AUDIT-027 | 14 | Hotel pax gate always min 1 | Use search guest count or document |
| AUDIT-028 | 15 | Quote detail shows snapshot UUID | Return sanitized offer title/description |
| AUDIT-029 | 15 | Fare-change UX is `alert()` | Inline banner |
| AUDIT-030 | 19 | Payments search input dead | Wire filter or remove |
| AUDIT-031 | 18 | Refund initiate stub missing from API | No-op admin stub + docs or uncheck |
| AUDIT-032 | 10 | No customer PATCH/delete UI | Optional |
| AUDIT-033 | 10/23 | Timeline / audit_events empty | Append on quote.sent / payment.captured |
| AUDIT-034 | 5 | Signup password min_length | Add ≥8 (or policy) |
| AUDIT-035 | 6 | Admin Agents approve UI is ComingSoon | Wire or document Postman-only |
| AUDIT-036 | 2 | `.env.example` missing CORS keys | Document |
| AUDIT-037 | 1 | CI lint placeholder | Wire when stable |
| AUDIT-038 | 0 | Git not initialized / check-ignore unverified | `git init` + verify secrets ignore |

---

# What is actually solid (keep / don’t regress)

These patterns are real and should remain:

1. **argon2** hashing + bcrypt verify/rehash (`security.py`)
2. **Prod JWT fail-fast** on placeholder secret (`config.py`)
3. **Refresh cookie** HttpOnly + SameSite=lax + Secure in production
4. **BFF** rewrite + `credentials: 'include'` + in-memory access + 401 refresh once
5. **CRM org scoping** + soft-delete + phone unique partial index
6. **Platform admin** via `is_platform_admin` (not email substring)
7. **Public quote sanitization** (no supplier cost / markup on public schema)
8. **Public token** `secrets.token_urlsafe(32)`
9. **Webhook HMAC** with `hmac.compare_digest` when secret set; prod refuses missing secret
10. **Revalidate-before-pay** + mock FARE-CHG / SOLD-OUT fixtures
11. **Worker SKIP LOCKED** on Postgres + retry/backoff/dead
12. **Encryption stub blocked** when `ENV=production`
13. **Dashboard** labeled placeholder (not fake GMV)
14. **Adapter contract pytest** (`tests/test_adapters_contract.py` — 14 tests green when suite runs)
15. **MessagingProvider** port + `wa_me_url`
16. **ADR** `docs/architecture/inventory-v1-mock.md` + payments mock ADR

---

# Deferred (acceptable if documented — do not pretend DONE)

| Item | When |
|---|---|
| Real Fernet/KMS encryption | Before live supplier secrets (Phase 25) |
| Redis / Upstash search cache | Skipped V1 — already documented |
| Live Razorpay SDK + test capture | After Phase 0 merchant (Phase 18/19 exit) |
| Real `adapter.book` confirm | **Phase 21** |
| `booking_passengers` table | Phase 21+ |
| DB `refresh_tokens` revoke | When multi-device revoke required |
| Celery + Redis worker | When outbox volume needs it |
| Multi-org switching | V3 |
| Root `adapters/` extract | Future package split |

---

# Recommended execution plan

## Sprint G — Integrity & security (do first, 1–2 days)

**Must ship before Phase 21:**

1. AUDIT-001 Fix `deps.py` + import smoke in CI  
2. AUDIT-003 JWT `type=access` enforcement  
3. AUDIT-002 Org-scope passengers + ready  
4. AUDIT-005 Bind customer to org on quote create  
5. AUDIT-006 Gate commercial APIs on `OrgStatus.active`  
6. AUDIT-011 Worker stale-`running` reclaim  
7. AUDIT-007 Webhook amount/currency verify  
8. AUDIT-008 Harden mock/unsigned webhook rules  
9. AUDIT-025 Master plan + scorecard honesty refresh  
10. Smoke: auth script + search → quote → ready → public → mock pay → worker job

**Exit:** API imports; no cross-org quote writes; access tokens typed; mock loop green end-to-end.

---

## Sprint H — Auth hardening & completeness (1–2 days)

11. AUDIT-004 Refresh revoke **or** honest residual-risk note  
12. AUDIT-018 Single-use reset tokens  
13. AUDIT-019 Redact JWT from email logs  
14. AUDIT-020 Sanitize `/ready` errors  
15. AUDIT-014 Use `FRONTEND_URL`  
16. AUDIT-015 Fix Razorpay webhook URL in credential templates  
17. AUDIT-012 / 013 Extend-expiry + % markup honesty  
18. AUDIT-016 Idempotency insert-or-catch  
19. AUDIT-017 Durable manual-review signal  
20. AUDIT-022 Unify AppError on commercial routes  
21. AUDIT-023 Pytest for public sanitize + webhook + IDOR + CI pytest job

**Exit:** Can honestly say “Phases 1–20 engineering closed for **mock pilot**” (still not live money).

---

## Sprint I — External / live money (parallel, not Farhan-only)

22. AUDIT-009 Phase 0 commercial filled by Nilesh  
23. Farhan: Resend + Vercel + Render accounts  
24. Live Razorpay test mode + one real capture (Phase 19 exit)  
25. Then **Phase 21** real booking confirm

---

## Optional Sprint J — Polish (can wait)

AUDIT-021, 026–038 as bandwidth allows.

---

# Phase 20 exit — explicit answer

**Not met.**

Reasons:
1. Auth dependency chain currently **broken** (`deps.py`)
2. Outbox can **orphan** `running` jobs
3. `booking_confirm` is a **stub**, not reliable fulfillment
4. Security IDOR + JWT type gaps mean “intact / foolproof” is false
5. Live payments and Phase 0 commercial remain open

After **Sprint G** (and preferably H): mock Phases 1–20 can be called **engineering-complete for demo**.  
Pilot / live money still needs Sprint I + Phase 21+.

---

# Checklist to tick as you close gaps

Copy into issues / project board:

### Sprint G
- [x] AUDIT-001 `deps.py` compile + auth smoke
- [x] AUDIT-003 JWT access type required
- [x] AUDIT-002 Quote passengers/ready org-scoped
- [x] AUDIT-005 Customer org bind on create
- [x] AUDIT-006 Org active gate
- [x] AUDIT-011 Worker reclaim stale running
- [x] AUDIT-007 Webhook amount verify
- [x] AUDIT-008 Production never unsigned webhooks
- [x] AUDIT-025 Master plan honesty + scorecard refresh
- [ ] E2E mock loop smoke green (manual — needs running API + DB)

### Sprint H
- [x] AUDIT-004 Refresh revoke or honesty note
- [x] AUDIT-018 Reset token single-use
- [x] AUDIT-019 Redact email JWT logs
- [x] AUDIT-020 `/ready` generic errors
- [x] AUDIT-014 `FRONTEND_URL`
- [x] AUDIT-015 Credential pack webhook URL
- [x] AUDIT-012/013 Extend / % markup honesty
- [x] AUDIT-016 Idempotency race-safe
- [x] AUDIT-017 Durable manual review
- [x] AUDIT-022 AppError consistency
- [x] AUDIT-023 Pytest + CI

### Sprint I (external)
- [x] AUDIT-009 handoff pack + live code path packaged
- [ ] AUDIT-009 Phase 0 commercial answers (Nilesh sign-off)
- [ ] Resend / Vercel / Render live (Farhan)
- [ ] One Razorpay test capture updates DB
- [ ] Start Phase 21 booking confirm

---

## Sign-off

| Role | Action |
|---|---|
| Farhan | Execute Sprint G immediately; then H |
| Nilesh | Fill Phase 0 commercial (AUDIT-009) |
| Sahil | Supplier sandbox when Phase 25; not blocking Sprint G |

**This document supersedes stale scorecard lines in older audit files where they conflict.** Update those files after Sprint G, or treat this as the single source of truth until then.
