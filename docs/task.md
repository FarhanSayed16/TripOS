# TripOS — Phases 31–40 Complete Implementation Task List

> **Purpose:** This document is the single source of truth for building Phases 31–40. Each task is implementation-ready with exact file paths, model schemas, API contracts, and frontend specifications. An AI coding assistant should be able to execute each task without needing to ask clarifying questions.

> **Codebase context:** Phases 1–30 are complete. The existing stack is:
> - **Backend:** FastAPI + SQLAlchemy (async) + PostgreSQL + Alembic migrations + `structlog` + Sentry
> - **Frontend:** Next.js 14 (App Router) + TypeScript + Redux Toolkit / RTK Query + shadcn/ui + Tailwind CSS
> - **Worker:** `worker.py` — DB outbox poller with `SKIP LOCKED`, backoff schedule, dead-letter to Sentry
> - **Adapters:** `BaseAdapter` → `MockAdapter` (live) + `TboAdapter` (simulated)
> - **Patterns:** `require_active_org` dependency for org scoping, `write_audit()` for all mutations, `AppError` for domain errors, `PaginatedResponse` for lists
> - **Deploy:** `render.yaml` (API + Worker + Redis + Postgres), Vercel for frontend, Sentry for errors

---

## Existing Architecture Reference

```
apps/api/
├── main.py                          # FastAPI app factory
├── worker.py                        # Outbox poller (poll_outbox, reclaim_stale, expire_quotes)
├── app/
│   ├── api/                         # Route files (auth, customers, quotes, bookings, admin, public, webhooks, payments, inventory, organizations, health)
│   ├── adapters/                    # base.py, mock_adapter.py, tbo_adapter.py, registry.py
│   ├── core/                        # config.py, security.py, exceptions.py, middleware.py, rate_limit.py, encryption.py, inventory_errors.py
│   ├── db/                          # session.py
│   ├── models/                      # base.py, tenancy.py, crm.py, commercial.py, inventory.py, enums.py
│   ├── schemas/                     # auth.py, crm.py, quotes.py, payments.py, bookings.py, inventory.py
│   ├── services/                    # audit.py, bookings.py, email.py, inventory.py, jobs.py, messaging.py, messaging_provider.py, payments.py, quotes.py
│   └── utils/                       # pagination.py
├── alembic/                         # Migration files
└── tests/e2e/                       # conftest.py, helpers.py, test_e2e_*.py

apps/web/
├── src/
│   ├── app/
│   │   ├── (agent)/app/             # Agent dashboard pages (home, customers, quotes, bookings, search, settings)
│   │   ├── (admin)/admin/           # Admin pages (dashboard, orgs, bookings, failures, suppliers)
│   │   ├── (auth)/                  # login, signup, verify, forgot-password, reset-password
│   │   ├── (public)/               # Public marketing pages
│   │   └── q/[token]/              # Public quote page
│   ├── lib/
│   │   ├── apiSlice.ts             # RTK Query base with auto-refresh
│   │   ├── api/                    # inventoryApi, quotesApi, customersApi, bookingsApi, adminApi, organizationsApi
│   │   ├── store.ts
│   │   └── quoteSlice.ts           # Quote builder state
│   └── components/                 # Reusable UI components (shadcn/ui based)
```

### Key Enums (existing in `app/models/enums.py`)
```python
QuoteStatus:    draft | ready | sent | paid | expired | superseded | cancelled
PaymentStatus:  pending | captured | failed
BookingStatus:  pending | confirmed | failed | cancelled
BookingFailureReason: fare_changed | sold_out | supplier_timeout | supplier_error | missing_pax | unknown
JobStatus:      pending | running | done | dead
OrgStatus:      pending_approval | active | inactive
UserRole:       agent | admin
```

### Key Config Settings (existing in `app/core/config.py`)
```python
AI_COPILOT_ENABLED: bool = False
PAYMENTS_MODE: str = "mock"      # mock | razorpay
INVENTORY_SUPPLIERS: str = "mock_supplier"
PLATFORM_FEE_PAISE: int = 0
```

---

# PHASE 31 — V1 Exit Gate (go/no-go for V2)

**Goal:** Data-driven decision on whether V1 is stable enough to begin V2 features.

**This phase is NOT a coding phase.** It's a metrics review + decision gate. However, we need to build the tooling to measure.

## Tasks

### 31.1 — Build Admin Analytics Dashboard
- `[ ]` **Backend:** Create `GET /api/v1/admin/analytics` (platform_admin only)
  - **File:** `apps/api/app/api/admin.py` — add new route
  - **Returns:**
    ```json
    {
      "active_orgs": 5,
      "total_quotes": 142,
      "total_bookings": 38,
      "confirmed_bookings": 29,
      "failed_bookings": 9,
      "booking_failure_rate": 0.237,
      "total_gmv_paise": 4250000,
      "monthly_active_transacting_agents": 3,
      "avg_gmv_per_agent_paise": 1416667,
      "dead_letter_jobs": 2
    }
  - **Logic:** Query `Booking` (JOIN `Quote` for org + amounts), `Organization` (active count), `JobOutbox` (dead count). Use `func.count`, `func.sum`.
  - **Scoping:** Requires `require_platform_admin`. Aggregates across ALL orgs.
  - **Time filters:** Accept `?days=30` query param (default 30).

- `[ ]` **Frontend:** Create `/admin/analytics` page
  - **File:** `apps/web/src/app/(admin)/admin/analytics/page.tsx`
  - **Components:** Stat cards (Active Agents, GMV, Failure Rate, Dead Letters) using shadcn Card
  - **RTK Query:** Add `getAnalytics` endpoint to `adminApi.ts`
  - **Design:** Use existing admin layout. Grid of 4-6 stat cards. Color-code failure rate (green < 10%, yellow 10-25%, red > 25%)

### 31.2 — V1 Exit Decision Document
- `[ ]` **Create:** `docs/v1-exit-decision.md`
  - Template with sections: Metrics Summary, Go Criteria Assessment, Decision, Next Steps
  - Farhan fills in after reviewing analytics dashboard
  - **Gate:** Must record "GO V2" or "FIX V1 LONGER" before unlocking Phase 32+

### 31.3 — Phase 31 Exit
- `[ ]` Analytics endpoint returns real data
- `[ ]` Admin analytics page renders stat cards
- `[ ]` Decision document created with explicit GO/NO-GO

---

# PHASE 32 — V2 Packages

**Goal:** Admin creates curated travel packages. Agents browse and instantly convert a package into a pre-filled quote for a customer.

## Tasks

### 32.1 — Database Models & Migration

- `[ ]` **Create models** in `apps/api/app/models/packages.py`:
  ```python
  class Package(Base, TimestampMixin, SoftDeleteMixin):
      __tablename__ = "packages"
      organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
      created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
      title: Mapped[str] = mapped_column(String(255))
      description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
      destination: Mapped[str] = mapped_column(String(100))
      duration_days: Mapped[int] = mapped_column(Integer)
      base_price_paise: Mapped[int] = mapped_column(Integer)  # suggested customer price
      status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | published | archived
      cover_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
      metadata_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
      # Relationships
      items: Mapped[List["PackageItem"]] = relationship(back_populates="package", cascade="all, delete-orphan")

  class PackageItem(Base, TimestampMixin):
      __tablename__ = "package_items"
      package_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("packages.id", ondelete="CASCADE"), index=True)
      type: Mapped[str] = mapped_column(String(20))  # flight | hotel | activity | transfer
      title: Mapped[str] = mapped_column(String(255))
      description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
      estimated_cost_paise: Mapped[int] = mapped_column(Integer)
      supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
      search_params: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # pre-fill search for this item
      sort_order: Mapped[int] = mapped_column(Integer, default=0)
      # Relationships
      package: Mapped["Package"] = relationship(back_populates="items")
  ```

- `[ ]` **Register models** in `apps/api/app/models/__init__.py`
- `[ ]` **Create Alembic migration:** `alembic revision --autogenerate -m "add_packages_tables"`
- `[ ]` **Add PackageStatus enum** to `enums.py`:
  ```python
  class PackageStatus(str, enum.Enum):
      draft = "draft"
      published = "published"
      archived = "archived"
  ```

### 32.2 — Backend Schemas

- `[ ]` **Create** `apps/api/app/schemas/packages.py`:
  ```python
  class PackageItemCreate(BaseModel):
      type: str  # flight | hotel | activity | transfer
      title: str
      description: Optional[str] = None
      estimated_cost_paise: int
      supplier_code: Optional[str] = None
      search_params: Optional[dict] = None
      sort_order: int = 0

  class PackageCreate(BaseModel):
      title: str
      description: Optional[str] = None
      destination: str
      duration_days: int
      base_price_paise: int
      cover_image_url: Optional[str] = None
      items: List[PackageItemCreate] = Field(default_factory=list)

  class PackageUpdate(BaseModel):
      title: Optional[str] = None
      description: Optional[str] = None
      destination: Optional[str] = None
      duration_days: Optional[int] = None
      base_price_paise: Optional[int] = None
      cover_image_url: Optional[str] = None
      status: Optional[PackageStatus] = None

  class PackageItemResponse(BaseModel):
      model_config = ConfigDict(from_attributes=True)
      id: uuid.UUID
      type: str
      title: str
      description: Optional[str]
      estimated_cost_paise: int
      supplier_code: Optional[str]
      sort_order: int

  class PackageResponse(BaseModel):
      model_config = ConfigDict(from_attributes=True)
      id: uuid.UUID
      organization_id: uuid.UUID
      title: str
      description: Optional[str]
      destination: str
      duration_days: int
      base_price_paise: int
      cover_image_url: Optional[str]
      status: str
      created_at: datetime
      items: List[PackageItemResponse] = Field(default_factory=list)
  ```

### 32.3 — Backend API Routes

- `[ ]` **Create** `apps/api/app/api/packages.py`:
  - `POST /packages` — create package (require_active_org + org_admin)
  - `GET /packages` — list packages for org (paginated, filter by status)
  - `GET /packages/{id}` — get single package with items
  - `PATCH /packages/{id}` — update package metadata or status
  - `DELETE /packages/{id}` — soft delete
  - `POST /packages/{id}/items` — add item to package
  - `DELETE /packages/{id}/items/{item_id}` — remove item
  - `POST /packages/{id}/publish` — set status = published (validate ≥1 item)
  - `POST /packages/{id}/to-quote` — **KEY ROUTE:** Create a Quote pre-filled from package
    - Accept `{ customer_id: uuid }` in body
    - For each PackageItem: if it has `search_params`, run inventory search and use first result; else create QuoteItem with manual pricing from `estimated_cost_paise`
    - Return the new Quote (draft status)

- `[ ]` **Register router** in `main.py`: `app.include_router(packages.router, prefix="/api/v1")`

### 32.4 — Frontend: Admin Package Editor

- `[ ]` **RTK Query:** Create `apps/web/src/lib/api/packagesApi.ts`
  - `getPackages`, `getPackage`, `createPackage`, `updatePackage`, `deletePackage`, `publishPackage`, `packageToQuote`

- `[ ]` **Pages:**
  - `apps/web/src/app/(admin)/admin/packages/page.tsx` — list all packages with status badges
  - `apps/web/src/app/(admin)/admin/packages/new/page.tsx` — create package form
  - `apps/web/src/app/(admin)/admin/packages/[id]/page.tsx` — edit package + manage items

### 32.5 — Frontend: Agent Package Browse

- `[ ]` **Page:** `apps/web/src/app/(agent)/app/packages/page.tsx`
  - Grid/list of published packages with cover images, destination, price, duration
  - "Create Quote from Package" button → calls `POST /packages/{id}/to-quote` → redirects to `/app/quotes/{newId}`

### 32.6 — Phase 32 Exit
- `[ ]` Admin creates a package with ≥2 items
- `[ ]` Admin publishes the package
- `[ ]` Agent browses packages, converts one to a quote
- `[ ]` Quote follows normal flow (passengers → ready → send → pay)

---

# PHASE 33 — V2 Commission & Wallet

**Goal:** Replace spreadsheet-based commissions. Every booking auto-calculates commission from stored `supplier_cost`, `agent_markup`, `platform_fee`. Agents see a wallet with pending/available balance.

## Tasks

### 33.1 — Database Models & Migration

- `[ ]` **Create models** in `apps/api/app/models/wallet.py`:
  ```python
  class WalletLedgerEntry(Base, TimestampMixin):
      __tablename__ = "wallet_ledger"
      organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
      booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bookings.id"), nullable=True, index=True)
      type: Mapped[str] = mapped_column(String(30))  # commission_earned | commission_paid | adjustment
      amount_paise: Mapped[int] = mapped_column(Integer)  # positive = credit, negative = debit
      status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | available | settled
      description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
      settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

  class CommissionRule(Base, TimestampMixin):
      __tablename__ = "commission_rules"
      organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("organizations.id"), nullable=True)  # NULL = platform default
      product_type: Mapped[str] = mapped_column(String(20), default="flight")  # flight | hotel | all
      rule_type: Mapped[str] = mapped_column(String(20), default="percentage")  # percentage | flat_paise
      value: Mapped[int] = mapped_column(Integer)  # e.g. 70 = 70% of agent_markup goes to agent
      is_active: Mapped[bool] = mapped_column(default=True)
  ```

- `[ ]` **Alembic migration:** `alembic revision --autogenerate -m "add_wallet_commission_tables"`

### 33.2 — Commission Calculator Service

- `[ ]` **Create** `apps/api/app/services/commissions.py`:
  ```python
  async def calculate_commission(booking: Booking, db: AsyncSession) -> int:
      """
      Calculate agent commission from QuoteItem's stored fields.
      NEVER invert from customer_total — always use: agent_markup directly.
      Returns commission amount in paise.
      """
      # 1. Get quote items via booking.quote_id
      # 2. Sum agent_markup across all items
      # 3. Look up CommissionRule for the org (fallback to platform default)
      # 4. Apply rule: if percentage → agent_markup * value / 100; if flat → value per item
      # 5. Return calculated commission paise

  async def create_commission_entry(booking: Booking, db: AsyncSession) -> WalletLedgerEntry:
      """Called by worker after booking confirmed. Creates pending ledger entry."""

  async def mark_commission_available(booking_id: uuid.UUID, db: AsyncSession):
      """Called after settlement period (e.g. 24h after booking). Sets pending → available."""

  async def get_wallet_summary(org_id: uuid.UUID, db: AsyncSession) -> dict:
      """Returns {pending_paise, available_paise, total_earned_paise, total_settled_paise}."""
  ```

- `[ ]` **Wire into worker:** After `booking.status = confirmed` in `jobs.py`, call `create_commission_entry()`

### 33.3 — Backend API Routes

- `[ ]` **Create** `apps/api/app/api/wallet.py`:
  - `GET /wallet/summary` — returns wallet balance for current org (require_active_org)
  - `GET /wallet/ledger` — paginated ledger entries (require_active_org)
  - `GET /wallet/ledger/export` — CSV export of ledger

- `[ ]` **Add to admin routes** (`apps/api/app/api/admin.py`):
  - `GET /admin/commissions` — list all orgs with pending/owed amounts (require_platform_admin)
  - `POST /admin/commissions/{org_id}/settle` — mark entries as settled (require_platform_admin)
  - `GET /admin/commission-rules` — list all rules
  - `POST /admin/commission-rules` — create/update rule

- `[ ]` **Register routers** in `main.py`

### 33.4 — Frontend: Agent Wallet Page

- `[ ]` **RTK Query:** Create `apps/web/src/lib/api/walletApi.ts`
- `[ ]` **Page:** `apps/web/src/app/(agent)/app/wallet/page.tsx`
  - Balance cards: Pending, Available, Total Earned
  - Ledger table with booking reference, amount, status, date
  - Export button (CSV download)
- `[ ]` **Add "Wallet" link** to agent sidebar navigation

### 33.5 — Frontend: Admin Commissions Page

- `[ ]` **Page:** `apps/web/src/app/(admin)/admin/commissions/page.tsx`
  - Table: Org name | Pending | Available | Owed | Actions (Settle)
  - Commission rules editor (modal or inline)

### 33.6 — Phase 33 Exit
- `[ ]` Confirmed booking auto-creates pending commission entry
- `[ ]` Agent wallet shows correct balance
- `[ ]` Admin can view owed amounts and settle
- `[ ]` Ledger reconciles to sample bookings using `agent_markup * rule / 100`

---

# PHASE 34 — V2 Follow-ups & Document Vault

**Goal:** Recover unpaid quotes via automated nudges. Store tickets/vouchers/invoices against bookings.

## Tasks

### 34.1 — Follow-up Detector Jobs

- `[ ]` **Add to worker.py:** New function `check_unpaid_followups(db)`:
  - Query quotes where `status IN (sent, ready)` AND `created_at < now - 24h` AND no followup sent in last 24h
  - For each, create a `JobOutbox` entry with `type = "followup_reminder"` and `payload = {quote_id, hours_unpaid: 24}`
  - Also check 48h threshold for second reminder
  - Call this in the worker's main loop every 15 minutes

- `[ ]` **Create model** in `apps/api/app/models/commercial.py`:
  ```python
  class FollowUp(Base, TimestampMixin):
      __tablename__ = "follow_ups"
      quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"), index=True)
      organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
      type: Mapped[str] = mapped_column(String(30))  # auto_24h | auto_48h | manual
      status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | sent | snoozed | dismissed
      message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
      snoozed_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
  ```

- `[ ]` **Alembic migration**

### 34.2 — Follow-up API Routes

- `[ ]` **Create** `apps/api/app/api/followups.py`:
  - `GET /followups` — list pending followups for org (require_active_org)
  - `POST /followups/{id}/snooze` — snooze for N hours `{ hours: 12 }`
  - `POST /followups/{id}/dismiss` — mark as dismissed
  - `POST /followups/{id}/send-reminder` — generate wa.me reminder for the unpaid quote

- `[ ]` **Register router** in `main.py`

### 34.3 — Follow-up Frontend

- `[ ]` **RTK Query:** Create `apps/web/src/lib/api/followupsApi.ts`
- `[ ]` **Page:** `apps/web/src/app/(agent)/app/followups/page.tsx`
  - List of unpaid quotes with customer name, amount, hours overdue
  - Actions: Snooze, Dismiss, Send Reminder (opens wa.me)
  - Badge count on sidebar "Follow-ups (3)"
- `[ ]` **Home page integration:** Add followup count to attention strip on agent home page

### 34.4 — Document Vault

- `[ ]` **Create model** in `apps/api/app/models/commercial.py`:
  ```python
  class BookingDocument(Base, TimestampMixin):
      __tablename__ = "booking_documents"
      booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id"), index=True)
      organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
      type: Mapped[str] = mapped_column(String(30))  # ticket | voucher | invoice | receipt | other
      filename: Mapped[str] = mapped_column(String(255))
      storage_url: Mapped[str] = mapped_column(String)  # S3/R2 URL or local path for V1
      mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
      uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
  ```

- `[ ]` **Alembic migration**

- `[ ]` **API Routes** in `apps/api/app/api/documents.py`:
  - `POST /bookings/{booking_id}/documents` — upload document (multipart/form-data)
    - V1: Store file to `uploads/` directory locally. V2: S3/R2.
    - Validate org ownership via booking → quote → organization_id
  - `GET /bookings/{booking_id}/documents` — list documents
  - `GET /documents/{id}/download` — serve file with org-scoped auth
  - `DELETE /documents/{id}` — soft delete

- `[ ]` **Frontend:** Add documents section to booking detail / quote detail page
  - Upload button (drag & drop or file picker)
  - Document list with type badge, filename, download link
  - "Share via WhatsApp" button (builds wa.me link with document URL)

### 34.5 — Phase 34 Exit
- `[ ]` Unpaid quote at 24h generates a followup entry
- `[ ]` Agent can snooze, dismiss, or send reminder from followups page
- `[ ]` Agent can upload a PDF to a confirmed booking
- `[ ]` Document download is org-scoped (other orgs cannot access)

---

# PHASE 35 — V2 AI Copilot

**Goal:** Agent types natural language ("Delhi to Mumbai flight for 2 adults next Friday under 10k") → AI parses intent → runs real inventory search → drafts a quote for agent review. **AI NEVER invents prices.**

## Tasks

### 35.1 — AI Service (Backend)

- `[ ]` **Create** `apps/api/app/services/ai_copilot.py`:
  ```python
  async def parse_travel_intent(user_message: str) -> dict:
      """
      Uses LLM (OpenAI/Gemini) to extract structured search params from natural language.
      Returns: { type, origin, destination, departure_date, return_date, passengers, budget_max }
      MUST NOT invent prices or availability.
      """

  async def format_quote_draft(offers: List[NormalizedOffer], intent: dict) -> dict:
      """
      Uses LLM to select best matching offers and format a human-readable summary.
      Returns: { selected_offer_ids: [...], summary: "...", suggested_markup: int }
      Offer IDs MUST be a subset of the actual search results.
      """
  ```

- `[ ]` **Add LLM config** to `config.py`:
  ```python
  OPENAI_API_KEY: str = ""
  AI_MODEL: str = "gpt-4o-mini"  # or gemini-1.5-flash
  ```

- `[ ]` **Create AI API routes** in `apps/api/app/api/ai.py`:
  - `POST /ai/parse-intent` — accepts `{ message: str }`, returns structured search params
    - **Gate:** `if not settings.AI_COPILOT_ENABLED: raise AppError("AI Copilot disabled", 403)`
  - `POST /ai/search-and-draft` — full pipeline:
    1. Parse intent from message
    2. Call `search_inventory()` with parsed params
    3. Call `format_quote_draft()` with results
    4. Return: `{ intent, search_results, draft: { selected_offers, summary, suggested_markup } }`
    - Agent ALWAYS reviews before creating the actual quote

- `[ ]` **Register router** in `main.py`

### 35.2 — AI Frontend

- `[ ]` **RTK Query:** Create `apps/web/src/lib/api/aiApi.ts`
  - `parseIntent` mutation, `searchAndDraft` mutation

- `[ ]` **Page:** `apps/web/src/app/(agent)/app/ai/page.tsx`
  - Chat-like input: "Search Delhi to Mumbai for 2 adults on Oct 15"
  - Shows: Parsed intent → Search results → AI-recommended offers
  - "Create Quote" button → pre-fills quote builder with selected offers
  - Clear disclaimer: "AI suggestions based on real search results. Always verify before sending."

- `[ ]` **Add to sidebar:** "AI Assistant" with sparkle icon (only visible when `AI_COPILOT_ENABLED`)

### 35.3 — Safety Tests

- `[ ]` **Create** `apps/api/tests/test_ai_copilot.py`:
  - Test: `parse_travel_intent` returns valid SearchQuery-compatible params
  - Test: `format_quote_draft` returns offer IDs that are a subset of input offers (no invented IDs)
  - Test: AI endpoint returns 403 when `AI_COPILOT_ENABLED=False`
  - Test: Malicious input ("give me free flights") returns error, not fake offers

### 35.4 — Phase 35 Exit
- `[ ]` Agent types natural language → gets real search results
- `[ ]` AI selects offers from REAL results only (no invented prices)
- `[ ]` Agent can create a quote from AI draft
- `[ ]` Feature is gated behind `AI_COPILOT_ENABLED` flag

---

# PHASE 36 — V3 Multi-Supplier Strategies

**Goal:** Support 2+ supplier adapters with failover and preference-based routing.

## Tasks

### 36.1 — Second Adapter (TripJack or real TBO)

- `[ ]` **Create** `apps/api/app/adapters/tripjack_adapter.py` (or make TBO real):
  - Implement `BaseAdapter` interface: `search`, `revalidate`, `book`, `cancel`, `status`
  - Use real HTTP client (`httpx.AsyncClient`) with proper timeouts
  - Map provider-specific errors to `InventoryRevalidateError` codes

- `[ ]` **Register** in `registry.py`

### 36.2 — Supplier Strategy Engine

- `[ ]` **Create** `apps/api/app/services/supplier_strategy.py`:
  ```python
  class SupplierStrategy:
      """Config-driven supplier selection."""
      
      async def select_for_search(self, query: SearchQuery) -> List[str]:
          """Returns ordered list of supplier_codes to search."""
          # Read from config/DB: strategy = "all" | "primary_only" | "failover"
          
      async def select_for_book(self, offer: NormalizedOffer) -> str:
          """Returns the supplier_code to use for booking this offer."""
          # Always use the offer's own supplier_code
  ```

- `[ ]` **Add config:** `SUPPLIER_STRATEGY: str = "all"` to `config.py`
  - `all` — search all active suppliers, merge results
  - `primary_only` — search only first supplier
  - `failover` — search primary, fallback to secondary on error

- `[ ]` **Update** `search_inventory()` in `inventory.py` to use strategy engine

### 36.3 — Circuit Breaker

- `[ ]` **Create** `apps/api/app/core/circuit_breaker.py`:
  - Track failure count per supplier (in-memory for V1)
  - If failures exceed threshold (e.g. 5 in 2 minutes), open circuit → skip supplier for 5 minutes
  - Log circuit state changes to structlog

- `[ ]` **Admin kill switch:** `POST /admin/suppliers/{code}/disable` — sets `Supplier.is_active = False`

### 36.4 — Admin Supplier UI

- `[ ]` **Replace** ComingSoon in `apps/web/src/app/(admin)/admin/suppliers/page.tsx`
  - List of registered suppliers with status (active/inactive/circuit open)
  - Toggle active/inactive
  - Strategy selector (dropdown: all / primary_only / failover)

### 36.5 — Phase 36 Exit
- `[ ]` Two adapters registered and searchable
- `[ ]` Kill one supplier → failover returns results from the other
- `[ ]` Circuit breaker auto-disables a failing supplier after threshold

---

# PHASE 37 — V3 White-Label

**Goal:** Agency gets their own branded domain for customer-facing quote pages.

## Tasks

### 37.1 — Backend: Domain Resolution

- `[ ]` **Create model** in `apps/api/app/models/tenancy.py`:
  ```python
  class OrganizationDomain(Base, TimestampMixin):
      __tablename__ = "organization_domains"
      organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
      domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
      is_verified: Mapped[bool] = mapped_column(default=False)
      verification_token: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
  ```

- `[ ]` **API Routes** in `apps/api/app/api/organizations.py`:
  - `POST /organizations/domains` — add custom domain
  - `GET /organizations/domains` — list domains
  - `DELETE /organizations/domains/{id}` — remove domain
  - `GET /public/theme/{domain}` — returns org branding (logo, colors, name) for a domain (no auth)

### 37.2 — Frontend: Public Layout Theming

- `[ ]` **Update** `apps/web/src/app/q/[token]/page.tsx`:
  - On load, check hostname. If it matches a custom domain, fetch org theme via `/public/theme/{domain}`
  - Apply org's `primary_color`, `logo_url`, `brand_name` to the public quote page
  - Minimize "Powered by TripOS" branding for white-label tenants

- `[ ]` **Admin page:** `apps/web/src/app/(admin)/admin/branding/page.tsx`
  - Upload logo, set primary color, add custom domains
  - Domain verification instructions (CNAME setup)

### 37.3 — Phase 37 Exit
- `[ ]` Custom domain resolves to branded quote page with agency logo/colors
- `[ ]` Default TripOS domain still works for non-WL agencies

---

# PHASE 38 — V3 Distributor Hierarchy

**Goal:** Master agency creates sub-agent organizations with scoped data and commission splits.

## Tasks

### 38.1 — Backend: Org Hierarchy

- `[ ]` **Activate `parent_organization_id`** (already on `Organization` model):
  - Add scoping: sub-agent queries filter by `organization_id`, master sees all children
  - `GET /organizations/network` — returns tree of sub-orgs (master only)
  - `POST /organizations/sub-agents` — master creates a sub-agent org

- `[ ]` **Permission scoping:**
  - Sub-agent cannot see sibling org data
  - Master org can see aggregate bookings/GMV across sub-agents
  - Commission waterfall: platform_fee → master commission → sub-agent commission

- `[ ]` **Extend RBAC:** Add `UserRole.master_admin` or use org hierarchy to determine access level

### 38.2 — Frontend: Distributor Dashboard

- `[ ]` **Page:** `apps/web/src/app/(agent)/app/network/page.tsx`
  - Tree view of sub-agents with status, booking count, GMV
  - Add/remove sub-agent actions
  - Aggregate stats cards

### 38.3 — Phase 38 Exit
- `[ ]` Master creates sub-agent; sub-agent cannot read sibling data
- `[ ]` Commission split visible in wallet (platform + master + agent shares)
- `[ ]` Master sees network-wide aggregates

---

# PHASE 39 — Scale, Observability, Ops Maturity

**Goal:** Production-grade observability and operational runbooks.

## Tasks

### 39.1 — Structured Logging & Metrics

- `[ ]` **Audit all services** for consistent structlog usage:
  - Every external call (adapter, Razorpay, email) logs: start, duration_ms, success/error
  - Every worker cycle logs: jobs_processed, jobs_failed, cycle_duration_ms
- `[ ]` **Add request timing** to middleware (already exists, verify correctness)
- `[ ]` **Sentry performance:** Enable `traces_sample_rate=0.1` in production (reduce from 1.0)

### 39.2 — Database Performance

- `[ ]` **Review indexes:** Add composite indexes for common query patterns:
  - `quotes(organization_id, status, created_at DESC)`
  - `bookings(quote_id)` (already exists via FK)
  - `job_outbox(status, run_at)` for worker polling
  - `audit_events(entity_type, entity_id, created_at DESC)`
- `[ ]` **Create migration** for new indexes

### 39.3 — Worker Tuning

- `[ ]` **Add concurrency config:** `WORKER_POLL_INTERVAL_SECONDS: int = 5` to config.py
- `[ ]` **Add health check endpoint** to worker (simple file touch or HTTP endpoint)
- `[ ]` **Alerting:** Worker logs `dead_letter_spike` if > 5 dead jobs in 1 hour

### 39.4 — Ops Runbooks

- `[ ]` **Create/update** `docs/ops/`:
  - `REFUND_RUNBOOK.md` — steps for manual refund after failed booking
  - `SUPPLIER_OUTAGE_RUNBOOK.md` — how to disable supplier, notify agents
  - `BACKUP_RESTORE.md` — Postgres backup/restore commands for Render
  - `INCIDENT_TEMPLATE.md` — standardized incident report format

### 39.5 — Phase 39 Exit
- `[ ]` All critical paths have structured logs
- `[ ]` Database indexes added for slow queries
- `[ ]` Ops runbooks exist for top 3 failure scenarios
- `[ ]` Worker health check functional

---

# PHASE 40 — Continuous Backlog & Quarterly Review

**Goal:** Establish cadence for controlled evolution.

## Tasks

### 40.1 — Process Setup

- `[ ]` **Create** `docs/backlog.md`:
  - Template with sections: New Ideas, V1.5 Queue, V2 Queue, V3 Queue, Parked
  - Every idea must have: title, requester, version tag, effort estimate, priority
- `[ ]` **Create** `docs/quarterly-review-template.md`:
  - Sections: Metrics Review, Feature Completion %, Active Issues, Next Quarter Goals

### 40.2 — Monitoring Cadence

- `[ ]` **Monthly check:** Admin analytics dashboard review
  - Active Transacting Agents trend
  - Booking failure rate trend
  - GMV growth
- `[ ]` **Quarterly:** Review `tripos-enhancements.md`, accept/park items

### 40.3 — Phase 40 Exit
- `[ ]` This phase never "ends" — it's a perpetual process
- `[ ]` Initial templates created and first review scheduled

---

# Cross-Cutting Rules (Apply to ALL Phases)

> **Every AI coding assistant implementing these phases MUST follow these rules:**

1. **Org scoping:** ALL commercial data routes use `require_active_org` dependency. Query MUST filter by `organization_id`.
2. **Audit trail:** ALL mutations (create/update/delete) on quotes, bookings, payments, packages, wallet entries call `write_audit()`.
3. **Error handling:** Use `AppError(message, status_code, error_code)` for domain errors. Never raise raw `HTTPException` in service layer.
4. **Pagination:** ALL list endpoints use `limit`/`offset` params. Cap at 100 per page. Return `{items, total, limit, offset}`.
5. **Testing:** Each phase must include at least 2 pytest files: one for happy path, one for auth/IDOR denial.
6. **Frontend patterns:** Use `apiSlice.injectEndpoints()` for new RTK Query endpoints. Use shadcn/ui components. All pages need loading skeleton, empty state, error retry.
7. **Enum consistency:** Add new enum values to `enums.py`. Use Python enums, not raw strings.
8. **Migration:** Every new model needs `alembic revision --autogenerate`. Run `alembic upgrade head` after.
9. **No hardcoded URLs:** Use `settings.FRONTEND_URL`, `settings.BACKEND_CORS_ORIGINS`. RTK Query uses relative `/api/v1/` paths (proxied by Next.js).
10. **Secrets:** Never commit `.env`. New secrets go in `render.yaml` as `sync: false`.
