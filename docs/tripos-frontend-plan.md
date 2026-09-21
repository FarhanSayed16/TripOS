# TripOS — Complete Frontend Plan

### Pages, navigation, design system, motion, and scalable UI architecture — **no code**

**Stack lock:** Next.js (App Router) + TypeScript · hosted on **Vercel** · talks to FastAPI on **Render**  

**Companions:** `tripos-backend-plan.md` · `tripos-implementation-plan.md` · `tripos-modules-and-flow.md`

**Purpose:** Blueprint for every screen, nav structure, visual language, animation rules, and how the frontend stays professional and scalable across V1 → V3. No source code in this document.

---

## 1. Frontend product surfaces (four apps in one Next.js project)

TripOS is not one flat website. Plan **five surfaces** under one Next.js app, with clear layout boundaries:

| Surface | Who uses it | Goal |
|---|---|---|
| **A. Marketing / entry** | Visitors, invited agents | Trust + clear “this is agent software” |
| **B. Auth** | Agents + admins | Signup, login, verify (Resend) |
| **C. Agent OS** | Travel agents (daily work) | Search → quote → wa.me → track money |
| **D. Admin OS** | Farhan / Nilesh (platform) | Approve agents, bookings, failures |
| **E. Public customer** | End customers (no login) | View quote, pay, payment status |

**Scalability rule:** Shared design system + shared API client; separate route groups and layouts so Agent UI never inherits Admin chrome (and Public never inherits dashboard chrome).

---

## 2. Visual identity — professional theme (locked direction)

### 2.1 Design intent
- **Feel:** Calm operations tool for Indian travel agencies — trustworthy, fast, crisp. Not a consumer OTA. Not “AI purple SaaS.”
- **Metaphor:** *Coastal ink desk* — deep ink navy for structure, sea teal for action, warm paper neutrals for reading long quote/booking data.
- **Avoid (explicit):** Purple/indigo gradient clichés · cream + terracotta “AI brochure” look · newspaper broadsheet density · neon glows · emoji UI · oversized glassmorphism · dark-mode-first default.

### 2.2 Color system (CSS variables — conceptual tokens)

| Token | Role | Direction |
|---|---|---|
| `--ink` | Primary text / strongest UI chrome | Deep ink navy (`~#0B1F33`) |
| `--ink-soft` | Secondary text | Slate blue-gray |
| `--paper` | App background | Warm off-white paper (`~#F7F5F1`) — not pure gray, not cream-terracotta palette |
| `--surface` | Panels / sheets | White / slightly lifted paper |
| `--line` | Borders / dividers | Soft cool gray-blue hairline |
| `--teal` | Primary actions (search, send, pay CTAs) | Sea teal (`~#0F766E`) |
| `--teal-deep` | Hover / pressed | Darker teal |
| `--coral` | Alerts / needs attention (sparingly) | Muted coral — errors & “attention” only |
| `--amber` | Warnings / fare expiry | Soft amber |
| `--mint` | Success / confirmed | Restrained green |
| `--focus` | Keyboard focus ring | Teal outline |

**Usage rules**
- Primary buttons = teal on paper/white — high contrast.
- Destructive = coral text/outline first; solid coral only for confirm destroy.
- Never use teal as large full-page background; teal is for **actions and accents**.
- Agent cost / margin (internal) use quieter ink tones; customer price uses stronger ink weight.
- Public quote pages can use org branding colors when present (white-label later); fallback = TripOS tokens.

### 2.3 Typography
| Role | Character | Notes |
|---|---|---|
| **Display / brand** | Distinctive serif or semi-serif with travel-editorial feel (e.g. family in the spirit of *Newsreader / Fraunces / Source Serif* — pick one and stick) | Used for brand wordmark, public quote titles, empty-state headlines |
| **UI / body** | Humanist sans with excellent digits (e.g. spirit of *Satoshi / Geist / Manrope* — **not** Inter/Roboto/Arial/system as the brand face) | Tables, forms, nav |
| **Mono / refs** | Tabular nums + mono for PNR, payment IDs | Booking refs only |

**Type scale:** 12 / 14 / 16 / 18 / 24 / 32 / 40 — denser in dashboards, more airy on public quote & auth.

### 2.4 Iconography
- One set only: **Lucide** or **Phosphor** (regular weight) — not mixed libraries.
- Stroke icons, consistent 1.5–2px optical weight.
- No illustrated emoji icons in product chrome.
- Status icons mapped: confirmed / pending / failed / expired / sent.

### 2.5 Elevation & shape
- Radius: **8px** controls, **12px** panels — not pill-everything.
- Borders over heavy shadows; one subtle shadow max for floating menus/modals.
- Default: **no card grids in marketing hero**; in the Agent OS, use **worksheets / sections / tables** more than nested card stacks.
- Dense data (search results, bookings) = **tables + row actions**, not only card masonry.

### 2.6 Background atmosphere
- App shell: soft paper wash + very subtle top gradient (ink→paper at ~4% opacity) — not flat gray.
- Auth & public quote: stronger atmosphere (soft coastal gradient or abstract map-grid texture at low opacity) + real travel photography only if licensed; otherwise geometric texture.
- Dashboard content area stays calm so data wins.

---

## 3. Motion & transitions (professional, purposeful)

Ship intentional motion — not decoration spam.

### 3.1 Motion principles
1. **Orient** — user always knows where they are (page enter).
2. **Feedback** — clicks and submits acknowledge instantly.
3. **Continuity** — shared elements (quote drawer, search → results) feel connected.
4. **Respect** — honor `prefers-reduced-motion` (instant cuts, no parallax).

### 3.2 Required motion set (minimum 2–3 “signature” motions + system)

| Motion | Where | Behavior |
|---|---|---|
| **Page enter** | All app pages | Soft fade + 6–10px rise (150–220ms) |
| **Shell persist** | Sidebar/topbar | No remount animation; only content animates |
| **List stagger** | Search results, booking rows | 20–40ms stagger, capped at 8 items |
| **Drawer / sheet** | Quote builder, filters | Slide from right + dim backdrop |
| **Status pulse** | Pending payment / confirming booking | Gentle opacity pulse on status chip only |
| **Button press** | Primary CTAs | 0.98 scale + color deepen |
| **Toast** | Success/error | Slide from top-right, auto-dismiss |
| **Table row hover** | Data tables | Background wash only (no bounce) |
| **Skeleton shimmer** | Loading | Soft shimmer on paper tone — no rainbow |

**Timing tokens:** `fast 120ms` · `base 200ms` · `slow 320ms` · easing `standard` (ease-out) · `emphasized` for drawers.

### 3.3 Transition map
- Route change inside Agent OS → content crossfade.
- Auth → Agent OS → one longer welcome fade (once per session).
- Public pay success → calm check animation (stroke draw), then static.

---

## 4. Information architecture & navigation

### 4.1 Agent OS — primary nav (left sidebar)

| Nav item | Destination | V1 |
|---|---|---|
| **Home** | Today’s snapshot | Yes |
| **Search** | Flights / Hotels | Yes |
| **Quotes** | Quote list + statuses | Yes |
| **Bookings** | Booking list + attention | Yes |
| **Customers** | CRM | Yes |
| **Payments** | Payment history (org) | Yes (light) |
| **Packages** | Browse packages | V2 |
| **Wallet** | Commissions | V2 |
| **AI Assist** | NL → draft quote | V2 (flagged) |
| **Settings** | Profile, org, branding fields | Yes (basic) |

**Top bar (Agent):** org name · user menu · “Needs attention” badge · global search (customers/quotes) later.

**Mobile Agent:** bottom tabs — Home · Search · Quotes · Bookings · More.

### 4.2 Admin OS — primary nav

| Nav item | Destination | V1 |
|---|---|---|
| **Overview** | Platform KPIs | Yes |
| **Agents** | Approve / list orgs | Yes |
| **Bookings** | Cross-org bookings | Yes |
| **Failures** | needs_manual_support queue | Yes |
| **Payments** | Gateway reconciliation view | Yes |
| **Suppliers** | Adapter enablement (read/config) | Yes (basic) |
| **Packages** | Curate packages | V2 |
| **Commissions** | Owed across agents | V2 |
| **Branding / Tenants** | White-label | V3 |
| **Distributors** | Org tree | V3 |

### 4.3 Public — no chrome nav
- Quote view · Pay redirect return · Status page only.
- Footer: agency name (brand) + support phone if provided · minimal TripOS mark until white-label removes it.

### 4.4 Auth — minimal chrome
- Brand wordmark only · language later · link to login/signup.

---

## 5. Complete page inventory

### 5.1 Marketing / entry
| Page | Purpose | Notes |
|---|---|---|
| `/` Landing | Brand-first: TripOS name as hero signal, one line value, one CTA “Agent login / Request access” | One composition; no dashboard widgets in first viewport |
| `/request-access` | Lead form for new agencies (optional V1) | Or WhatsApp contact — keep simple |

### 5.2 Auth pages
| Page | Purpose |
|---|---|
| `/login` | Email + password |
| `/signup` | Agency + user KYC basics |
| `/verify-email` | “Check inbox” + resend via Resend |
| `/verify-email/confirm` | Token landing |
| `/forgot-password` | V1.5 optional |
| `/reset-password` | V1.5 optional |

### 5.3 Agent OS pages
| Page | Purpose | Key UI blocks |
|---|---|---|
| `/app` Home | Daily OS | Attention strip · recent quotes · quick actions (New search, New customer) |
| `/app/search` | Hub | Choose Flights / Hotels |
| `/app/search/flights` | Flight search | Form · results table · compare tray (optional) · “Add to quote” |
| `/app/search/hotels` | Hotel search | Form · results · room pick · “Add to quote” |
| `/app/quotes` | Quote list | Filters: draft/sent/paid/expired · table |
| `/app/quotes/new` | Quote builder | Customer · line items · markup · pax · totals · expiry |
| `/app/quotes/[id]` | Quote detail | Status · timeline · actions: Refresh, Create pay link, Share wa.me, Clone |
| `/app/quotes/[id]/send` | Send checklist | Preview WhatsApp text · open wa.me · mark sent |
| `/app/bookings` | Bookings list | Status filters · attention first |
| `/app/bookings/[id]` | Booking detail | Supplier ref · pax · docs (V2) · cancel request |
| `/app/customers` | CRM list | Search by phone/name |
| `/app/customers/[id]` | Customer 360 | Quotes · bookings · messages log |
| `/app/customers/new` | Add customer | Name, phone, email |
| `/app/payments` | Payments list | Captured / failed / pending |
| `/app/settings` | User settings | Profile, password |
| `/app/settings/organization` | Org profile | KYC fields, branding fields (logo/color for future WL) |
| `/app/packages` | Package browse | V2 |
| `/app/wallet` | Wallet/commission | V2 |
| `/app/ai` | AI assist | V2 · feature flag |
| `/app/follow-ups` | Nudge inbox | V2 |

### 5.4 Admin OS pages
| Page | Purpose |
|---|---|
| `/admin` | Overview KPIs |
| `/admin/agents` | List + approve/reject |
| `/admin/agents/[orgId]` | Org detail + support access to their bookings |
| `/admin/bookings` | Global bookings |
| `/admin/failures` | Manual support queue |
| `/admin/payments` | Payment ops |
| `/admin/suppliers` | Supplier status / primary switch (careful) |
| `/admin/packages` | V2 package editor |
| `/admin/commissions` | V2 |
| `/admin/tenants` | V3 white-label domains |
| `/admin/distributors` | V3 tree |

### 5.5 Public customer pages
| Page | Purpose |
|---|---|
| `/q/[token]` | Hosted quote — clean, non-technical, expiry, total, Pay CTA |
| `/q/[token]/pay-return` | After Razorpay redirect |
| `/q/[token]/status` | Payment received / booking confirming / confirmed / contact agent |

---

## 6. Key user flows (screen sequences)

### 6.1 Core V1 loop (Agent)
1. Home → Search flights/hotels  
2. Select offers → Quote builder (customer + markup + pax)  
3. Revalidate indicator (fare check)  
4. Create payment link  
5. Send checklist → open wa.me  
6. Bookings / quote detail updates when webhook confirms  

### 6.2 Public pay
1. Open `/q/[token]`  
2. Pay CTA → Razorpay  
3. Return → status page (“don’t close — confirming”)  
4. Agent sees confirmed in Bookings  

### 6.3 Admin pilot ops
1. Agents → approve  
2. Failures → open booking → mark/handle  

### 6.4 V2 AI (later)
1. AI Assist → type NL → review structured params → run search → review draft → open Quote builder prefilled  

---

## 7. Layout system

| Layout | Used by | Structure |
|---|---|---|
| `MarketingLayout` | `/` | Full-bleed hero possible; minimal top brand bar |
| `AuthLayout` | login/signup | Split or centered form on atmospheric background; brand dominant |
| `AgentLayout` | `/app/*` | Collapsible sidebar + topbar + main + optional right drawer |
| `AdminLayout` | `/admin/*` | Similar shell, distinct accent stripe so operators never confuse surfaces |
| `PublicLayout` | `/q/*` | No sidebar; brand header (agency) + content + quiet footer |
| `BlankLayout` | callbacks | Minimal |

**Responsive breakpoints:** mobile · tablet · desktop (sidebar becomes drawer &lt; tablet).

---

## 8. UI component inventory (design system — structure only)

### 8.1 Foundations
- Color tokens · type tokens · space scale (4/8/12/16/24/32/48) · radius · motion tokens · z-index scale  

### 8.2 Primitives
- Button (primary / secondary / ghost / danger)  
- Input · Textarea · Select · Checkbox · Radio · Date picker · Phone input  
- Badge / Status chip  
- Avatar · Icon wrapper  
- Tooltip · Toast · Modal · Drawer / Sheet  
- Tabs · Pagination · Empty state · Skeleton  
- Table (sortable headers later) · Row actions menu  

### 8.3 Product patterns (composites)
- **SearchFormFlight / SearchFormHotel**  
- **ResultsTable** + fare expiry hint  
- **CompareTray** (optional V1.5)  
- **MarkupControl** (₹ or %)  
- **PriceBreakdown** (agent-only vs customer-facing variants)  
- **PassengerForm**  
- **QuoteTimeline**  
- **WaMePreview** (message preview + copy + open)  
- **AttentionBanner**  
- **OrgSwitcher** (future multi-org; stub)  
- **FeatureFlagGate**  

### 8.4 Card policy
- Prefer **sections and tables** in Agent OS.  
- Use bordered panels when grouping forms.  
- Public quote: one clear document layout — not a stack of marketing cards.

---

## 9. Content & UX copy rules
- Customer-facing: plain language, ₹ formatting (`en-IN`), dates clear (e.g. `02 Dec 2026`).  
- No GDS jargon on public pages.  
- Always show quote expiry when relevant.  
- Agent-only screens may show supplier cost; public never.  
- Empty states teach the loop: “Create a customer → Search → Quote → Share on WhatsApp.”  
- Error states suggest next action (“Refresh fare”, “Contact support”, “Retry”).  

---

## 10. State design (every list/detail page)

| State | Treatment |
|---|---|
| Loading | Skeletons matching layout (no spinner-only full page) |
| Empty | Illustration-free; typography + one CTA |
| Error | Inline alert + retry |
| Partial (fare changed) | Blocking banner before pay/send |
| Success | Toast + optional inline confirmation |
| Permission denied | Calm locked page |

---

## 11. Frontend folder structure (planning — no code)

```text
apps/web/
├── app/
│   ├── (marketing)/          # Landing
│   ├── (auth)/               # Login, signup, verify
│   ├── (agent)/app/          # Agent OS routes
│   ├── (admin)/admin/        # Admin OS routes
│   ├── (public)/q/[token]/   # Customer quote/pay status
│   ├── layout                # Root providers
│   └── api/                  # Optional BFF route handlers (only if needed)
├── components/
│   ├── ui/                   # Primitives
│   ├── patterns/             # Product composites
│   ├── layouts/              # Shells
│   └── motion/               # Shared transition wrappers
├── features/                 # Feature-sliced UI (search, quotes, …)
│   ├── search/
│   ├── quotes/
│   ├── bookings/
│   ├── customers/
│   ├── payments/
│   ├── messaging/
│   ├── admin/
│   └── ai/                   # V2
├── lib/
│   ├── api/                  # API client, auth headers, error mapping
│   ├── auth/                 # Session helpers
│   ├── formatting/           # ₹, dates, phones
│   ├── flags/                # Feature flags
│   └── wa-me/                # Build/open helpers (client)
├── styles/                   # Tokens, global
└── public/                   # Brand assets, textures
```

**Scalability:** features own their pages’ building blocks; `components/ui` stays generic; never import Admin feature code into Agent pages.

---

## 12. Data & client architecture (frontend)

| Concern | Plan |
|---|---|
| API base | Env `NEXT_PUBLIC_API_URL` → Render |
| Auth | HttpOnly cookie session preferred **via Next.js BFF/proxy** so browser stays same-origin to Vercel; API on Render uses Bearer access + refresh. Avoid raw cross-domain cookie-only auth unless `*.tripos.in` parent domain is configured (`SameSite=None; Secure`). |
| Fetching | Server Components where useful (public quote); client for interactive search/builder |
| Cache | React Query or equivalent for Agent lists (quotes/bookings) — optional but recommended for scale |
| Forms | One form library standard (e.g. React Hook Form) across app |
| Validation | Mirror backend rules; show field errors clearly |
| Feature flags | Match backend flags for AI / offline pay |
| Errors | Central toast + error boundary per surface |
| Analytics | Later; don’t block V1 |

---

## 13. Accessibility & quality bar
- Keyboard: sidebar, drawers, modals, tables.  
- Focus rings visible (`--focus`).  
- Contrast: text on paper/teal meets WCAG AA.  
- Touch targets ≥ 44px on mobile Agent tabs.  
- Reduced motion supported.  
- Public quote readable on low-end Android (common for customers).  

---

## 14. Responsive behavior matrix

| Surface | Mobile priority |
|---|---|
| Agent Search | Form first; results as stacked rows; sticky “Add to quote” |
| Quote builder | Stepper: Customer → Items → Pax → Price → Send |
| Bookings | Cards-as-rows acceptable on mobile only |
| Public quote | Single column; sticky Pay bar |
| Admin | Usable on tablet; desktop preferred for ops |

---

## 15. Branding & white-label readiness (UI)

**V1:** TripOS tokens everywhere; org `brand_name` on quote header if set.  
**V3:** Public layout reads org theme (logo, primary color, domain).  
**Never hardcode** agency name as “TripOS” on `/q/*` once org branding exists.

---

## 16. Animation inventory by page (checklist)

| Page | Motions |
|---|---|
| Landing | Hero fade-in · CTA hover · light background drift (subtle) |
| Login/Signup | Form rise · error shake (subtle, once) |
| Agent Home | Attention banner slide · quick-action hover |
| Search results | Stagger rows · drawer for filters |
| Quote builder | Step progress · line-item add animation |
| Send / wa.me | Preview appear · success toast after mark sent |
| Booking detail | Status chip change transition |
| Public quote | Document enter · sticky pay bar slide-up on mobile |
| Pay status | Confirm stroke animation |

---

## 17. V1 vs V2 vs V3 frontend scope

### V1 — must build
- Marketing minimal · Auth + verify · full Agent loop pages · Admin approve/failures · Public quote + status  
- Design tokens · layouts · primitives · WaMePreview · Attention states  
- Core motions (page enter, drawer, toast, skeletons)  

### V2 — add pages
- Packages · Wallet · AI Assist · Follow-ups · Document attachments UI  

### V3 — add pages
- Tenant branding admin · Distributor tree views · themed public storefront  

---

## 18. Frontend build order (execution)

1. **Design tokens + layouts + primitives**  
2. **Auth pages** wired to backend  
3. **Agent shell + Home + Customers**  
4. **Search (mock data) + Quote builder**  
5. **Quotes list/detail + WaMe send**  
6. **Payments + Bookings views**  
7. **Public quote + status**  
8. **Admin agents/bookings/failures**  
9. **Polish motion + empty/error states**  
10. **V2 pages when backend ready**  

---

## 19. Definition of done — Frontend V1

- [ ] All V1 pages exist with real navigation  
- [ ] Theme tokens applied consistently (no random one-off colors)  
- [ ] Agent can complete loop in UI against API  
- [ ] Public quote never shows agent cost  
- [ ] wa.me preview + open works on mobile  
- [ ] Admin can approve agents and open failures  
- [ ] Loading/empty/error states on all primary lists  
- [ ] Motion present and reduced-motion safe  
- [ ] Deployed on Vercel; env pointed at Render API  

---

## 20. Page → module mapping (for build ownership)

| Frontend area | Backend modules used |
|---|---|
| Auth pages | auth, organizations |
| Customers | crm |
| Search | inventory |
| Quotes / Send | quotes, messaging, payments |
| Bookings | bookings |
| Payments list | payments |
| Admin | admin, audit, organizations |
| Public quote | quotes (public), payments |
| AI page (V2) | ai_gateway + inventory |

---

## 21. Document map

| Doc | Role |
|---|---|
| `tripos-backend-plan.md` | Backend modules & services |
| **`tripos-frontend-plan.md` (this file)** | **Pages, nav, design, motion, FE structure** |
| `tripos-implementation-plan.md` | Overall phases & stack |

---

**Principle:** One professional visual system; four clear surfaces; Agent OS optimized for speed and clarity; public pages optimized for trust and payment; every V2/V3 screen extends the same tokens and layouts instead of inventing a new UI language.
