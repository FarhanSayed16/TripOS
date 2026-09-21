# TripOS — Full Implementation Plan (V1 → V2 → V3)

### How we build it so the foundation stays correct when scale arrives

**Companions:** `tripos-plan.md` · `tripos-modules-and-flow.md` · `tripos-work-division.md` · `tripos-enhancements.md`

**Purpose:** One execution document that covers:
1. Broader product picture across **Version 1 / 2 / 3**
2. **Technical stack** (locked for build)
3. **Backend & system design** that stays healthy when you integrate **many external APIs** (hundreds of hotels / suppliers / partners — not “hack one TBO client and rewrite later”)
4. **How we implement** — modules, contracts, data model, jobs, security
5. **Phased execution** — what ships when, without breaking earlier versions

**North-star constraint:** Ship a real agent booking loop in V1, but design the *internals* as if multi-supplier, multi-tenant, and high integration count are inevitable.

---

## 0. One-page summary

| Layer | Decision |
|---|---|
| Product | B2B Travel Agent Operating System (not a consumer OTA) |
| V1 | Auth → Search → Quote → WhatsApp → Pay → Book → CRM (+ admin) |
| V2 | AI copilot, packages, wallet/commission, follow-ups, ops hardening |
| V3 | Multi-supplier mesh, white-label, distributor hierarchy, scale |
| App shape | **Modular monolith** (FastAPI) + Next.js; extract services only when proven |
| Integration shape | **Supplier / Partner Adapter Platform** — every external API is a plugin behind one contract |
| Source of truth for price | Supplier APIs only (AI never invents availability/price) |
| Success metric | Monthly Active Transacting Agents (real paid bookings) |

---

## 0.1 Locked product/tech decisions (from plan review — FINAL)

These resolve cross-doc contradictions. **Do not re-open during V1 build.**

### Passenger data timing (Issue 2)
**Decision: Option A — collect passenger/guest details BEFORE payment link creation.**  
- Flights: all required pax fields must be on the quote before `create payment link` and before mark-sent is allowed if pay link already exists.  
- Hotels: primary guest name minimum before pay link.  
- Public quote page: customer does **not** enter pax in V1 (agent-only).  
- Booking job: if pax missing despite paid → `booking_failed_missing_pax` + manual support (should be rare if gates enforced).  
- Status machine stays `draft → ready → sent → paid → expired/cancelled`; “pax complete” is a **gate on ready/pay**, not a separate status.

### Pricing amounts on every quote_item (Issue 3)
Store from V1 day one (even though wallet logic is V2):

```text
customer_total = supplier_cost + agent_markup + platform_fee
```

- `supplier_cost` — what TripOS/agent pays the supplier (internal)  
- `agent_markup` — agent’s commercial add-on  
- `platform_fee` — TripOS cut (may be 0 in pilot; still store the column)  
- `customer_total` — what customer pays  

**Never use** `supplier_payout − customer_price` for commission.  
Phase 0 must record: platform fee rule (flat / % / per product / zero for pilot).

### Booking failure sub-reasons (Issue 4)
After payment captured, booking confirm job sets a **failure_reason** (not only a generic needs_manual_support):

| Code | Meaning | Typical action |
|---|---|---|
| `booking_failed_fare_changed` | Revalidate price changed | Agent/admin: approve delta, re-quote, or refund |
| `booking_failed_sold_out` | Offer gone | Prefer refund / re-shop |
| `booking_failed_supplier_timeout` | Timeout | Auto-retry then escalate |
| `booking_failed_supplier_error` | Mapped vendor error | Investigate + manual |
| `booking_failed_missing_pax` | Gate bug / incomplete data | Fix pax then retry book |
| `booking_failed_unknown` | Unclassified | Manual |

Plus status: `needs_manual_support` when human action required. **No auto-refund in V1** without human decision.

### Cross-domain auth Vercel ↔ Render (Issue 5)
**Default for V1:**  
1. Access token via `Authorization: Bearer` (memory / short-lived; not localStorage long-term if avoidable).  
2. Refresh token in **HttpOnly Secure cookie** on the **API domain**, used only by a **Next.js BFF/proxy** route (`/api/proxy/...` or Route Handlers) so the browser talks same-origin to Vercel.  
3. CORS allowlists exact web origins (prod + preview as needed).  

**Alternative (if single parent domain):** `app.` + `api.` under `tripos.in` with cookie `Domain=.tripos.in; SameSite=None; Secure` — document if chosen instead of BFF.

### Auth method V1 (Issue 8)
**Email + password + Resend email verification only.** No phone OTP in V1.

### Quote expiry default (Issue 12)
- Default `valid_until` = **4 hours** from creation (org-configurable later).  
- Agent may extend up to **24 hours** with fare-risk warning.  
- Revalidate still mandatory before pay link and before book.

### Search rate limits V1 (Issue 10)
- Default: **30 searches / minute / organization** (tune later).  
- In-memory token bucket for pilot; Upstash Redis when shared across instances.  
- Respect supplier `Retry-After` / rate-limit headers in adapters.

### Search result limits (Enhancement E)
- Backend returns max **50** normalized offers per search (configurable), pre-sorted by price ascending unless agent chooses time.  
- Frontend: show first page of **20**, “Load more” client-side within the 50.

### Phone normalization (Enhancement C)
- Store E.164 (e.g. `919876543210` for India).  
- Normalize on CRM create/update; wa.me uses digits-only international form.

### Public quote tokens (Enhancement D)
- Cryptographically random token (UUID v4 or 32+ byte url-safe secret).  
- Must not embed quote id / org id.  
- Lookup by token only; respect quote expiry.

### Webhook late/retry rules (Enhancement B)
- Razorpay may retry ~24h: handlers stay idempotent.  
- If quote already `paid` + booking exists → ack and no-op.  
- If quote `expired` but payment captured → mark `needs_manual_support` + `payment_captured_quote_expired`; **no silent book**.  
- If booking already `failed_*` and new webhook duplicate → no-op.

---

## 1. Broader picture: what each version really means

Think in **capabilities of the platform**, not just feature lists.

```text
V1  =  “One reliable money loop + correct system bones”
V2  =  “Make agents faster and stickier on the same bones”
V3  =  “Open the platform to many suppliers, many brands, many org levels”
```

### 1.1 Version 1 — Core Operating Loop + Solid Bones

**Business outcome:** 5–20 agents complete real paid bookings without Excel + manual WhatsApp chaos.

**Product capabilities:**
- Organization + user auth (agent / admin)
- Customer CRM (basic)
- Flight + hotel search & book via **one live supplier**, through the **adapter platform**
- Quotation (margin, expiry, hosted link)
- WhatsApp share via **wa.me** deep links (agent opens WhatsApp with prefilled quote + pay URL; Business API later)
- Payments (link + webhook)
- Booking confirm pipeline (async, idempotent)
- Admin visibility (agents, bookings, failures)
- Audit log + honest failure states

**System bones that must exist in V1 (even if only 1 supplier is live):**
- Normalized domain models (Offer, Quote, Booking, Payment, Message)
- Supplier adapter interface + registry
- Credential vault pattern
- Job/outbox for async side effects
- Idempotency keys on payments & bookings
- Multi-tenant data scoping by `organization_id`
- Schema hooks for brand + parent org (unused logic)

**Explicitly not V1:** AI quoting, packages UI, wallet payouts, white-label domains, sub-agents, 2nd supplier merge logic, inbound WhatsApp bots.

---

### 1.2 Version 2 — Speed, Money Ops, Retention

**Business outcome:** Agents prefer TripOS daily; commissions are visible; unpaid quotes get followed up; packages reduce quote time.

**Product capabilities:**
- AI Copilot (intent parse + draft format over **real** search)
- Admin-curated holiday packages
- Commission engine + agent wallet ledger
- Follow-up automation (24h / 48h)
- Document vault (tickets/vouchers/invoices) + re-send on WhatsApp
- Stronger ops: needs-attention queue, CSV exports, offline-paid marking
- Optional PWA polish for agents

**System upgrades:**
- Separate **AI service** with frozen HTTP contract
- Ledger tables for wallet (double-entry friendly)
- Package versioning
- Quote analytics (sent / viewed / paid) if hosted quote supports view pixels

---

### 1.3 Version 3 — Platform Scale

**Business outcome:** Larger agencies and networks run on TripOS; inventory is resilient; brands look independent.

**Product capabilities:**
- **Many supplier/partner adapters** (flights, hotels, activities, transfers, insurance, etc.)
- Search strategies: failover → weighted preference → merge/dedupe
- White-label: custom domain, branding, optional public lead page
- Distributor hierarchy: master → sub-agents, scoped permissions, commission waterfall
- Second+ payment/WhatsApp providers if needed
- Multi-language customer messaging (Hindi/Marathi first)

**System upgrades:**
- Adapter SDK + CI certification for new integrations
- Per-supplier circuit breakers, rate limits, SLAs
- Tenant branding service / config
- Org tree + RBAC matrix
- Optional split of Search/Booking workers if volume demands

---

## 2. The 300–500 APIs problem — how we design for it now

You will not integrate 300–500 APIs in V1. You **will** hit that scale over years if TripOS becomes the agent OS across hotels, flights, packages, add-ons, and regional suppliers.

### 2.1 What “300–500 APIs” means in practice

Not 300–500 random HTTP calls inside the agent dashboard. It means **hundreds of external systems**, for example:
- Aggregators (TBO, TripJack, …)
- Direct hotel chains / CRS
- Bedbanks / DMC APIs
- Activity / transfer / visa / insurance partners
- Per-client private APIs (a large agency’s own rate sheet API)
- Regional GDS / low-cost carrier connectors

Each external system has different auth, payloads, error codes, and booking lifecycles. If application code talks to them directly, the product dies under integration debt.

### 2.2 Solution: Supplier / Partner Adapter Platform

**Rule (non-negotiable):**  
Application modules (Search, Quote, Booking, AI, Packages) **never** call a vendor SDK or raw HTTP client for a specific supplier. They only call the **TripOS Inventory & Fulfillment API** (internal), which dispatches to adapters.

```text
┌─────────────────────────────────────────────────────────────┐
│  Product modules (Auth, CRM, Quotes, Payments, WhatsApp…)   │
└────────────────────────────┬────────────────────────────────┘
                             │ internal domain commands
                             ▼
┌─────────────────────────────────────────────────────────────┐
│           Inventory & Fulfillment Layer (core)              │
│  search / revalidate / book / cancel / status / map errors  │
└────────────────────────────┬────────────────────────────────┘
                             │ Adapter Registry
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   Adapter: TBO        Adapter: TripJack   Adapter: HotelX …
   Adapter: DirectH    Adapter: Insurance  Adapter: ClientAPI_N
         │                   │                   │
         ▼                   ▼                   ▼
   External APIs         External APIs       External APIs
```

### 2.3 Adapter contract (canonical — freeze in V1)

Every adapter implements the same capability interface (methods may no-op with `NotSupported` if the vendor lacks that product):

| Capability | Purpose |
|---|---|
| `capabilities()` | Declares: flights? hotels? packages? cancel? sync? async book? |
| `search(request) -> list[NormalizedOffer]` | Search inventory |
| `revalidate(offer_ref) -> NormalizedOffer \| FareChanged` | Lock/check price before pay/confirm |
| `book(request) -> BookingResult` | Create supplier booking |
| `cancel(booking_ref) -> CancelResult` | Cancel if supported |
| `get_status(booking_ref) -> StatusResult` | Poll / fetch status |
| `map_error(raw) -> TripOSError` | Normalize vendor errors |

**Normalized objects (examples):**
- `NormalizedOffer` — product_type, price breakdown, currency, expires_at, supplier_code, supplier_offer_ref, raw_payload_ref (stored, not leaked to UI)
- `BookingResult` — supplier_booking_ref, tickets/vouchers metadata, status

### 2.4 Adapter packaging model (so 500 integrations don’t explode the monolith)

| Phase | How adapters live |
|---|---|
| **V1** | In-repo packages: `adapters/tbo/`, `adapters/tripjack/` behind registry |
| **V2** | Adapter SDK (`tripos-adapter-sdk`) + checklist + contract tests |
| **V3** | Adapters as installable plugins (same process first; separate workers later if needed). Each adapter versioned; registry maps `supplier_code → adapter_version` |

**Per supplier config (DB, not code):**
- credentials (encrypted)
- rate limits
- timeout / retry policy
- enabled products
- commercial metadata (margin rules hints — optional)
- environment (`sandbox` / `production`)

### 2.5 Search strategies (evolve, don’t rewrite)

| Strategy | Phase | Behavior |
|---|---|---|
| `primary_only` | V1 | One active supplier |
| `failover` | V3 early | If primary errors/timeout → secondary |
| `preference` | V3 | Route by product/city/airline preference table |
| `merge_dedupe` | V3 late | Parallel search, normalize, dedupe, rank — hardest |

**V1 implements `primary_only` on top of the same registry** so switching strategy later is config, not a rewrite.

### 2.6 What we store vs what we call live

- **Never** treat cached search results as bookable forever.
- Cache search for UX speed (Redis, short TTL).
- Always **`revalidate`** before creating payment link and again before supplier `book` (see enhancements).
- Store opaque `supplier_offer_ref` + snapshot of priced offer on the quote line item.

---

## 3. Technical stack (locked — team decision)

### 3.1 Application stack

| Layer | Choice | Why |
|---|---|---|
| Agent + Admin UI | **Next.js (App Router) + TypeScript** | Fast UI, SSR for hosted quote pages, one frontend codebase |
| Frontend hosting | **Vercel** | Native Next.js deploy, previews, CDN for quote pages |
| API / Domain | **FastAPI + Python 3.12+** | Team familiarity; great for integrations & jobs |
| Backend hosting | **Render** | API + worker services; Postgres add-on if used |
| ORM / migrations | **SQLAlchemy 2.x + Alembic** | One schema owner next to FastAPI |
| DB | **PostgreSQL 16** (Render Postgres or equivalent) | Relational integrity for money/bookings |
| Cache / Redis | **Upstash Redis** (when required) | Serverless Redis; search cache, rate limits, locks, Celery broker if needed |
| Queue / workers | **Celery** on Render worker (broker via Upstash Redis) *or* lightweight in-process/RQ if traffic is tiny at pilot | Payment webhooks, booking confirm, expiry jobs |
| Email / verification | **Resend** | Signup / login verification emails (and later transactional mail) |
| Object storage | **S3-compatible** (AWS S3 / Cloudflare R2) when needed | Tickets, invoices, logos (V2+) |
| Auth | **JWT access + refresh** (HttpOnly cookies preferred) + argon2 passwords; **email verification via Resend** | Simple V1 |
| Payments | **Razorpay** (primary candidate) or PayU | Indian agent market |
| WhatsApp (V1) | **wa.me links** | Generate `https://wa.me/<phone>?text=...` with quote + pay URL; agent taps “Send on WhatsApp” — no Cloud API in V1 |
| WhatsApp (later) | Meta Cloud API / Interakt / AiSensy | Automated send + templates when volume justifies it |
| AI (V2) | Separate **FastAPI AI service**; LLM via provider API (OpenAI / Gemini / etc.) | Keeps core booking logic clean |
| Observability | Structured logs (JSON) + **Sentry** + OpenTelemetry later | Pilot debugging |
| CI | GitHub Actions | lint, test, migrate checks |

### 3.2 Hosting path (locked for V1)

| Component | Where |
|---|---|
| Frontend (`apps/web`) | **Vercel** |
| Backend API (`apps/api`) | **Render** (web service) |
| Background worker | **Render** (background worker) when Celery/jobs are needed |
| PostgreSQL | **Render Postgres** (or external managed PG pointed at by Render) |
| Redis | **Upstash** — add when caching / queues / rate limits are required (not mandatory on day 1) |
| Email | **Resend** |
| Later scale (V3) | Can migrate API/workers to AWS/GCP if needed; keep Vercel for frontend if it still fits |

### 3.2.1 WhatsApp V1 behavior (wa.me)

```text
Agent clicks "Send on WhatsApp"
  → Backend builds prefilled message (quote summary + hosted quote URL + payment URL)
  → Backend returns wa.me deep link for customer's phone
  → Frontend opens link (agent’s WhatsApp)
  → Agent hits send (human-in-the-loop)
  → System marks quote as "sent" and logs the intended message text
```

**Not in V1:** server-side auto-send, Meta template approval, inbound WhatsApp webhooks.  
**Upgrade path:** swap Messaging module implementation to Cloud API later without changing Quote/Payment modules.

### 3.3 Repo structure (monorepo recommended)

```text
tripos/
  apps/
    web/                 # Next.js (agent, admin, public quote pages)
    api/                 # FastAPI modular monolith
    worker/              # Celery worker entry (can share api package)
    ai/                  # V2 AI service (stub folder from day one optional)
  packages/
    domain/              # shared types/DTOs if needed
    adapter-sdk/         # V2+ ; thin Protocol in api for V1
  adapters/
    tbo/
    tripjack/
    _template/           # copy-paste skeleton for new supplier
  docs/                  # already exists
  docker-compose.yml     # postgres, redis, mailhog/local stubs
```

### 3.4 Modular monolith layout (inside `apps/api`)

```text
api/
  app/
    main.py
    core/           # config, security, db, redis, errors
    modules/
      auth/
      organizations/
      crm/
      inventory/    # search/revalidate orchestration + registry
      quotes/
      payments/
      bookings/
      messaging/    # WhatsApp
      admin/
      audit/
      commissions/  # mostly empty until V2
      packages/     # mostly empty until V2
    jobs/           # celery tasks
  adapters/         # or import from /adapters
  tests/
```

**Module rule:** each module owns its routes, schemas, services, repository. Cross-module calls go through **service interfaces**, not random DB grabs.

---

## 4. Domain model (foundation tables)

Design these in V1 even if some columns are unused.

### 4.1 Tenancy & identity
- `organizations` — agency; fields: `slug`, `brand_name`, `logo_url`, `primary_color`, `parent_organization_id` (nullable), `status`
- `users` — login identity
- `organization_members` — user ↔ org + role (`agent`, `admin`; later `ops`, `sub_agent`)
- `sessions` / refresh tokens if needed

### 4.2 CRM
- `customers` — unique `(organization_id, phone)` soft-unique
- customer notes (V2)

### 4.3 Inventory platform
- `suppliers` — code, name, type, status
- `supplier_credentials` — encrypted secrets, env
- `supplier_configs` — rate limit, strategy weights, enabled products
- `search_requests` — audit of what was searched
- `offer_snapshots` — priced offers attached to quotes (immutable snapshot)

### 4.4 Commercial loop
- `quotes`, `quote_items` — status, `valid_until`, customer totals, agent cost (internal), markup
- `passengers` / `booking_passengers`
- `payments`, `refunds` — idempotency keys, gateway refs
- `bookings` — status machine, `supplier_code`, `supplier_booking_ref`
- `messages` — WhatsApp outbound log
- `audit_events`
- `jobs_outbox` — durable async work

### 4.5 V2 tables (create when building V2, design names now)
- `packages`, `package_items`, `package_versions`
- `commissions`, `wallets`, `wallet_ledger_entries`
- `follow_up_tasks`
- `documents`

### 4.6 V3 tables
- `organization_branding_domains`
- `commission_rules` (waterfall)
- `supplier_route_preferences`
- RBAC permissions if roles explode

### 4.7 Status machines (implement explicitly)

**Quote:** `draft → ready → sent → paid → expired → cancelled`  
**Payment:** `created → pending → captured → failed → refunded`  
**Booking:** `pending_payment → pending_confirm → confirmed → failed → cancelled → needs_manual_support`

---

## 5. End-to-end implementation flows (canonical)

### 5.1 V1 happy path

```text
Agent auth
  → CRM: select/create customer
  → Inventory.search (adapter)
  → Agent selects offers + markup
  → Collect pax (flights) / guest (hotels)
  → Inventory.revalidate
  → Create quote (snapshot offers, valid_until)
  → Create payment link
  → Build wa.me link (summary + quote URL + pay URL) → agent sends in WhatsApp
  → Customer pays
  → Webhook (verify) → outbox job
  → Inventory.revalidate again → Inventory.book
  → Persist booking refs → CRM history
  → Agent notified in dashboard; optional wa.me “share confirmation” link (auto Cloud API later)
```

### 5.2 Failure path (must be first-class)

```text
Pay captured BUT book fails
  → booking = needs_manual_support / failed
  → notify agent + admin
  → do NOT auto-refund in V1 without human decision
  → audit everything
```

### 5.3 V2 AI path

```text
NL text → AI.parse_intent
  → Inventory.search (real)
  → AI.format_quote_draft
  → Agent edits → rejoins V1 quote send flow
```

### 5.4 V3 multi-supplier search

```text
Inventory.search
  → strategy selects adapters
  → parallel/failover calls
  → normalize → (optional dedupe/rank)
  → return NormalizedOffer[]
```

---

## 6. API surface strategy (your own APIs vs external APIs)

There are **two different “API counts”** — don’t confuse them:

| Kind | What | How we manage |
|---|---|---|
| **A. TripOS public/internal HTTP APIs** | Endpoints your frontend and webhooks call | Versioned REST under `/api/v1/...`; keep V1 list small and stable |
| **B. External partner APIs** | TBO, hotels, etc. (path to 300–500) | Hidden behind adapters; never exposed 1:1 to frontend |

### 6.1 TripOS API modules (grow by version)

**V1 (illustrative groups, not 500 routes):**
- `/auth/*`
- `/orgs/*` (current org profile)
- `/customers/*`
- `/inventory/search/flights|hotels`
- `/inventory/revalidate`
- `/quotes/*` (+ `/send`)
- `/payments/create-link`, `/payments/webhook`
- `/bookings/*`
- `/admin/*`
- `/public/quotes/{token}` (hosted quote page data)

**V2 adds:** `/packages/*`, `/wallet/*`, `/ai/*` (or BFF to AI service), `/follow-ups/*`, `/documents/*`  
**V3 adds:** `/branding/*`, `/distributors/*`, admin supplier strategy configs

**Design rule:** Frontend talks only to TripOS APIs with **normalized JSON**. Vendor payloads stay server-side.

### 6.2 Idempotency & safety on TripOS APIs
- `Idempotency-Key` header on payment create + booking confirm jobs
- Webhook signature verification mandatory
- All mutating routes scoped by org membership
- Admin routes separate permission check

---

## 7. Cross-cutting platform requirements (build into V1 bones)

| Concern | V1 implementation |
|---|---|
| Multi-tenancy | Every business row has `organization_id`; queries always filtered |
| Security | Secrets in env / secret manager; supplier creds encrypted at rest |
| Jobs | Outbox row + Celery consumer; retries with backoff; dead-letter status |
| Caching | Redis TTL cache for search; never cache “book” |
| Rate limits | Per org + per supplier |
| Observability | `request_id`, `organization_id`, `supplier_code` on logs |
| Testing | Contract tests for adapter interface + golden booking flow tests with fake adapter |
| Fake adapter | `adapters/mock/` for local/dev/CI without vendor credentials |

**Critical:** Implement a **MockSupplierAdapter** in week 1 so frontend and quote/payment flows can be built before live TBO credentials arrive.

---

## 8. Versioned delivery plan (execution)

### Phase A — Foundation (Weeks 1–2) → still V1

**Goals:** repo, environments, auth, schema, adapter skeleton, mock supplier.

| Work | Owner (default) |
|---|---|
| Monorepo + docker-compose (Postgres, Redis) | Farhan |
| DB schema v1 + migrations | Farhan |
| Auth + org + member roles | Farhan |
| Adapter Protocol + Registry + Mock adapter | Farhan |
| Celery + outbox skeleton | Farhan |
| Next.js app shell (agent + admin layouts) | Farhan |
| Secure supplier credential storage design | Farhan |
| Source sandbox creds (TBO/TripJack, Razorpay); Resend API key; Upstash if needed | Sahil / Farhan |
| Confirm commercials / money flow / invoice party | Nilesh |

**Exit criteria:** Agent can log in; create customer; run mock flight/hotel search; see normalized results in UI.

---

### Phase B — Inventory + Quotes (Weeks 3–6) → V1

| Work | Notes |
|---|---|
| First real adapter (TBO **or** TripJack) | Flights + hotels if both available |
| `revalidate` wired | Before quote finalize |
| Quotation engine | Markup, expiry, snapshots, pax capture |
| Hosted public quote page | Link-first |
| CRM list/history hooks | Quote tied to customer |

**Exit criteria:** Agent creates a real (or sandbox) quote with live/sandbox supplier offers and opens hosted link.

---

### Phase C — Money + Messaging + Booking (Weeks 7–8) → V1

| Work | Notes |
|---|---|
| Razorpay payment links | + webhook verify + idempotency |
| Booking worker | revalidate → book → status updates |
| wa.me share links | Prefill quote + pay; log message; mark quote sent |
| Resend verification emails | Signup / verify flows |
| Failure states + admin lists | needs_manual_support visible |
| Audit events | pay/book/send |

**Exit criteria:** Sandbox end-to-end: search → quote → wa.me share → pay webhook → booking confirm → message log entry.

---

### Phase D — Pilot harden (Weeks 9–12) → V1 complete / V1.5 start

| Work | Notes |
|---|---|
| Onboard 5–10 agents | Nilesh network |
| Fix friction only | No V2 features |
| Offline-paid mark, re-quote, CSV if demanded | V1.5 |
| Watch: booking failures, fare changes, message delivery | |

**Exit criteria:** Real paid bookings; metric dashboard for active transacting agents.

---

### Phase E — V2 (Months 4–6)

Order (do not parallelize everything):
1. Document vault + re-send  
2. Commission + wallet ledger  
3. Packages  
4. Follow-up jobs  
5. AI service (`parse-intent`, `format-quote-draft`) + UI entry point  
6. Adapter SDK + second adapter *only if* commercially required earlier than V3  

**Exit criteria:** AI drafts used by agents; commissions visible; packages selling.

---

### Phase F — V3 (Months 7–12+)

1. Supplier strategy config (`failover` → `preference`)  
2. N additional adapters (prioritize by GMV / Nilesh supply deals)  
3. White-label domains + branding on quote/pay pages  
4. Distributor hierarchy + RBAC + commission waterfall  
5. Merge/dedupe search only after failover is stable  
6. Scale workers / DB as metrics demand  

**Exit criteria:** Multi-supplier resilience; at least one white-label tenant; one master/sub-agent network live.

---

## 9. Work division (implementation-aligned)

| Area | Farhan | Sahil | Nilesh |
|---|---|---|---|
| Product UI + FastAPI modules | Owns | — | Feedback |
| Adapter platform + first adapters | Owns | Docs/creds handoff | Commercial terms |
| Payments + wa.me messaging + Resend | Owns | Razorpay/supplier creds; Cloud API later if needed | Policy copy |
| AI service | **Owns fully** (prompts, service, UI wiring) | — | Agent phrase examples only |
| External API access (300–500 journey) | Integrates via SDK | Sources contracts/creds, maintains partner list | Supplier relationships |
| Pilot agents / licensing | Supports | — | Owns |
| White-label / hierarchy (V3) | Owns build | — | Defines org/commercial rules |

**Sahil during V1:** credentials + documentation packs per partner only (auth method, sandboxes, rate limits, booking quirks). **No AI build.** Farhan may optionally prototype AI alone against Mock adapter without blocking V1.

---

## 10. Adding a new external API (repeatable playbook)

This is how you get toward hundreds of integrations without chaos:

1. **Commercial intake** (Nilesh/Sahil): products covered, margins, settlement, cancel rules  
2. **Tech intake** (Sahil → Farhan): OpenAPI/docs, auth, sandbox, sample book/cancel  
3. **Scaffold** from `adapters/_template`  
4. **Map** to NormalizedOffer / book/cancel  
5. **Contract tests** + sandbox certification checklist  
6. **Register** supplier in DB; store encrypted creds  
7. **Enable** for `primary_only` or strategy weights  
8. **Monitor** error rate / latency for 2 weeks before wide enable  

**Never** add a one-off route in the frontend for a new hotel API.

---

## 11. Quality gates (definition of done)

### V1 done when:
- [ ] Mock + one real adapter pass contract tests  
- [ ] Full sandbox loop works twice in a row without manual DB edits  
- [ ] Webhook retries do not double-book  
- [ ] Fare-change path is handled (block pay or refresh quote)  
- [ ] Org scoping verified (agent A cannot see agent B’s customers)  
- [ ] Pilot: ≥1 real booking from ≥3 agents (stretch: 5–10 agents active)

### V2 done when:
- [ ] AI never returns prices except from Inventory results  
- [ ] Wallet ledger balances reconcile to bookings  
- [ ] Package send creates a normal quote under the hood  

### V3 done when:
- [ ] Failover search works with supplier kill-switch  
- [ ] One white-label domain serves branded quote/pay  
- [ ] Sub-agent cannot read master sibling data  

---

## 12. Risk register (implementation-focused)

| Risk | Mitigation |
|---|---|
| Vendor API chaos / poor docs | Mock adapter + contract tests; certify sandbox before prod |
| Stale fares | Mandatory revalidate; quote expiry |
| Webhook double processing | Idempotency keys + unique payment refs |
| Integration explosion | Adapter platform + playbook; refuse bespoke UI integrations |
| Farhan bottleneck | Sahil/Nilesh supply API creds only; Farhan owns AI too — keep V1 scope ruthless; AI waits for Phase 35 |
| Money / refund disputes | Manual refund V1; clear `needs_manual_support` queue |
| Premature microservices | Stay modular monolith until a module has independent scale pain |

---

## 13. Immediate next actions (this week)

1. **Team review** this document + vote critical enhancement items in `tripos-enhancements.md`  
2. **Nilesh:** money flow (who is Razorpay merchant), invoice party, first supplier choice  
3. **Sahil:** sandbox credential pack for supplier #1 + Razorpay (WhatsApp Business API deferred; V1 uses wa.me)  
4. **Farhan:** initialize monorepo, docker-compose, schema migration 001, Mock adapter, auth + Resend; deploy web→Vercel, api→Render; add Upstash when Redis is needed  

---

## 14. Document map

| Doc | Role |
|---|---|
| `tripos-plan.md` | Vision, GTM, business model |
| `tripos-modules-and-flow.md` | Module responsibilities & flows |
| `tripos-work-division.md` | People ownership |
| `tripos-enhancements.md` | Ideas backlog & priorities |
| **`tripos-implementation-plan.md` (this file)** | **How we build it — stack, architecture for many APIs, phased execution** |

---

**Final principle:**  
*Product features version up (V1→V2→V3). The adapter platform, tenancy model, money state machines, and job/idempotency design do not get reinvented each version — they only grow.*
