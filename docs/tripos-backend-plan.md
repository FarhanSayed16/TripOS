# TripOS — Complete Backend Plan

### Structure, modules, services, and responsibilities — **no code**

**Stack lock:** FastAPI modular monolith · PostgreSQL · SQLAlchemy + Alembic · Celery (when needed) · Upstash Redis (when needed) · Resend · Razorpay · wa.me messaging · Render hosting  

**Companions:** `tripos-implementation-plan.md` · `tripos-modules-and-flow.md` · `tripos-enhancements.md`

**Purpose of this document:** Exact backend layout — folders, modules, what each service does, what each layer owns, build order. Use this as the blueprint when creating files. No source code here.

---

## 1. Backend shape (one sentence)

One **modular monolith** on Render: HTTP API + optional background worker sharing the same domain modules. External travel APIs sit behind an **adapter registry**. AI (if/when built) is a **separate service** called only from an orchestration layer — never mixed into payments/bookings.

---

## 2. Top-level backend layout

```text
apps/api/
├── README.md                          # How to run API locally / on Render
├── pyproject.toml / requirements      # Dependencies
├── Dockerfile                         # API image
├── alembic/                           # Migrations
│   ├── versions/                      # One migration file per schema change
│   └── env settings                   # Alembic runtime config
├── app/
│   ├── main                           # App factory, router mount, lifespan
│   ├── core/                          # Cross-cutting platform (not business features)
│   ├── modules/                       # Business feature modules (see §4)
│   ├── adapters/                      # Supplier/partner plugins (or symlink to /adapters)
│   ├── jobs/                          # Background task definitions
│   └── integrations/                  # Non-supplier third parties (Resend, Razorpay SDK wrappers)
└── tests/
    ├── unit/
    ├── integration/
    ├── contract/                      # Adapter contract tests
    └── fixtures/                      # Sample offers, webhooks, intents

apps/worker/                           # Same codebase entrypoint for Celery/Render worker
apps/ai/                               # Optional V2 — separate process (even if you own it)
```

> **V1 execution note (2026-09-16):** Scaffolding uses a **flat** `app/api` + `app/schemas` + `app/models` layout.  
> See `docs/architecture/v1-api-layout.md` — `modules/*` remains the target for large domains; do not big-bang refactor before Phase 11+.

---

## 3. Layer rules (how responsibilities split)

| Layer | Lives in | Allowed to | Forbidden to |
|---|---|---|---|
| **Routes / Controllers** | `modules/*/router` | Validate input, call one service, return response | Call suppliers, run SQL, business rules |
| **Schemas / DTOs** | `modules/*/schemas` | Request/response shapes | Hide vendor payloads from clients |
| **Services** | `modules/*/service` | Business logic, orchestration, status transitions | Raw HTTP to TBO/etc. (use Inventory) |
| **Repositories** | `modules/*/repository` | DB read/write for that module’s tables | Call external APIs |
| **Models** | `modules/*/models` or shared `db/models` | Table mapping | Business workflows |
| **Adapters** | `adapters/*` | Talk to one external supplier | Know about quotes/payments/UI |
| **Jobs** | `jobs/` | Retryable side effects | Long sync HTTP in request thread when avoidable |
| **Core** | `core/` | Auth helpers, config, errors, db session | Feature-specific rules |

**Golden rules**
1. Every business row is scoped by `organization_id` (except global admin/supplier config).
2. Only **Inventory** talks to the adapter registry.
3. Money changes go through **Payments** + idempotency.
4. Booking confirm runs as a **job** after payment, not inside the webhook request body work beyond verify + enqueue.

---

## 4. `app/core/` — platform foundation

| File / unit | Purpose |
|---|---|
| **config** | Env settings: DB, Redis, Resend, Razorpay, JWT, feature flags, AI URL |
| **db** | Engine, session factory, base model |
| **redis** | Upstash client (optional until caching/queues needed) |
| **security** | Password hashing, JWT issue/verify, current-user dependency |
| **permissions** | Role checks: `agent`, `admin` (later `ops`, `sub_agent`) |
| **errors** | Standard error types + HTTP mapping |
| **logging** | Request ID, org ID, structured logs |
| **idempotency** | Idempotency-key store/helpers for pay/book |
| **encryption** | Encrypt/decrypt supplier credentials at rest |
| **pagination** | Shared list pagination helpers |
| **feature_flags** | e.g. `AI_COPILOT_ENABLED`, `OFFLINE_PAYMENT_ENABLED` |

---

## 5. Feature modules (complete division)

Each module folder contains the same internal headings (even if some start empty):

```text
modules/<name>/
├── router          # HTTP endpoints for this feature
├── schemas         # In/out contracts for frontend
├── models          # Tables this module owns (or imports)
├── repository      # DB access
├── service         # Business logic
├── constants       # Status enums, limits
├── events          # Optional: domain events emitted (quote.sent, payment.captured)
└── dependencies    # Module-specific FastAPI deps
```

---

### 5.1 Auth module — `modules/auth` (V1)

**Purpose:** Identity, login, verification, tokens.

| Service / concern | Responsibility |
|---|---|
| Signup service | Register user + create/join organization skeleton |
| Login service | Email/password → tokens |
| Verification service | Send verify email via **Resend**; mark email verified |
| Token service | Access + refresh JWT lifecycle |
| Password service | Hash, reset request (optional V1.5), change password |
| Session service | Optional refresh-token persistence / revoke |

**Endpoints (logical):** signup · login · refresh · logout · verify-email · me  

**Depends on:** Organizations (create org on signup), Resend integration  

**Does not own:** Roles inside org (Organization Members), supplier auth  

---

### 5.2 Organizations module — `modules/organizations` (V1, hooks for V3)

**Purpose:** Agency tenancy and branding fields.

| Service / concern | Responsibility |
|---|---|
| Organization service | CRUD profile: name, phone, license/KYC fields, status |
| Membership service | Add member, list members, assign role (`agent` / `admin`) |
| Branding service | Read/update `slug`, `brand_name`, `logo_url`, `colors` (used lightly in V1 quotes; full white-label in V3) |
| Hierarchy stub | Store nullable `parent_organization_id` — **no hierarchy logic until V3** |

**Data owned:** organizations, organization_members  

**Exposes:** “current org context” used by every other module  

---

### 5.3 CRM module — `modules/crm` (V1)

**Purpose:** Customers per organization.

| Service / concern | Responsibility |
|---|---|
| Customer service | Create / update / search by name or phone |
| Customer history service | Aggregate quotes + bookings + payments for one customer |
| Dedup helper | Soft-unique phone per org; merge later (V1.5) |

**Data owned:** customers (notes table in V2)  

**Used by:** Quotes, Messaging, Bookings  

---

### 5.4 Inventory module — `modules/inventory` (V1 — critical)

**Purpose:** Only gateway to all travel supplier APIs. Orchestrates search, revalidate, book, cancel, status.

| Service / concern | Responsibility |
|---|---|
| Adapter registry | Map `supplier_code` → adapter implementation |
| Search service | Flight/hotel search → normalized offers; optional Redis cache |
| Revalidate service | Re-price/lock offer before pay and before book |
| Fulfillment service | create_booking / cancel / get_status via adapter |
| Strategy service | V1: `primary_only`; V3: failover / preference / merge |
| Offer snapshot service | Persist immutable offer snapshot for quote lines |
| Supplier admin service | Enable supplier, store encrypted credentials, rate limits |

**Subfolders / units inside inventory:**
- `products/flights` — flight search request shaping  
- `products/hotels` — hotel search request shaping  
- `normalization` — map adapter output → NormalizedOffer  
- `errors` — map vendor errors → TripOS errors  

**Data owned:** suppliers, supplier_credentials, supplier_configs, search_requests, offer_snapshots  

**Used by:** Quotes, Bookings, Packages (V2), AI orchestration (V2)  

**Never used by:** Frontend calling TBO directly  

---

### 5.5 Quotes module — `modules/quotes` (V1)

**Purpose:** Turn selected offers + margin into a customer quote with lifecycle.

| Service / concern | Responsibility |
|---|---|
| Quote builder | Create draft from selected offer snapshots + markup |
| Pricing service | Compute agent_cost, markup, customer_total (never leak cost on public quote) |
| Pax service | Attach passengers/guests before send/pay (per product rules) |
| Expiry service | Set `valid_until`; mark expired via job |
| Quote status service | draft → ready → sent → paid → expired / cancelled |
| Public quote service | Tokenized public view payload for hosted quote page |
| Send orchestration | Mark sent + call Messaging for wa.me payload (does not send itself) |
| Refresh / clone | V1.5: re-search and clone quote |

**Data owned:** quotes, quote_items, passengers (or shared passenger tables)  

**Depends on:** Inventory (snapshots/revalidate), CRM, Messaging, Payments  

---

### 5.6 Payments module — `modules/payments` (V1)

**Purpose:** Collect money; tell the system when paid. Never store cards.

| Service / concern | Responsibility |
|---|---|
| Payment link service | Create Razorpay link for quote amount |
| Webhook service | Verify signature, idempotent capture handling |
| Reconciliation service | Link gateway payment ↔ quote ↔ booking intent |
| Refund service | V1: manual/admin initiate; auto later |
| Offline payment service | V1.5: mark paid outside gateway + audit |

**Data owned:** payments, refunds  

**On success:** enqueue booking confirmation job (outbox)  

**Depends on:** Quotes; Razorpay integration wrapper  

---

### 5.7 Bookings module — `modules/bookings` (V1)

**Purpose:** Lifecycle after payment: confirm with supplier, track, cancel.

| Service / concern | Responsibility |
|---|---|
| Confirm service | Job: revalidate → inventory.book → persist refs |
| Status service | pending_confirm → confirmed / failed / needs_manual_support |
| Cancel service | Soft cancel + supplier cancel if supported; else manual flag |
| Booking query service | List/filter by org, customer, status |
| Attention queue | Paid-but-not-confirmed, failures (V1.5) |

**Data owned:** bookings, booking_passengers  

**Depends on:** Inventory, Payments, Quotes, Audit, Messaging (notify agent)  

---

### 5.8 Messaging module — `modules/messaging` (V1)

**Purpose:** Build and log customer outreach. V1 = wa.me only.

| Service / concern | Responsibility |
|---|---|
| Message builder | Compose quote summary + public quote URL + pay URL |
| wa.me link service | Build deep link for customer phone + prefilled text |
| Message log service | Store outbound intent/content against customer + quote |
| Confirmation share helper | Optional second wa.me after booking confirm |
| Provider swap port | Interface so V2/V3 can add Cloud API without touching Quotes |

**Data owned:** messages  

**Does not:** Auto-send via Meta in V1; no inbound webhook handling in V1  

---

### 5.9 Admin module — `modules/admin` (V1 → grows)

**Purpose:** Platform operator (you / Nilesh) views — not the agent’s daily UI.

| Service / concern | Responsibility |
|---|---|
| Agent approval service | pending_approval → active / rejected |
| Agent directory | List orgs/users, activity, last booking |
| Global bookings view | Cross-org booking list + failure filters |
| Revenue snapshot | Basic GMV / paid counts (simple in V1) |
| Manual support actions | Flag booking, trigger refund initiate, resend instructions |

**Depends on:** reads Organizations, Bookings, Payments, Quotes — owns little new data  

---

### 5.10 Audit module — `modules/audit` (V1)

**Purpose:** Append-only trail for support and disputes.

| Service / concern | Responsibility |
|---|---|
| Audit writer | Record: quote.sent, payment.captured, booking.confirmed/failed, cancel.requested |
| Audit reader | Filter by org, quote, booking, time |

**Data owned:** audit_events  

---

### 5.11 Jobs / Outbox — `modules/outbox` + `app/jobs` (V1)

**Purpose:** Reliable async work.

| Service / concern | Responsibility |
|---|---|
| Outbox writer | Persist intended job: confirm_booking, expire_quotes, send_email |
| Outbox dispatcher | Worker picks pending jobs, retries, dead-letters |
| Job handlers | One handler per job type calling the right module service |

**Job catalog (V1)**
- Expire quotes  
- Confirm booking after payment  
- Send verification email (or sync via Resend if simple)  
- (Later) Follow-up nudges, commission calc  

**Data owned:** jobs_outbox  

---

### 5.12 Commissions module — `modules/commissions` (V2)

| Service | Responsibility |
|---|---|
| Commission calculator | On confirmed booking → compute amounts |
| Wallet ledger | Pending / available / paid out |
| Statements | Monthly summary for agent/admin |

**Scaffold empty in V1; do not implement logic early.**

---

### 5.13 Packages module — `modules/packages` (V2)

| Service | Responsibility |
|---|---|
| Package admin | Create versioned packages from real inventory building blocks |
| Package publish | Agent browse + “send as quote” → Quotes module |

---

### 5.14 Follow-ups module — `modules/followups` (V2)

| Service | Responsibility |
|---|---|
| Detector job | Quotes sent unpaid after 24h/48h |
| Nudge service | Notify agent; optional wa.me reminder builder |
| Snooze | Agent dismiss/snooze |

---

### 5.15 AI orchestration module — `modules/ai_gateway` (V2)

**Purpose:** Thin BFF inside main API — **not** the LLM brain.

| Service | Responsibility |
|---|---|
| Parse proxy | Forward text to AI service `/parse-intent` |
| Draft flow | parse → Inventory.search → `/format-quote-draft` → return to UI |
| Feature flag gate | Disabled until ready |

**FINAL:** Farhan owns AI. Implement LLM logic in `apps/ai`; keep this gateway thin.

---

### 5.16 Branding / White-label module — `modules/branding` (V3)

| Service | Responsibility |
|---|---|
| Domain mapping | Custom domain → organization |
| Theme resolution | Logo/colors for public quote & pay success pages |
| Public lead intake | Optional lead form → CRM |

Uses org branding fields already present from V1.

---

### 5.17 Distributors module — `modules/distributors` (V3)

| Service | Responsibility |
|---|---|
| Org tree | Master → sub-agents |
| Scope enforcement | Sub sees only own data |
| Commission waterfall | Split rules |

Uses `parent_organization_id` stub from V1.

---

## 6. Adapters layer — `app/adapters/` (or `/adapters`)

```text
adapters/
├── base                    # Shared adapter interface / capability flags
├── registry                # Register and resolve adapters
├── mock                    # Fake flights/hotels for local + CI
├── tbo/                    # First real supplier (example)
│   ├── adapter
│   ├── client              # HTTP to vendor
│   ├── mappers             # Vendor ↔ normalized
│   └── errors
├── tripjack/               # Alternate / second supplier
└── _template/              # Copy for the 300–500 API journey
```

| Unit | Responsibility |
|---|---|
| **Interface** | capabilities, search, revalidate, book, cancel, status, map_error |
| **Per-vendor client** | Auth, timeouts, rate limit respect |
| **Mappers** | Only place vendor JSON is understood |
| **Mock** | Unblocks frontend and quote/payment flows without live keys |

**Rule:** Adding a new hotel/client API = new adapter folder + registry entry + DB supplier row — **not** a new module in Quotes/Payments.

---

## 7. Integrations layer — `app/integrations/` (non-travel)

| Integration | Responsibility |
|---|---|
| **resend** | Send verification (and later transactional) emails |
| **razorpay** | Create payment links; verify webhooks |
| **upstash_redis** | Cache / broker helpers when enabled |
| **s3** (later) | Tickets, logos, invoices |
| **ai_client** | HTTP client to `apps/ai` |

Keep SDKs here so feature modules stay clean.

---

## 8. Background worker plan — `apps/worker` + `app/jobs`

| Heading | Contents |
|---|---|
| Worker entry | Starts Celery/compatible consumer on Render |
| Task registration | Maps outbox job types → handlers |
| Schedules | Beat/cron: expire quotes; V2 follow-ups |
| Retry policy | Backoff, max attempts, dead-letter status |
| Alerting | Log + Sentry on permanent failure |

**V1 minimum jobs:** quote expiry · booking confirm after pay  

---

## 9. Database plan (owned by Alembic)

### Migration strategy
- One migration per meaningful change  
- Never edit applied migrations  
- Seed script: mock supplier, platform admin user  

### Table groups (by owning module)

| Group | Tables |
|---|---|
| Auth / Org | users, organizations, organization_members, email_verifications, refresh_tokens (if any) |
| CRM | customers |
| Inventory | suppliers, supplier_credentials, supplier_configs, search_requests, offer_snapshots |
| Quotes | quotes, quote_items, quote_passengers |
| Payments | payments, refunds |
| Bookings | bookings, booking_passengers |
| Messaging | messages |
| Platform | audit_events, jobs_outbox |
| V2 | packages*, commissions*, wallets*, wallet_ledger*, follow_up_tasks*, documents* |
| V3 | organization_domains, commission_rules, … |

### Status machines to document in constants
- Quote · Payment · Booking · Organization · Outbox job  

---

## 10. HTTP API map (backend surface only)

Group routers by module; version prefix `/api/v1`.

| Router group | Main resources |
|---|---|
| Auth | signup, login, refresh, verify, me |
| Organizations | current org, members, branding fields |
| CRM | customers CRUD, customer timeline |
| Inventory | search flights, search hotels, revalidate |
| Quotes | create, get, list, attach pax, prepare send, public token get |
| Payments | create-link, webhook, (admin refund) |
| Bookings | get, list, cancel request |
| Messaging | build wa.me for quote (or nested under quotes/send) |
| Admin | agents approve/list, bookings, failures |
| Public | public quote by token (limited fields) |
| AI gateway | V2 only, feature-flagged |
| Health | health, readiness |

**Public vs private:** public quote + payment webhook are special-cased (no agent JWT; webhook uses signature).

---

## 11. Cross-cutting implementation checklist

| Concern | Where handled |
|---|---|
| Multi-tenancy filter | Core dependency + every repository |
| Authn | Auth module + core security |
| **Cross-domain auth (Vercel↔Render)** | Default: **Next.js BFF/proxy** + `Authorization: Bearer` access token; refresh via HttpOnly cookie usable from BFF. Alternative: shared parent domain cookies (`Domain=.tripos.in; SameSite=None; Secure`). See implementation plan §0.1 |
| Authz | permissions (agent vs admin) |
| Idempotency | Payments + Bookings + core helper |
| Fare freshness | Inventory.revalidate before pay link and before book |
| **Pax before pay** | Quotes gate: no payment link without required pax |
| **Price columns** | quote_items: supplier_cost, agent_markup, platform_fee, customer_total |
| **Booking failure_reason** | Explicit codes (fare_changed, sold_out, timeout, …) |
| Phone E.164 | CRM normalize; Messaging wa.me uses digits |
| Public quote token | Cryptographically random; not enumerable |
| Secrets | config + encryption for supplier creds |
| Observability | core logging + Sentry (+ optional log drain in pilot) |
| Feature flags | core config |
| Rate limits | Inventory: 30/min/org in-memory (Upstash later); respect supplier Retry-After |
| Search result cap | Max 50 offers; FE shows 20 + load more |
| CORS | main app (allowlist exact Vercel origins incl. previews as needed) |
| Webhook late arrivals | Idempotent; expired+paid → needs_manual_support, no silent book |

---

## 12. Build order for backend (execution sequence)

### Phase B1 — Skeleton
1. App factory + config + DB + Alembic  
2. Core security + error handling  
3. Organizations + Auth + Resend verify  
4. Health endpoints  
5. Deploy API to Render  

### Phase B2 — Inventory bones
1. Adapter interface + registry + **Mock adapter**  
2. Search + revalidate services  
3. Supplier tables + encrypted credentials  
4. Normalized offer snapshots  

### Phase B3 — Commercial loop
1. CRM  
2. Quotes + public quote  
3. Messaging wa.me + message log  
4. Payments + webhook + outbox  
5. Bookings confirm job  
6. Audit + Admin lists  

### Phase B4 — First real adapter
1. TBO or TripJack adapter  
2. Switch strategy `primary_only` to real supplier in sandbox  
3. Contract tests  

### Phase B5 — V2 backends (after pilot)
1. Commissions / packages / follow-ups modules  
2. AI gateway + `apps/ai` (**Farhan**)  
3. Documents storage integration  

### Phase B6 — V3 backends
1. Branding/domains  
2. Distributor tree + RBAC  
3. Multi-adapter strategies  

---

## 13. Testing plan (backend)

| Type | What |
|---|---|
| Unit | Pricing, status transitions, wa.me message builder |
| Integration | Quote → pay webhook → outbox → booking confirm (mock adapter) |
| Contract | Every adapter satisfies interface |
| Security | Org A cannot read Org B data |
| Webhook | Replay / duplicate payment does not double-book |
| Idempotency | Same key → same payment result |

---

## 14. Environment & config headings

| Config group | Examples |
|---|---|
| App | ENV, DEBUG, API_URL, PUBLIC_WEB_URL (Vercel) |
| Database | DATABASE_URL |
| Redis | UPSTASH_REDIS_URL (optional) |
| Auth | JWT secrets, token TTLs |
| Resend | API key, from-email |
| Razorpay | key, secret, webhook secret |
| Suppliers | which primary code; creds in DB not env when possible |
| AI | AI_SERVICE_URL, AI_SERVICE_KEY, AI_COPILOT_ENABLED |
| Feature flags | offline pay, AI, etc. |

---

## 15. What “backend done for V1” means

- [ ] Auth + email verify + org membership works  
- [ ] Mock search → quote → wa.me payload → payment link → webhook → booking confirm  
- [ ] Real supplier adapter works in sandbox for flights and/or hotels  
- [ ] Failures surface as `needs_manual_support` / `booking_failed`  
- [ ] Admin can list agents and problem bookings  
- [ ] Audit log covers send / pay / book  
- [ ] No vendor API calls outside adapters  
- [ ] Deployed on Render with Postgres; Upstash only if actually used  

---

## 16. Document map

| Doc | Role |
|---|---|
| `tripos-docs-index.md` | Map of all docs + locked stack |
| `tripos-master-plan.md` | 40-phase execution checklist |
| `tripos-implementation-plan.md` | Full product + stack + locked decisions §0.1 |
| `tripos-modules-and-flow.md` | Product module meanings + flows |
| `tripos-frontend-plan.md` | Pages, design, motion |
| **`tripos-backend-plan.md` (this file)** | **Backend folders, services, ownership, build order — no code** |
| `tripos-ai-spec.md` | Farhan-owned AI contract |
| `tripos_plan_review.md` | Review findings (applied 2026-09-16) |

---

**Principle:** Features live in **modules**. Vendors live in **adapters**. Money and booking state machines stay strict. Everything else (AI, white-label, hierarchy) plugs into this skeleton without rewriting it.
