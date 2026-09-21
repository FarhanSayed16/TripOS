# TripOS — Complete Master Plan (Execution Checklist)

### Final checkpoint document for building the entire product without missing work

**Use with:** [`tripos-docs-index.md`](./tripos-docs-index.md)  
**Detail references:** backend / frontend / implementation / modules / enhancements / work-division docs  

**How to use:** Treat every `- [ ]` as a gate. Finish a phase before starting the next unless the phase explicitly says it can run in parallel.  
**Owner default:** **Farhan** for all product/AI code. **Nilesh / Sahil** = API credentials, commercials, pilot agents only.  
**Stack lock:** Next.js → Vercel · FastAPI → Render · PostgreSQL · Upstash (when needed) · Resend · Razorpay · wa.me · Adapter platform for suppliers.

---

# PART A — NORTH STAR

## A1. One-line product
Software for travel agents to search flights/hotels, build a margin quote, share via WhatsApp (wa.me), collect payment, auto-confirm booking, and keep CRM — from one dashboard.

## A2. Success metric
**Monthly Active Transacting Agents** = agents with ≥1 real paid booking that month.  
Secondary: GMV per active agent.

## A3. Non-negotiables
- [ ] B2B agent OS only (not MakeMyTrip clone)
- [ ] Supplier APIs only behind adapters
- [ ] AI never invents price/availability
- [ ] Multi-tenant `organization_id` on business data
- [ ] Idempotent payment → booking
- [ ] Fare revalidate before pay link and before book
- [ ] Public quote never shows agent cost
- [ ] V1 WhatsApp = wa.me (not Cloud API)
- [ ] Modular monolith (no microservices in V1)

## A4. Product versions (reminder)
| Version | Meaning |
|---|---|
| V1 | Core money loop + solid bones |
| V1.5 | Pilot friction fixes |
| V2 | AI, packages, wallet, follow-ups |
| V3 | Multi-supplier strategies, white-label, distributor hierarchy |

---

# PART B — PHASE OVERVIEW (40 PHASES)

| Phase | Name | Version band | ~Weeks (rough) |
|---|---|---|---|
| 0 | Team, commercial, credentials lock | Foundation | 0.5 |
| 1 | Monorepo & engineering standards | Foundation | 0.5 |
| 2 | Local environments & docker | Foundation | 0.5 |
| 3 | Backend platform core | Foundation | 0.5 |
| 4 | Database schema V1 + migrations | Foundation | 0.5 |
| 5 | Auth module (backend) | V1 | 0.5 |
| 6 | Organizations & memberships (backend) | V1 | 0.5 |
| 7 | Frontend design system tokens | V1 | 0.5 |
| 8 | Frontend layouts & navigation shells | V1 | 0.5 |
| 9 | Auth + Resend (frontend wired) | V1 | 0.5 |
| 10 | CRM customers (backend + frontend) | V1 | 0.5 |
| 11 | Adapter platform + Mock supplier | V1 | 0.5 |
| 12 | Inventory search & revalidate (backend) | V1 | 0.75 |
| 13 | Search experience (frontend) | V1 | 0.75 |
| 14 | Quotes engine (backend) | V1 | 0.75 |
| 15 | Quote builder & lists (frontend) | V1 | 0.75 |
| 16 | Messaging wa.me (backend + frontend) | V1 | 0.5 |
| 17 | Public hosted quote pages | V1 | 0.5 |
| 18 | Payments module (backend) | V1 | 0.75 |
| 19 | Payments UI + Razorpay webhook path | V1 | 0.5 |
| 20 | Outbox, worker, async jobs | V1 | 0.5 |
| 21 | Bookings confirm engine (backend) | V1 | 0.75 |
| 22 | Bookings & attention UI (frontend) | V1 | 0.5 |
| 23 | Audit log & honest failure states | V1 | 0.25 |
| 24 | Admin OS (backend + frontend) | V1 | 0.75 |
| 25 | First real supplier adapter (sandbox) | V1 | 1 |
| 26 | Full sandbox E2E hardening | V1 | 0.5 |
| 27 | Production-like deploy (Vercel + Render) | V1 | 0.5 |
| 28 | Security, tenancy, reliability gate | V1 | 0.5 |
| 29 | Pilot onboarding (5–10 agents) | V1 Pilot | 2 |
| 30 | V1.5 friction fixes | V1.5 | 1–2 |
| 31 | V1 Exit Gate (go / no-go for V2) | Gate | 0.25 |
| 32 | V2 Packages | V2 | 1–2 |
| 33 | V2 Commission & Wallet | V2 | 1–2 |
| 34 | V2 Follow-ups & document vault | V2 | 1 |
| 35 | V2 AI Copilot | V2 | 1–2 |
| 36 | V3 Multi-supplier strategies | V3 | 2+ |
| 37 | V3 White-label | V3 | 2+ |
| 38 | V3 Distributor hierarchy | V3 | 2+ |
| 39 | Scale, observability, ops maturity | Scale | ongoing |
| 40 | Continuous backlog & quarterly review | Ongoing | ongoing |

**Rough band totals:** Foundation+V1 build ≈ **12–14 weeks** · Pilot+V1.5+gate ≈ **4 weeks** · then V2/V3. Estimates are planning aids, not commitments.

---

# PART C — DETAILED PHASES & SUB-PHASES

---

## PHASE 0 — Team, commercial, credentials lock

**Goal:** No build ambiguity on money, supplier, or roles.  
**Execution log:** [`docs/phase-0/PHASE_0_DECISIONS.md`](./phase-0/PHASE_0_DECISIONS.md)  
**Status:** STARTED 2026-09-16 — engineering locks DONE; commercial + live creds PENDING

### 0.1 Roles & ownership
- [x] Confirm Farhan = full product FE/BE/integrations **and AI Copilot** *(pre-confirmed in planning; re-ack in team read-through)*
- [x] Confirm Nilesh = licensing, commercials, pilot agents, supply APIs/relationships
- [x] Confirm Sahil = credential sourcing / API access docs only (no AI build)
- [x] AI ownership FINAL: **Farhan only**
- [x] Read `tripos-docs-index.md` + `tripos_plan_review.md` resolution *(Farhan — execution start; share with team)*

### 0.2 Commercial checklist (Nilesh-led)
- [ ] Who is Razorpay merchant of record? → fill [`phase-0/COMMERCIAL_CHECKLIST.md`](./phase-0/COMMERCIAL_CHECKLIST.md)
- [ ] Who invoices the customer (agent vs platform)?
- [ ] Settlement path: customer → gateway → platform/agent
- [ ] Cancellation/refund policy copy (even if manual process) — draft in PHASE_0_DECISIONS.md
- [ ] First supplier chosen: TBO **or** TripJack
- [ ] Confirm sandbox vs production timeline
- [ ] **Platform fee rule for V1/pilot:** flat / % / per product / **₹0 for pilot** (still store `platform_fee` column) — proposed ₹0
- [ ] Confirm default agent markup guidance (optional, non-blocking)

### 0.2b Locked flow decisions (already decided — confirm understood)
- [x] Pax collected **before** payment link (flights full pax; hotels guest minimum)
- [x] V1 login = email + password + Resend (no OTP)
- [x] V1 WhatsApp = wa.me only
- [x] Quote default expiry = **4h for flights, 12h for hotels**; extend ≤24h is **planned but not implemented yet**
- [x] **V1 quotes:** one product type per quote (flight-only **or** hotel-only) — no mixed flight+hotel quotes in V1
- [x] Cross-domain auth = Bearer + BFF/proxy (or documented cookie parent-domain alternative)
- [x] **V1 jobs:** DB-polling outbox worker (no Redis required); Celery+Upstash optional later if volume needs it

### 0.3 Credentials intake (Sahil → Farhan)
- [x] Credential **templates** + gitignored `secrets/` folder created
- [ ] Supplier sandbox docs pack (auth, base URL, rate limits, sample book) — *values pending*
- [ ] Razorpay test keys + webhook secret process — *values pending*
- [ ] Resend account + domain/from-email — *Farhan can create*
- [ ] Vercel + Render accounts ready — *Farhan can create*
- [x] Upstash account ready (**optional for V1** — only required if you later switch to Celery/cache) — skip V1
- [x] WhatsApp Business API **not** required for V1 (wa.me)

### 0.4 Phase 0 exit
- [ ] Written answers for 0.2 stored in team notes *(template ready; awaiting Nilesh)*
- [x] Credential pack folder exists (secrets not committed to git)
- [ ] Master plan Phase 0 marked DONE

**DONE when:** Build can start without commercial blockers on payments/supplier choice.  
**Parallel OK now:** Phase 1–2 (monorepo + docker) while Nilesh fills commercial checklist.

---

## PHASE 1 — Monorepo & engineering standards

**Goal:** Single repo structure matching backend/frontend plans.

### 1.1 Repository skeleton
- [x] Create monorepo root `tripos/`
- [x] Folders: `apps/web`, `apps/api`, `apps/worker`, `apps/ai` (stub ok), `adapters`, `docs`, `.github`
- [x] Root README: what TripOS is + how to run later
- [x] `.gitignore` for env, secrets, node, python caches
- [x] Keep existing `docs/` content

### 1.2 Standards
- [x] Agree Python version (3.12+)
- [x] Agree Node LTS for Next.js
- [x] Lint/format approach (ruff/black + eslint/prettier) documented
- [x] Commit message convention (short, why-focused)
- [x] Branch strategy (main + feature branches)

### 1.3 CI skeleton
- [x] GitHub Actions workflow stub (lint placeholder)
- [x] No secrets in CI logs policy noted

### 1.4 Phase 1 exit
- [x] Empty apps bootable later without restructuring
- [x] Docs linked from root README

**DONE when:** Repo shape matches plans; team clones and understands layout.

---

## PHASE 2 — Local environments & Docker

**Goal:** Local Postgres (and optional Redis) for development.

### 2.1 Docker Compose
- [x] Postgres service
- [x] Optional Redis service (or document Upstash-only later)
- [x] Document ports and credentials for local only

### 2.2 Env templates
- [x] `apps/api/.env.example` (DATABASE_URL, JWT, Resend, Razorpay, flags)
- [x] `apps/web/.env.example` (NEXT_PUBLIC_API_URL)
- [x] Never commit real `.env`

### 2.3 Runbooks
- [x] “Start local DB” steps
- [x] “Run API” steps (placeholder until Phase 3)
- [x] “Run Web” steps (placeholder until Phase 7+)

### 2.4 Phase 2 exit
- [x] Postgres reachable locally
- [x] Env examples complete

**DONE when:** Any engineer can start infrastructure without tribal knowledge.

---

## PHASE 3 — Backend platform core

**Goal:** FastAPI app boots with core cross-cutting pieces.

### 3.1 App factory
- [x] `main` / app factory
- [x] Router mounting pattern
- [x] Lifespan (DB connect/disconnect)
- [x] CORS for Vercel local + prod + preview origins (configurable allowlist)

### 3.2 Core package
- [x] Config / settings loader
- [x] DB engine + session
- [x] Security helpers (password hash, JWT issue/verify)
- [x] **Auth strategy stubs:** Bearer access + refresh cookie for BFF **or** documented parent-domain cookies
- [x] Error types + HTTP exception handlers
- [x] Request ID logging middleware (JSON structured logs)
- [x] Pagination helpers
- [x] Feature flags structure
- [x] Idempotency helper stubs
- [x] Encryption helper stubs for supplier secrets

### 3.3 Health
- [x] `/health` and `/ready` (DB check)

### 3.4 Phase 3 exit
- [x] API runs locally
- [x] Health returns OK with Postgres up
- [x] CORS + auth strategy written in README snippet

**Detail ref:** `tripos-backend-plan.md` §3–4 · `tripos-implementation-plan.md` §0.1  

**DONE when:** Platform core exists; no business modules required yet.

---

## PHASE 4 — Database schema V1 + migrations

**Goal:** Alembic migrations for all V1 tables (+ V3 hooks).

### 4.1 Tenancy & auth tables
- [x] users
- [x] organizations (include slug, brand_name, logo_url, primary_color, parent_organization_id nullable, status)
- [x] organization_members (roles: agent, admin)
- [x] email_verifications / refresh_tokens as needed

### 4.2 CRM
- [x] customers (org scoped; phone uniqueness strategy; **E.164 phone column**)

### 4.3 Inventory
- [x] suppliers
- [x] supplier_credentials (encrypted fields)
- [x] supplier_configs
- [x] search_requests
- [x] offer_snapshots

### 4.4 Commercial loop
- [x] quotes, quote_items — columns: **supplier_cost, agent_markup, platform_fee, customer_total**
- [x] quote passengers / booking_passengers (required before pay for flights)
- [x] payments, refunds
- [x] bookings — include **failure_reason** enum/text field
- [x] messages
- [x] audit_events
- [x] jobs_outbox
- [x] quotes.public_token — **cryptographically random**, unique, not derived from id

### 4.5 Status enums documented
- [x] Quote statuses
- [x] Payment statuses
- [x] Booking statuses + **failure_reason codes** (fare_changed, sold_out, supplier_timeout, supplier_error, missing_pax, unknown)
- [x] Org/agent statuses
- [x] Outbox job statuses

### 4.6 Seed
- [x] Seed script: platform admin user, mock supplier row

### 4.7 Phase 4 exit
- [x] `alembic upgrade head` works on empty DB
- [x] Schema matches backend plan table groups

**DONE when:** Schema is the contract; FE can assume fields exist.

---

## PHASE 5 — Auth module (backend)

**Goal:** Signup, login, verify email, tokens, me.

### 5.1 Services
- [x] Signup creates user + organization + membership
- [x] Login **email + password only** (no OTP in V1) → access + refresh
- [x] Logout / refresh rotate as designed (BFF-friendly)
- [x] Password hashing (argon2)
- [x] Email verification token create + confirm
- [x] Resend integration wrapper sends verify email

### 5.2 Routes
- [x] signup, login, refresh, logout, me
- [x] verify-email request + confirm

### 5.3 Cross-domain auth wiring
- [x] Document chosen path: **Next.js BFF proxy + Bearer** (default) or parent-domain cookies
- [x] Refresh endpoint usable from BFF same-origin calls

### 5.4 Tests
- [x] Signup → verify → login happy path
- [x] Bad password rejected
- [x] Unverified policy decided (block or allow limited)

### 5.5 Phase 5 exit
- [x] Auth works via API client/Postman
- [x] Resend delivers in test mode

**DONE when:** Identity works without UI.

---

## PHASE 6 — Organizations & memberships (backend)

**Goal:** Org profile + roles; branding fields writable.

### 6.1 Services
- [x] Get/update current organization
- [x] List members
- [x] Role checks dependency (agent vs admin)
- [x] Agent status: invited / pending_approval / active / inactive

### 6.2 Admin hooks (minimal API)
- [x] Pending orgs list (for later Admin UI)
- [x] Approve / reject org

### 6.3 Phase 6 exit
- [x] Org context available to protected routes
- [x] Branding fields updateable (even if unused in UI yet)

**DONE when:** Tenancy context is real.

---

## PHASE 7 — Frontend design system tokens

**Goal:** Coastal ink desk theme implemented as tokens (no feature pages yet).

### 7.1 Tokens
- [x] Color CSS variables (ink, paper, teal, coral, amber, mint, line, focus)
- [x] Typography: display + UI + mono chosen and loaded
- [x] Space, radius, motion duration/easing tokens
- [x] Icon library chosen (Lucide or Phosphor only)

### 7.2 Primitives (minimum set)
- [x] Button variants
- [x] Input, Select, Textarea
- [x] Badge / status chip
- [x] Toast
- [x] Modal + Drawer
- [x] Table base
- [x] Skeleton
- [x] Empty state pattern

### 7.3 Motion foundations
- [x] Page enter wrapper
- [x] Reduced-motion media query respected
- [x] Toast enter/exit

### 7.4 Phase 7 exit
- [x] Story/demo page or styleguide route showing primitives
- [x] No purple/terracotta cliché theme

**Detail ref:** `tripos-frontend-plan.md` §2–3, §8  

**DONE when:** All future pages can consume tokens only.

---

## PHASE 8 — Frontend layouts & navigation shells

**Goal:** Five surfaces’ layouts exist with nav placeholders.

### 8.1 Layouts
- [x] MarketingLayout
- [x] AuthLayout
- [x] AgentLayout (sidebar + topbar)
- [x] AdminLayout (distinct accent)
- [x] PublicLayout

### 8.2 Agent nav items (wired to placeholder routes)
- [x] Home, Search, Quotes, Bookings, Customers, Payments, Settings

### 8.3 Admin nav items
- [x] Overview, Agents, Bookings, Failures, Payments, Suppliers

### 8.4 Mobile
- [x] Agent bottom tabs plan implemented for small screens

### 8.5 Frontend → API health
- [x] Next.js `/api/health` (or similar) checks backend `/health` using configured API URL
- [x] Fails clearly if `NEXT_PUBLIC_API_URL` misconfigured

### 8.6 Phase 8 exit
- [x] Navigating shells works with empty pages
- [x] Route groups prevent chrome bleed
- [x] Frontend health check works locally

**DONE when:** IA matches frontend plan.

---

## PHASE 9 — Auth + Resend (frontend wired)

**Goal:** Full auth UX live against backend.

### 9.1 Pages
- [x] Landing (brand-first, one CTA)
- [x] Login
- [x] Signup
- [x] Verify email waiting + confirm
- [x] Optional forgot/reset deferred unless needed

### 9.2 Client wiring
- [x] API client via **BFF/proxy** (preferred) or CORS + Bearer per locked auth strategy
- [x] On page load: BFF calls `/refresh` silently → new access token in memory
- [x] If refresh fails (expired/revoked): redirect to `/login`
- [x] Show brief loading state during session restore (not a flash of login page)
- [x] Protected route guards for `/app` and `/admin`
- [x] Role-based redirect (admin vs agent)
- [x] No long-lived tokens in localStorage (prefer memory + httpOnly refresh via BFF)

### 9.3 UX states
- [x] Loading, error toasts, field errors
- [x] Motion on auth forms

### 9.4 Phase 9 exit
- [x] New user can signup → verify → land in Agent OS (pending approval if required)

**DONE when:** Auth loop is production-shaped.

---

## PHASE 10 — CRM customers (backend + frontend)

**Goal:** Agents manage customers.

### 10.1 Backend
- [x] Customer CRUD
- [x] **Phone normalization to E.164** on create/update (India default +91)
- [x] Reject/repair invalid phones before save
- [x] Search by name/phone
- [x] Org scoping enforced
- [x] Customer timeline endpoint (quotes/bookings empty ok)

### 10.2 Frontend
- [x] Customers list
- [x] Customer create (phone input with format hint)
- [x] Customer detail (timeline placeholders)

### 10.3 Phase 10 exit
- [x] Agent creates customer; stored phone works for wa.me later

**DONE when:** Quotes can attach to a real customer.

---

> **Audit note (2026-09-16):** Sprints A–C closed engineering gaps for Phases **1–10**. See [`phase-0-10-audit-fixes.md`](./phase-0-10-audit-fixes.md).  
> **Phase 0** stays PARTIAL until commercial checklist + credential values. **Phase 11 (mock) may start now.**

---

## PHASE 11 — Adapter platform + Mock supplier

**Goal:** Inventory can search without live TBO.

### 11.1 Adapter interface
- [x] capabilities / search / revalidate / book / cancel / status / map_error
- [x] Registry resolves supplier_code → adapter
- [x] NormalizedOffer shape frozen and documented
- [x] Send fixture NormalizedOffer JSON to AI track if needed

### 11.2 Mock adapter
- [x] Flights search returns deterministic offers
- [x] Hotels search returns deterministic offers
- [x] Revalidate can simulate fare change flag
- [x] Book returns fake supplier refs
- [x] Contract tests pass for mock

### 11.3 Phase 11 exit
- [x] Inventory module can call mock via registry only

**DONE when:** Rest of commercial loop can be built offline.

---

## PHASE 12 — Inventory search & revalidate (backend)

**Goal:** Search APIs for flights/hotels + revalidate.

### 12.1 Search service
- [x] Flight search endpoint
- [x] Hotel search endpoint
- [x] Persist search_requests audit
- [ ] Optional Redis/Upstash cache with short TTL — **skipped for V1 pilot** (see `docs/architecture/inventory-v1-mock.md`)
- [x] Rate limit: **30 searches/min/org** (in-memory token bucket for pilot)
- [x] Cap response to **max 50 offers**, default sort price ascending
- [ ] Adapters respect supplier Retry-After / rate-limit headers (log them) — **N/A for mock; defer to live adapters (Phase 25)**

### 12.2 Revalidate service
- [x] Revalidate offer before quote finalize
- [x] Revalidate before payment link (called by quotes/payments)
- [ ] Revalidate before book (called by bookings job) — **Phase 21** (current job is stub; see `jobs.handle_booking_confirm`)
- [x] Distinct errors: fare_changed vs sold_out vs timeout

### 12.3 Offer snapshots
- [x] Snapshot immutable offer when adding to quote

### 12.4 Phase 12 exit
- [x] Authenticated agent can search mock flights/hotels via API
- [x] Rate limit returns clear 429 under abuse

**DONE when:** Inventory is the only path to offers.

---

## PHASE 13 — Search experience (frontend)

**Goal:** Agents can search and pick offers in UI.

### 13.1 Pages
- [x] Search hub (flights/hotels)
- [x] Flight search form + results table
- [x] Hotel search form + results table

### 13.2 UX
- [x] Skeletons, empty, error
- [x] Stagger motion on results (capped)
- [x] Show first **20** results; Load more within capped 50
- [x] “Add to quote” action stores selection for builder
- [x] Show agent cost vs hide on any shareable preview
- [x] Handle 429 rate limit with clear message

### 13.3 Phase 13 exit
- [x] Agent selects offers and proceeds toward quote builder

**DONE when:** Search UX is usable with mock data.

---

## PHASE 14 — Quotes engine (backend)

**Goal:** Full quote lifecycle server-side.

### 14.1 Builder
- [x] Create quote with customer + items from snapshots
- [x] **V1 rule:** one product type per quote — **flight-only or hotel-only** (no mixed flight+hotel in V1)
- [x] Markup **per item** (flat ₹/paise in V1; **% markup deferred**) → persist **supplier_cost, agent_markup, platform_fee, customer_total**
- [x] **Pax gate:** flights require full pax before payment-link creation; hotels require guest minimum
- [x] Block create-pay-link if pax incomplete
- [x] Default `valid_until`: **4h flights / 12h hotels** from creation
- [ ] Agent may extend ≤ **24 hours** with fare-risk warning — **not implemented (AUDIT-012)**
- [x] Revalidate still required before pay regardless of expiry
- [x] Revalidation failure on any item blocks entire pay (V1 simplicity)

### 14.2 Status machine
- [x] draft → ready → sent → paid → expired / cancelled
- [x] Public token = **cryptographically random** unique secret (not sequential id)

### 14.3 Public quote API
- [x] Get by token — **no agent cost / supplier_cost / platform internals**

### 14.4 Phase 14 exit
- [x] Quote CRUD + public payload verified by API tests
- [x] Cannot create pay link without required pax

**DONE when:** Quotes are the commercial source object.

---

## PHASE 15 — Quote builder & lists (frontend)

**Goal:** Agents build and manage quotes in UI.

### 15.1 Pages
- [x] Quotes list with status filters
- [x] Quote builder (customer, items, markup, pax, totals, expiry)
- [x] Quote detail with timeline/actions

### 15.2 UX rules
- [x] Stepper on mobile
- [x] Fare-change banner if revalidate fails
- [x] Clear customer price emphasis

### 15.3 Phase 15 exit
- [x] Agent creates ready quote from search selection

**DONE when:** Quote UI complete except send/pay polish.

---

## PHASE 16 — Messaging wa.me (backend + frontend)

**Goal:** Share quote via WhatsApp deep link.

### 16.1 Backend
- [x] Message builder (summary + public URL + pay URL placeholder)
- [x] wa.me link generator using **E.164 digits-only** phone
- [x] Reject send if phone not normalized
- [x] messages log write
- [x] Mark quote sent when agent confirms send
- [x] Provider port interface for future Cloud API

### 16.2 Frontend
- [x] Send checklist page
- [x] WaMePreview (edit-safe preview)
- [x] Open wa.me / copy text
- [x] Mark as sent CTA

### 16.3 Phase 16 exit
- [x] Quote status becomes `sent` with message log entry
- [x] wa.me opens correctly for Indian numbers

**DONE when:** WhatsApp share works without Meta API.

---

## PHASE 17 — Public hosted quote pages

**Goal:** Customer-facing quote document.

### 17.1 Pages
- [x] `/q/[token]` quote view
- [x] Expiry display
- [x] Pay CTA (enabled when payment link exists)
- [x] Agency brand_name/logo if set
- [x] `/q/[token]/status` placeholder ready for pay return
- [x] OG meta tags: title = "Travel Quote from {agency_name}", description = trip summary
- [ ] OG image: simple branded card or static asset (WhatsApp rich preview) — **optional; not shipped**

### 17.2 Rules
- [x] No agent cost / supplier jargon
- [x] Token unguessable (random); graceful expired/invalid token page (not raw stack trace)
- [x] Mobile sticky pay bar
- [x] Atmosphere per frontend plan (not flat gray)
- [x] Customer does **not** enter pax on public page (V1)

### 17.3 Phase 17 exit
- [x] Opening public link works logged-out

**DONE when:** Customers can view a professional quote.

---

## PHASE 18 — Payments module (backend)

**Goal:** Create payment links; verify webhooks idempotently.

### 18.1 Services
- [x] Create Razorpay payment link for quote **only if pax gate passed + revalidate OK + not expired**
- [x] Store payment row with idempotency key
- [x] Webhook signature verify
- [x] Mark payment captured once
- [x] Mark quote paid once
- [x] Enqueue booking confirm outbox job (do not book inline)
- [x] Refund initiate stub (manual)

### 18.2 Failure / retry paths (Razorpay ~24h retries)
- [x] Duplicate webhook safe (idempotent no-op)
- [x] Pay on expired quote blocked at create-link time
- [x] Set Razorpay payment link expiry to match quote `valid_until` (or slightly after), if gateway supports it
- [x] If gateway link cannot expire: on webhook, check quote expiry → `payment_captured_quote_expired` → queue for **manual refund decision** (no auto-refund, no silent book)
- [x] Late webhook on already-paid+booked quote → ack no-op
- [x] Payment captured but quote expired → `needs_manual_support` + reason `payment_captured_quote_expired`
- [x] Webhook after booking already failed_* → no-op (no double jobs)

### 18.3 Phase 18 exit
- [x] Simulated/test webhook marks quote paid + outbox row created *(mock mode)*
- [x] Replay webhook does not create second booking job *(mock mode)*
- [ ] **Live Razorpay test-mode capture** — deferred; see `docs/architecture/payments-v1-mock.md`

**DONE when:** Money events are trustworthy.  
**Honesty (2026-09-16):** Mock path trustworthy; live gateway **not** DONE.

---

## PHASE 19 — Payments UI + Razorpay webhook path

**Goal:** UI + real test-mode gateway path.

### 19.1 Agent UI
- [x] Create payment link from quote detail
- [x] Payments list page
- [x] Show payment status on quote

### 19.2 Public
- [x] Pay CTA opens gateway
- [x] Pay return page messaging

### 19.3 Ops
- [ ] Webhook URL configured for test *(pending Razorpay dashboard + secret)*
- [ ] End-to-end test payment in Razorpay test mode *(blocked on Phase 0 merchant)*

### 19.4 Phase 19 exit
- [ ] Test payment captures and updates quote in DB *(live gateway)*
- [x] Agent UI can create mock payment link + list payments *(mock)*

**DONE when:** Live test money flow works.  
**Honesty (2026-09-16):** UI + mock webhook path only — see `payments-v1-mock.md`.

---

## PHASE 20 — Outbox, worker, async jobs

**Goal:** Reliable background processing on Render worker.

### 20.1 Outbox
- [x] jobs_outbox writer/reader
- [x] Status: pending → running → done / dead
- [x] Retries with backoff

### 20.2 Worker app (V1 locked decision)
- [x] **V1 decision:** **DB-polling outbox** (simpler for pilot; **no Redis required**)
- [x] Implement poll loop: `SELECT … FOR UPDATE SKIP LOCKED` (or equivalent) for pending jobs
- [x] Worker entry on Render (background worker service)
- [x] Handlers registered (confirm_booking, expire_quotes, …)
- [x] Document upgrade path: Celery + Upstash Redis if/when volume needs it (not V1 blocker)

### 20.3 Scheduled jobs
- [x] Expire quotes job (via same worker poll or cron trigger)

### 20.4 Phase 20 exit
- [x] Outbox job processes without waiting on HTTP request thread
- [x] Worker runs without Upstash

**DONE when:** Async backbone is real without forcing Redis.

> **Audit note (Sprint G, 2026-09-16):** SKIP LOCKED + stale-`running` reclaim shipped. `booking_confirm` remains a **stub** (fabricated `STUB-*` PNR) until Phase 21. See [`phase-0-20-full-audit.md`](./phase-0-20-full-audit.md). Do not treat confirm as live supplier fulfillment.

---

## PHASE 21 — Bookings confirm engine (backend)

**Goal:** After pay → revalidate → book via adapter → persist.

### 21.1 Confirm job
- [x] Load paid quote
- [x] Assert pax present else `booking_failed_missing_pax`
- [x] Revalidate all items
- [x] On fare change → `booking_failed_fare_changed` + needs_manual_support (no auto-refund)
- [x] On sold out → `booking_failed_sold_out`
- [x] On timeout → retry with policy below, then `booking_failed_supplier_timeout`
- [x] **Retry policy:** max **3 attempts**, exponential backoff (**30s, 2min, 10min**)
- [x] After max retries: `booking_failed_supplier_timeout` + `needs_manual_support`
- [x] Each retry is a new outbox job (or scheduled next_run_at) — not blocking the worker forever
- [x] On other vendor errors → `booking_failed_supplier_error` / `unknown`
- [x] Call inventory.book on success path
- [x] Save supplier refs
- [x] Status confirmed or failed_* / needs_manual_support
- [x] Audit events written with failure_reason
- [x] Notify agent path (dashboard state; optional wa.me share helper)

### 21.2 Cancel
- [x] Cancel request endpoint (manual handling ok in V1)

### 21.3 Phase 21 exit
- [x] Mock path: pay → job → confirmed booking with fake PNR
- [x] Mock path: fare-change after pay sets correct failure_reason

**DONE when:** Fulfillment works asynchronously with diagnosable failures.

---

## PHASE 22 — Bookings & attention UI (frontend)

**Goal:** Agents see booking outcomes and problems.

### 22.1 Pages
- [x] Bookings list (filters)
- [ ] Booking detail (canonical: quote page `/app/quotes/[id]` — no separate booking detail route)
- [x] Home attention strip for pending_confirm / failed
- [ ] Customer timeline shows bookings (Deferred to Phase 25/Post-sale CRM)

### 22.2 UX
- [x] Status chips + transitions
- [x] Clear copy when needs_manual_support

### 22.3 Phase 22 exit
- [x] Agent can track a booking end-to-end in UI (list → quote detail)

**DONE when:** Ops visibility for agents exists.

---

## PHASE 23 — Audit log & honest failure states

**Goal:** Supportability for pilot.

### 23.1 Audit events
- [x] quote.sent, payment.captured, booking.confirmed, booking.failed, cancel.requested (Sprint J writers)
- [x] Admin/agent-safe readers as appropriate (`/quotes/{id}/audit`)

### 23.2 Failure taxonomy in UI + API
- [x] payment_received_booking_pending (home attention + public status)
- [x] needs_manual_support (derived on failed bookings + audit metadata; see `docs/failure-taxonomy.md`)
- [x] booking_failed_fare_changed
- [x] booking_failed_sold_out
- [x] booking_failed_supplier_timeout (show retryable)
- [x] booking_failed_supplier_error
- [x] booking_failed_missing_pax
- [x] booking_failed_unknown
- [x] fare_changed / expired quote (pre-pay)
- [x] payment_captured_quote_expired

### 23.3 Phase 23 exit
- [x] Can answer “what happened to this quote?” from audit + statuses + failure_reason (Sprint J)
- [x] Full event log exists for any quote transaction.

**DONE when:** Pilot support is possible without DB spelunking only.

---

## PHASE 24 — Admin OS (backend + frontend)

**Goal:** Platform operators run the pilot.

### 24.1 Backend
- [x] Agents list + approve/reject
- [x] Global bookings list
- [x] Failures queue (`/admin/dead-letters` → `JobStatus.dead`)
- [x] Payments overview
- [ ] Suppliers list (read/config basic) — deferred to Phase 36

### 24.2 Frontend `/admin`
- [x] Overview KPIs (simple counts ok)
- [x] Agents pages
- [x] Bookings + Failures pages
- [x] Payments page
- [ ] Suppliers page — deferred to Phase 36 (ComingSoon)

### 24.3 Access
- [x] Only platform admin role
- [x] Distinct AdminLayout chrome

### 24.4 Phase 24 exit
- [x] Admin can approve an agent and open a failed booking

**DONE when:** You/Nilesh can operate without SQL.

---

## PHASE 25 — First real supplier adapter (sandbox)

**Goal:** Replace mock for sandbox searches/books.

### 25.1 Adapter implementation
- [ ] TBO or TripJack client (current TBO is **simulated HTTP**, not live sandbox)
- [x] Mappers to NormalizedOffer
- [ ] Encrypted credentials stored (wiring incomplete for live)
- [x] Contract tests against mock
- [x] Error mapping (Sprint J)
- [ ] Test full lifecycle in sandbox: search → revalidate → book → get_status → cancel
- [ ] Document sandbox quirks / limitations with real sandbox evidence

### 25.2 Config
- [ ] Strategy `primary_only` → real supplier (still hardcodes mock + tbo)
- [x] Keep mock available for CI

### 25.3 Phase 25 exit
- [ ] Sandbox flight and/or hotel search returns real offers
- [ ] Sandbox book path **tested** and quirks documented

**DONE when:** Real inventory path exists.

---

## PHASE 26 — Full sandbox E2E hardening

**Goal:** Repeatable full loop without manual DB edits.

### 26.1 Scripted scenarios
- [ ] Search → quote (with pax) → wa.me mark sent → pay test → booking confirm
- [ ] Quote without pax → create-pay-link returns error (pax gate enforced)
- [ ] Duplicate webhook does not double-book
- [ ] Expired quote cannot create pay link
- [ ] Fare change blocks pay with refresh path
- [ ] Fare change **after** pay → correct failure_reason (not generic only)
- [ ] Late webhook after confirm → no-op
- [ ] Org A cannot see Org B data
- [ ] Rate limit 429 under hammered search

### 26.2 Performance sanity
- [ ] Search timeout behavior
- [ ] Webhook responds quickly (enqueue only)

### 26.3 Phase 26 exit
- [ ] Two clean E2E runs back-to-back recorded

**DONE when:** V1 functionally trustworthy in sandbox.

---

## PHASE 27 — Production-like deploy (Vercel + Render)

**Goal:** Hosted environments for pilot.

### 27.1 Render
- [x] API web service (Blueprint `render.yaml`)
- [x] Worker service (env parity with API)
- [x] Postgres
- [ ] Env vars set _(dashboard — after Blueprint)_
- [x] Migrations on deploy strategy
- [ ] Every Alembic migration has a working `downgrade()`
- [x] Document Render rollback (previous deploy) procedure
- [x] Confirm **automatic Postgres backups** enabled; note retention _(documented; verify on live DB)_
- [x] Document point-in-time / restore steps (Render docs link in runbook)

### 27.2 Vercel
- [ ] Web app deploy _(pending account)_
- [x] Env API URL (documented)
- [x] Preview vs production noted
- [x] Note **instant rollback** to previous Vercel deployment
- [ ] Frontend `/api/health` passes against prod API

### 27.3 Upstash
- [x] **Skip for V1 default** (DB-poll worker); Redis in Blueprint unused by app — reserved only

### 27.4 Domains & CORS
- [ ] Production web URL allowlisted on API
- [ ] Public quote URLs correct in messages
- [ ] Auth BFF/cookie strategy verified on real domains (not only localhost)

### 27.5 Observability (pilot minimum)
- [x] Sentry DSN wiring for API + worker (set value in hosted env)
- [x] Capture hooks: dead jobs + webhook signature failures
- [ ] Alerts configured in Sentry UI
- [x] Optional: log drain noted (Vercel runbook)

### 27.6 Phase 27 exit
- [ ] Hosted E2E smoke test passes
- [ ] Backup setting confirmed; restore procedure written
- [ ] Rollback procedures written for Render + Vercel

**DONE when:** Pilot can use non-localhost URLs with basic ops visibility.

---

## PHASE 28 — Security, tenancy, reliability gate

**Goal:** Pre-pilot hardening gate.

### 28.1 Security
- [ ] Secrets not in repo
- [ ] Supplier creds encrypted
- [ ] Webhook signatures verified
- [ ] JWT/cookie/BFF flags correct for HTTPS
- [ ] Admin routes locked
- [ ] Public quote tokens not enumerable

### 28.2 Tenancy
- [ ] Automated tests for cross-org isolation

### 28.3 Reliability
- [x] Outbox dead-letter visible in Admin
- [ ] Sentry hooked and alert smoke-tested _(code ready; hosted DSN pending)_
- [x] Runbook: payment captured but booking failed (by failure_reason)
- [x] **Backup restore dry-run** deferred ≤1 week after first hosted deploy (documented in Phase 28 checklist)

### 28.4 Phase 28 exit
- [ ] Checklist signed off by Farhan (+ Nilesh for commercial)

**DONE when:** Safe to invite real agents.

---

## PHASE 29 — Pilot onboarding (5–10 agents)

**Goal:** Real usage with Nilesh’s network.

### 29.1 Prep
- [ ] Shortlist 5–10 agents (Nilesh) — tracker ready in `docs/pilot-onboarding-tracker.md`
- [x] Approval workflow practiced (Admin approve/reject → `inactive`)
- [x] Support channel norms documented (`docs/pilot-support-channel.md`) — create WA group when demos start
- [x] Create 1-page quick-start (`docs/agent-quickstart.md`)
- [ ] Record 3–5 min screen recording walkthrough (optional; script in `pilot-demo-script.md`)
- [ ] Schedule live demo with first 3 agents (Nilesh + Farhan)
- [x] Training outline: Search → Quote → wa.me → Pay (`pilot-demo-script.md`)

### 29.2 Watch
- [ ] Sit with 2–3 agents on first bookings
- [x] Friction log template ready (tracker §2) — fill during pilot
- [ ] Track transacting agents weekly

### 29.3 Phase 29 exit
- [ ] ≥3 agents completed ≥1 real paid booking (stretch: 5–10)

**DONE when:** Real GMV exists; feedback list captured.

---

## PHASE 30 — V1.5 friction fixes

**Goal:** Fix only what pilot proved necessary.

### 30.1 Candidate fixes (build only if needed)
- [ ] Offline mark-as-paid + audit
- [ ] Re-quote / refresh expired quote
- [ ] Needs-attention queue polish
- [ ] CSV export bookings
- [ ] WhatsApp message presets
- [ ] Customer phone dedup/merge
- [ ] Password reset flow

### 30.2 Process
- [ ] Rank frictions by booking blockers vs nice-to-have
- [ ] Ship blockers only

### 30.3 Phase 30 exit
- [ ] Top blockers from pilot closed

**DONE when:** Agents book without you pushing every step.

---

## PHASE 31 — V1 Exit Gate (go / no-go for V2)

**Goal:** Decide whether to expand scope.

### 31.1 Metrics review
- [ ] Monthly Active Transacting Agents count
- [ ] GMV / agent
- [ ] Booking failure rate
- [ ] Support load qualitative

### 31.2 Go criteria (suggested)
- [ ] Core loop used without constant hand-holding
- [ ] No critical money/booking integrity bugs open
- [ ] At least target pilot size met or consciously waived by founders

### 31.3 Decision
- [ ] **GO V2** or **FIX V1 longer** written decision

### 31.4 Phase 31 exit
- [ ] Decision recorded; V2 phases unlocked only on GO

**DONE when:** Scope discipline preserved.

---

## PHASE 32 — V2 Packages

**Goal:** Admin-curated packages agents resell as quotes.

### 32.1 Backend
- [ ] packages, package_items, versioning
- [ ] Publish → creates/pre-fills quote via Quotes module
- [ ] Still backed by real inventory rules where required

### 32.2 Frontend
- [ ] Admin package editor
- [ ] Agent package browse + send

### 32.3 Phase 32 exit
- [ ] One live package sold/sent through normal quote→pay path

**DONE when:** Packages are quotes under the hood.

---

## PHASE 33 — V2 Commission & Wallet

**Goal:** Replace spreadsheet commissions.

### 33.1 Backend
- [ ] Commission calculator uses **stored** supplier_cost / agent_markup / platform_fee (not inverted formula)
- [ ] agent_commission rule per Phase 0 commercial decision
- [ ] Wallet ledger (pending/available/paid)
- [ ] Admin owed view
- [ ] Platform fee vs agent markup distinction in UI/API

### 33.2 Frontend
- [ ] Agent wallet page
- [ ] Admin commissions page
- [ ] Statement export (basic)

### 33.3 Phase 33 exit
- [ ] Ledger reconciles to sample bookings using correct formula

**DONE when:** Money owed is visible and auditable.

---

## PHASE 34 — V2 Follow-ups & document vault

**Goal:** Recover unpaid quotes; store tickets/vouchers.

### 34.1 Follow-ups
- [ ] 24h / 48h detector jobs
- [ ] Agent nudge inbox
- [ ] Snooze
- [ ] Optional wa.me reminder builder

### 34.2 Documents
- [ ] S3/R2 storage integration
- [ ] Attach ticket/voucher/invoice to booking
- [ ] Re-share via wa.me helper

### 34.3 Phase 34 exit
- [ ] Unpaid quote generates nudge; booking has attachable doc

**DONE when:** Retention + fulfillment docs exist.

---

## PHASE 35 — V2 AI Copilot

**Goal:** NL → real search → draft quote (no invented prices).

### 35.1 Service (`apps/ai` — **Farhan only**)
- [ ] `POST /ai/v1/parse-intent`
- [ ] `POST /ai/v1/format-quote-draft`
- [ ] Eval set of agent phrases (collect phrasing examples via Nilesh’s agents)
- [ ] Tests: never invent prices; offer IDs subset check
- [ ] Deploy AI service (e.g. Render)
- [ ] LLM provider key owned by Farhan/product

### 35.2 Main API gateway (**Farhan**)
- [ ] Feature flag `AI_COPILOT_ENABLED`
- [ ] parse → Inventory.search → format draft orchestration
- [ ] Auth to AI service

### 35.3 Frontend (**Farhan**)
- [ ] `/app/ai` page
- [ ] Prefill quote builder from draft
- [ ] Agent always reviews before send

### 35.4 Phase 35 exit
- [ ] Pilot agents use AI draft on real search results at least once successfully

**Detail ref:** `tripos-ai-spec.md`  

**DONE when:** AI is a UX layer over Inventory, not a side brain. **Owner: Farhan only.**

---

## PHASE 36 — V3 Multi-supplier strategies

**Goal:** Resilience beyond one supplier.

### 36.1 Platform
- [ ] Second adapter live
- [ ] Strategy config: failover → preference
- [ ] Per-booking store supplier_code + refs
- [ ] Circuit breaker / kill switch per supplier
- [ ] Admin supplier strategy UI

### 36.2 Optional later
- [ ] merge_dedupe search (only after failover stable)

### 36.3 Phase 36 exit
- [ ] Kill primary supplier in staging → failover still returns offers

**DONE when:** Inventory strategy is config-driven.

---

## PHASE 7 — Setup & Config

### 7.1 Setup & Config
- [x] Tailwind CSS + standard colors (brand_primary, etc.)
- [x] `shadcn/ui` initialized (install Button, Input, Card)
- [x] Redux Toolkit + RTK Query (boilerplate store setup, empty `apiSlice`)
- [x] NextAuth.js or custom AuthProvider (must support cross-domain BFF strategy)

### 7.2 Core Layouts
- [x] `/login` (public layout)
- [x] `/(dashboard)` (protected layout with Sidebar + Header)
  - Sidebar links: Dashboard, CRM, Quotes, Bookings, Settings

### 7.3 Phase 7 exit
- [x] `npm run dev` works
- [x] Can view Login page (no logic yet)
- [x] Can view Dashboard shell (static)

---

## PHASE 37 — V3 White-label

**Goal:** Agency-branded customer surface.

### 37.1 Backend
- [ ] organization domains table
- [ ] Domain → org resolution
- [ ] Theme payload API

### 37.2 Frontend
- [ ] Public layout theming (logo, colors)
- [ ] Custom domain on Vercel (or proxy)
- [ ] Optional public lead form → CRM
- [ ] Minimize TripOS branding for WL tenants

### 37.3 Phase 37 exit
- [ ] One agency domain serves branded quote + pay status

**DONE when:** White-label is presentation over same engine.

---

## PHASE 38 — V3 Distributor hierarchy

**Goal:** Master → sub-agents with scoped data & commission split.

### 38.1 Backend
- [ ] Activate parent_organization_id tree logic
- [ ] Permission scoping for sub-agents
- [ ] Commission waterfall rules
- [ ] RBAC roles extended

### 38.2 Frontend
- [ ] Admin distributor tree
- [ ] Sub-agent limited nav/data
- [ ] Master sees network aggregates

### 38.3 Phase 38 exit
- [ ] Sub-agent cannot read sibling data; commission split visible

**DONE when:** Indian distribution structure supported.

---

## PHASE 39 — Scale, observability, ops maturity

**Goal:** Run at higher volume without heroics.

### 39.1 Observability
- [ ] Structured logs everywhere critical
- [ ] Metrics: search latency, book success rate, webhook failures
- [ ] Alerting on dead-letter spike

### 39.2 Performance
- [ ] DB indexes reviewed
- [ ] Search cache tuned
- [ ] Worker concurrency tuned

### 39.3 Ops
- [ ] Runbooks for refunds, failed books, supplier outage
- [ ] Backup/restore tested for Postgres

### 39.4 Phase 39 exit
- [ ] On-call style checklist exists for Nilesh/Farhan

**DONE when:** Platform is operable at growth.

---

## PHASE 40 — Continuous backlog & quarterly review

**Goal:** Controlled evolution; no random scope.

### 40.1 Cadence
- [ ] Monthly: transacting agents + GMV review
- [ ] Quarterly: enhancements accept/park from `tripos-enhancements.md`
- [ ] Revisit AI heavy-ML track only with data

### 40.2 Backlog hygiene
- [ ] Every new idea tagged V1.5 / V2 / V3 / Park
- [ ] No feature enters build without phase assignment

### 40.3 Phase 40 ongoing checklist (repeat)
- [ ] Update master plan checkboxes for newly accepted work
- [ ] Keep docs index accurate when stack decisions change

**DONE when:** Process is perpetual (this phase never “ends”).

---

# PART D — CROSS-CUTTING CHECKLISTS (APPLY ACROSS PHASES)

## D1. Every backend module must include
- [ ] router / schemas / models / repository / service pattern
- [ ] Org scoping
- [ ] Tests for happy path + authz denial
- [ ] No direct supplier HTTP outside adapters

## D2. Every Agent OS page must include
- [ ] Loading skeleton
- [ ] Empty state with CTA
- [ ] Error + retry
- [ ] Token colors only
- [ ] Page-enter motion (or reduced-motion fallback)

## D3. Money integrity
- [ ] Idempotent payment create
- [ ] Idempotent webhook
- [ ] Single booking per paid quote
- [ ] Audit on pay and book

## D4. Secrets
- [ ] `.env` never committed
- [ ] Production secrets only in Vercel/Render/Upstash dashboards
- [ ] Credential packs stored securely offline/shared vault

## D5. Every Public customer page must include
- [ ] No agent cost / supplier cost / internal IDs visible
- [ ] Works without login (token-only access)
- [ ] Mobile-first layout with sticky Pay CTA
- [ ] Graceful expired/invalid token handling (not raw 404/stack)
- [ ] Agency brand_name displayed if set
- [ ] OG tags for WhatsApp preview where applicable

---

# PART E — PARALLEL TRACK NOTES

| Track | Can parallelize with | Notes |
|---|---|---|
| Sahil credentials | Phases 1–10 | Needed before Phase 25 |
| **Nilesh commercial answers (0.2)** | **Phases 1–10** | **Blocking for Phase 14 (pricing/platform_fee) and Phase 18 (payment merchant)** |
| AI service build (Farhan) | Phases 11–31 optional prototype | Fixtures only until Phase 35; Sahil/Nilesh not on this track |
| Nilesh pilot list | Phases 20–28 | Ready for Phase 29 |
| Frontend design system | Backend auth/schema | Phases 7–8 \|\| 3–6 |

---

# PART F — DEFINITION OF COMPLETE PROJECT (MACRO)

TripOS is “complete” for a mature V3 platform when:

- [ ] Phases 0–31 done (solid V1 + pilot proof)
- [ ] Phases 32–35 done (V2 stickiness)
- [ ] Phases 36–38 done (platform scale features)
- [ ] Phase 39 ops maturity acceptable
- [ ] Phase 40 process running

V1 product launch to agents requires **through Phase 29 minimum** (ideally 28+29), not V3.

---

# PART G — QUICK DAILY STANDUP PROMPT

1. Which **phase number** are we on?  
2. Which **sub-phase** checkboxes closed yesterday?  
3. What is blocked (credentials, commercial, supplier sandbox)?  
4. Are we accidentally building V2/V3 early?  

---

# PART H — DOCUMENT CHANGE LOG (maintain manually)

| Date | Change | Who |
|---|---|---|
| 2026-09-16 | Master plan + docs index created from all planning docs | Farhan / Cursor assist |
| 2026-09-16 | FINAL: AI owned by Farhan only; Sahil/Nilesh = APIs/creds only; `tripos-ai-spec.md` replaces Sahil AI handoff | Farhan |
| 2026-09-16 | Applied `tripos_plan_review.md` (18 issues + enhancements A–E) into master/implementation/modules docs | Farhan |
| 2026-09-16 | Applied `master_plan_suggested_changes.md` (14 items): DB-poll outbox, quote rules, retries, session restore, weeks, etc. | Farhan |
| 2026-09-16 | **Phase 0 STARTED** — decisions log + commercial checklist + credential templates + `secrets/` gitignore | Farhan |

---

**End of Master Plan.**  
**Start execution at Phase 0.**  
**When in doubt, open `tripos-docs-index.md`, then the detail doc for the current phase.**
