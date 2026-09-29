# TripOS — Master Frontend UI/UX Enhancement Plan

**Version:** 1.0 · **Date:** 2026-09-29  
**Product:** TripOS B2B Agent OS  
**Sources compared:**
- Current product screenshots → [`docs/currentui/`](../currentui/) (`1–5.png`)
- Approved new reference frames → [`docs/NewUIReference/`](../NewUIReference/) (`1–11.png`)
- Prior design notes → [`FRONTEND_UX_PLAN.md`](./FRONTEND_UX_PLAN.md), [`FRONTEND_IMAGE_GEN_PROMPTS.md`](./FRONTEND_IMAGE_GEN_PROMPTS.md)

**Goal:** Bring every agent, public, admin, and marketing surface from **today’s sparse functional UI** to the **NewUIReference visual + information density**, without inventing B2C/OTA features (no cabs, reviews, fake logo walls).

**How to use:** Work **one phase at a time**. Each phase has sub-phases, reference image IDs, acceptance checks, and “not in reference → still build” notes. Mark ☐ → ☑ as you ship.

---

## A. Snapshot: Current vs Target

| Area | Current UI (today) | New UI Reference (target) | Gap severity |
|---|---|---|---|
| Design tokens | Ad-hoc white + teal; inconsistent icon colors | Full board: Ink/Paper/Teal/Coral/Amber/Mint/Focus/Line + DM Sans + mono | **High** |
| Agent Home | Attention KPIs + empty “caught up”; weak quick actions; no right rail | Greeting + alert cards + KPI trends + embedded search + recent table + wallet/notifications rail | **High** |
| Search | Pill form on empty page; no results density | Summary bar, filters, fare/inventory chips, FX footnote, selected-flight rail | **Critical** |
| Quotes list | Filters + empty state | Richer list (status, money mono, actions) — extend beyond empty | **Medium** |
| Quote detail | Exists functionally; not at reference density | Markup ladder, ancillaries, seats, passengers, sticky CTA stack | **Critical** |
| Public quote | Basic `/q/[token]` | White-label header, EN/HI, FX display, Pay CTA, trust footer | **High** |
| Bookings | Simple ledger | KPI strip + filters + Change drawer with mock-reissue honesty | **High** |
| Settings | Thin | Tabs: Org / Display / Deal codes / AI / Domain checklist | **High** |
| Wallet | 3 KPI cards + empty tx | Keep structure; align tokens + trends + export | **Medium** |
| Admin | Functional dark admin | L2B banner, failures, partners create/rotate, supplier health | **High** |
| Marketing | Minimal centered hero + 5 cards | Brand-first hero image, EN/HI, 3 value cards, how-it-works | **Medium** |
| Mobile | Partial bottom nav | Full Home mobile pattern (ref `10.png`) | **High** |
| Global chrome | Bell + email; no EN/HI; Money nav under Finance mislabel | EN/HI toggle, agency switcher, global search, Money section | **High** |

**Reference map (NewUIReference)**

| File | Screen |
|---|---|
| `1.png` | Design system board |
| `2.png` | Agent Home (desktop) |
| `3.png` | Search results + selected flight rail |
| `4.png` | Quote detail + price ladder |
| `5.png` | Public customer quote |
| `6.png` | Bookings + Change (reissue) drawer |
| `7.png` | Settings (org / display / deals / AI / domain) |
| `8.png` | Admin overview + partners |
| `9.png` | Marketing landing |
| `10.png` | Mobile Home |
| `11.png` | Composite system overview (cross-check) |

**Current map (`currentui`)**

| File | Screen |
|---|---|
| `1.png` | Marketing landing (minimal) |
| `2.png` | Agent Home (attention desk) |
| `3.png` | Search (form only) |
| `4.png` | Quotes list (empty) |
| `5.png` | Wallet |

---

## B. Principles (apply in every phase)

1. **Tokens first** — no one-off blues/purples; use §Phase 1 palette.  
2. **Honesty** — Live / Simulated / Mock badges on every inventory surface.  
3. **Money truth** — display currency + “charged in INR” when different; PNR & ₹ in **mono**.  
4. **One job per page** — drawers for Change/reissue; sticky rails for quote price / selected flight.  
5. **Reference is law for layout** — if a control exists in NewUIReference, implement it; if missing but needed for FC backend, add per “Plus” notes below.  
6. **Do not copy** generic royal-blue SaaS clones; keep TripOS teal/ink/paper.

---

## Phase 1 — Design system foundation

**Why first:** Every later phase paints on these tokens.  
**Refs:** `NewUIReference/1.png`, styleguide `/styleguide`

### 1.1 Color tokens
- Wire CSS variables: Ink `#0F1C1A`, Paper `#F7F6F2`, Surface `#FFFFFF`, Teal `#0D9488`, Coral `#F87171`, Amber `#F59E0B`, Mint `#22C55E`, Focus `#14B8A6`, Line `#E5E7EB`
- Map Tailwind theme (`bg-paper`, `text-ink`, `bg-teal`, status utilities)

### 1.2 Typography
- UI: **DM Sans** (or equivalent geometric) for headings/body  
- Mono: **JetBrains Mono** / IBM Plex Mono for PNR, amounts, quote IDs  
- Hindi: Noto Sans Devanagari fallback

### 1.3 Core components
- Buttons: Primary / Secondary / Ghost / Destructive (exact states from board)  
- Inputs: default / focus / filled chip / error  
- Status chips: Confirmed, Pending, Failed, Live, Simulated, Mock  
- Alert banner (amber)  
- Table: header row, mono cells, row hover, checkbox column optional  

### 1.4 Elevation rules
- Prefer **1px Line border**; shadow only for floating drawers/modals (low)

**Exit:** Styleguide page matches `1.png`; agent shell can consume tokens without hard-coded hex in pages.

---

## Phase 2 — App shell & global chrome

**Why:** Shared frame for all agent pages.  
**Refs:** `2.png`, `3.png`, `7.png` (header pattern) · Current: `2–5.png` sidebar

### 2.1 Left navigation
- Groups: **Workspace** · **Operations** · **Money** · **System** (rename Finance → Money per reference)  
- Items: Home, Search, AI · Quotes, Bookings, Packages, Customers, Network · Wallet, Payments · Settings  
- Active: light teal pill + left teal bar  
- Footer: avatar, **name + agency**, Logout (not email-only)

### 2.2 Top header
- Page title + short subtitle  
- Global search: “Search bookings, PNR, customer…”  
- Agency selector (“Sahil Travels”)  
- **EN | HI** segmented control  
- Notifications bell + badge  
- User avatar initials  

### 2.3 Layout grid
- Desktop: sidebar 240px + main; right rail **only where reference shows it** (Home, Search selected, Quote price, Bookings change)  
- Content background = Paper; cards = Surface  

### 2.4 Plus (not in current UI)
- Wire locale toggle to existing i18n  
- Agency selector can be single-org stub until multi-org  

**Exit:** Every `/app/*` page shares identical shell; nav labels match reference.

---

## Phase 3 — Agent Home dashboard

**Refs:** `NewUIReference/2.png` · Current: `currentui/2.png`

### 3.1 Greeting block
- Time-based greeting + date  
- Subcopy: attention desk line  
- Optional “All systems operational” / L2B soft note  

### 3.2 Attention alerts
- Failed bookings card (coral) with count + CTA  
- Paid awaiting confirm card (amber) with count + CTA  
- Replace sole “You’re all caught up” as the *only* hero when counts > 0; keep empty success state when zero  

### 3.3 KPI row
- Bookings · GMV · Wallet · Customers  
- Trend microcopy when API allows; else hide trend  

### 3.4 Embedded search widget
- Flights / Hotels tabs  
- From / To + swap · dates · pax/class · **Deal code** · Search CTA  

### 3.5 Recent bookings table
- Columns per `2.png`: customer, route, status chip, PNR mono, amount mono, Open quote  

### 3.6 Right rail
- Wallet + Add money · Pending settlements  
- Notifications list (3–5 items)  
- AI Assistant promo card → `/app/ai`  

**Exit:** Side-by-side match with `2.png` structure; current sparse home retired.

---

## Phase 4 — Search & inventory results

**Refs:** `NewUIReference/3.png` · Current: `currentui/3.png`  
**Critical path for FC features.**

### 4.1 Search form polish
- Keep pill form but align spacing/labels to reference readability  
- Deal code field first-class (not tiny OPTIONAL)  

### 4.2 Results chrome
- Summary bar: `DEL → BOM · date · pax` + Edit search  
- Filters: Sort, Max stops, Airline, Max price  
- Results count  
- FX footnote when display ≠ charge  

### 4.3 Offer rows
- Airline / flight times / duration / stops  
- Fare family chip (Basic/Flex/Premium)  
- Inventory chip (Live/Simulated/Mock)  
- Segment lines: mkt vs operating  
- Deal code chip  
- Dual money: display large + charge small  
- Select / Selected states  

### 4.4 Selected flight right rail
- Timeline itinerary  
- Fare breakdown  
- Baggage/policy bullets  
- View fare rules  
- **Continue to quote →**  

### 4.5 Hotels tab
- Parity skeleton: list rows + select (hotel card density lighter than OTA)

### 4.6 Plus
- Empty results state with adjust-search CTA  
- Loading skeletons for rows  

**Exit:** Search page no longer “form over void”; results match `3.png` density.

---

## Phase 5 — Quotes list & create flow

**Refs:** Composite `11.png` quotes patterns · Current: `currentui/4.png`

### 5.1 Quotes list
- Title + “+ New Quote”  
- Search + status pills: All / Draft / Ready / Sent / Paid / Expired  
- Table: Customer, Created, Valid until, Status chip, Total (mono), actions  
- Empty state: icon + Search Inventory CTA (keep current idea, restyle)

### 5.2 New quote / cart
- Selected offers from search  
- Per-item markup inputs  
- Continue to detail  

### 5.3 Plus
- Bulk archive/filter by customer  
- Show inventory_mode on list rows  

**Exit:** List feels like a ledger, not an empty shell; create path clear.

---

## Phase 6 — Quote detail (core money desk)

**Refs:** `NewUIReference/4.png`  
**Most important revenue screen.**

### 6.1 Header
- Quote ID mono + copy  
- Status chips (Ready / Paid / …) + Live Inventory  
- Customer, pax count, created, valid until  
- Breadcrumbs  

### 6.2 Flight offer card
- Legs, times, aircraft, fare family  
- View fare rules  

### 6.3 Ancillaries & seats
- Selected baggage/meal grid + Edit  
- Seat list per passenger  
- Included-seat info banner  

### 6.4 Passengers table
- Title, name, type, DOB, seat, bag, meal, FF  

### 6.5 Sticky price panel (right)
- Currency toggle display  
- Ladder: Supplier → Platform fee → Agent markup (editable) → Extras → **Customer total**  
- FX secondary line  
- CTAs: Mark ready · Create pay link · Send WhatsApp · Cancel (coral outline)  

### 6.6 Meta card
- Inventory mode, fare family, deal code, validity, creator  

### 6.7 Plus
- Documents / itinerary / PDF links when vault exists  
- Soft-fail cancel messaging  

**Exit:** Visual match to `4.png`; markup ladder always visible.

---

## Phase 7 — Public quote & payment

**Refs:** `NewUIReference/5.png`

### 7.1 White-label chrome
- TripOS + agency brand/logo/tagline  
- EN | हिन्दी  

### 7.2 Trip card
- Route headline, dates, pax, cabin  
- Valid / days-left badges  
- Flight timeline (sanitized — no supplier cost)  
- Inclusions: bag / meal / seat  
- Fare conditions accordion  

### 7.3 Pay column
- Display total + INR charge footnote  
- **Pay ₹…** primary  
- Payment method trust row  
- Important information box  

### 7.4 Trust footer
- Secure / Instant confirmation / Contact agency WhatsApp  

### 7.5 Status page (`/q/[token]/status`)
- Post-pay outcome; no agent economics  

**Exit:** Customer page matches `5.png`; never leaks markup.

---

## Phase 8 — Bookings ledger & reissue change

**Refs:** `NewUIReference/6.png`

### 8.1 Bookings header & tabs
- All / Flights / Hotels  

### 8.2 KPI strip
- Total / Confirmed / Pending / Failed (30d)  

### 8.3 Filters
- Search, date range, status, supplier  

### 8.4 Table
- Checkbox, customer, route, status chips, PNR mono, travel date, amount, **Change** + View quote  

### 8.5 Change booking drawer
- Amber honesty banner (mock reissue)  
- Booking summary  
- Radio: date / route / name  
- Get change quote · fee breakdown  
- Collect & confirm (mock) · Awaiting payment  

### 8.6 Plus
- Pagination  
- Failed row deep-link to quote  

**Exit:** Matches `6.png`; honesty banner never omitted.

---

## Phase 9 — Settings (org, FX, locale, deals, AI, domain)

**Refs:** `NewUIReference/7.png`

### 9.1 Tab bar
- Organization · Display · Deal codes · AI preferences · Custom domain · Notifications  

### 9.2 Organization
- Brand name, tagline, logo upload, primary color, contact  

### 9.3 Display
- Preferred display currency · charge currency (read-only INR) · locale · date/time format  

### 9.4 Deal codes
- Table + Add deal code  

### 9.5 AI preferences
- Opt-in toggle · preferred airlines · max stops · cabin  

### 9.6 Custom domain / white-label
- Stepper checklist (brand, logo, domain, DNS TXT with copy, production)  
- Link to ops checklist doc  

### 9.7 Notifications (plus)
- Email/WhatsApp prefs stubs if API thin  

**Exit:** Settings is a real control center matching `7.png`.

---

## Phase 10 — Money, CRM, packages, network, AI

**Refs:** Current wallet `currentui/5.png` + Home rail patterns · fill gaps not fully boarded in NewUI

### 10.1 Wallet & commissions
- Restyle KPI cards to tokens (Pending / Available / Settled)  
- Transactions table with mono amounts + status chips  
- Export CSV  

### 10.2 Payments
- List gateway payments; status chips; link to quote  

### 10.3 Customers / CRM
- List + detail timeline; quote/booking links; empty states  

### 10.4 Packages
- Agent catalog cards; admin create already exists — unify card chrome  

### 10.5 Network
- Sub-agents table + invite; GMV column  

### 10.6 AI Assistant
- Chat-style intent → search/draft; locale-aware; never invent fares  
- Entry from Home rail + nav  

**Exit:** Secondary ops pages share same density/tokens as primary flows.

---

## Phase 11 — Platform Admin

**Refs:** `NewUIReference/8.png`

### 11.1 Admin shell
- Dark Ink sidebar “TripOS Admin”  
- Nav: Overview, Agents, Bookings, Failures/Refunds, Payments, Suppliers, Partners, FX, Commissions, Analytics, Settings  

### 11.2 Overview
- L2B survival amber banner  
- KPIs: open failures, pending refunds, supplier health, active agents  
- Recent failed bookings table  
- Supplier health list  

### 11.3 Partners
- Apps table + Rotate key  
- Create form + one-time API key callout  

### 11.4 FX & Commissions
- Align existing `/admin/fx` and `/admin/commissions` to admin chrome  

### 11.5 Plus
- System logs stub or link to Sentry  
- Reports placeholder  

**Exit:** Admin feels distinct from agent; matches `8.png` hierarchy.

---

## Phase 12 — Marketing landing

**Refs:** `NewUIReference/9.png` · Current: `currentui/1.png`

### 12.1 Header
- TripOS wordmark · Product / For Agencies / How it Works / Pricing / Resources  
- EN/HI · Login · Request access  

### 12.2 Hero (brand-first)
- Full-bleed India travel atmosphere  
- TripOS as hero brand signal  
- One headline + one sentence + Login / Request access  
- **No** first-viewport stats strip  

### 12.3 Below fold
- Three value cards: Live honesty · Quote→WhatsApp→Pay · Wallet  
- How it works: Search → Quote → Collect → Confirm  

### 12.4 Footer
- Product / Resources / Legal · social · copyright  

**Exit:** Landing upgraded from minimal cards-only to `9.png` story without B2C clutter.

---

## Phase 13 — Mobile & responsive

**Refs:** `NewUIReference/10.png`

### 13.1 Bottom tabs
- Home · Search · Quotes · More  

### 13.2 Mobile Home
- Compact header (logo, agency, EN/HI, bell)  
- Alert cards · KPI pair · search widget · recent list  

### 13.3 Responsive rules
- Collapse left nav to drawer on &lt;1024px  
- Quote price panel becomes bottom sheet  
- Search selected rail becomes full-screen sheet  
- Tables → card stacks on small screens  

### 13.4 Plus
- Thumb-reachable primary CTAs  
- Safe-area padding  

**Exit:** Mobile Home matches `10.png`; critical flows usable on phone.

---

## Phase 14 — Cross-cutting polish, i18n, a11y, QA

### 14.1 Empty / loading / error
- Skeleton for tables and search rows  
- Localized empty copies  
- AppError toasts  

### 14.2 i18n pass
- EN/HI catalogs for all new chrome strings  
- Public quote Hindi layout  

### 14.3 Accessibility
- Focus rings = Focus token  
- Contrast on chips  
- Keyboard nav for drawers  

### 14.4 Motion
- PageTransition keep; drawer slide; selected offer pulse  

### 14.5 Visual QA checklist
- Side-by-side each NewUIReference frame vs implemented page  
- No purple / Inter-default / royal-blue regressions  
- Honesty badges present on inventory  

### 14.6 Performance
- Avoid layout shift on KPI load  
- Virtualize long search lists if &gt;100  

**Exit:** Signed visual QA sheet; production-ready FE.

---

## Phase 15 (optional buffer) — Stretch & partner-facing UI

Only after 1–14:

### 15.1 Partner developer portal (thin)
- Docs link + sandbox key instructions (admin remains source of truth)  

### 15.2 Advanced analytics charts on agent Home  
### 15.3 Notification center full page  
### 15.4 Print/PDF quote template visual parity  

---

## C. Suggested build order (calendar)

| Week | Phases | Outcome |
|---|---|---|
| 1 | 1–2 | Tokens + shell |
| 2 | 3–4 | Home + Search |
| 3 | 5–6 | Quotes list + detail |
| 4 | 7–8 | Public pay + Bookings/reissue |
| 5 | 9–10 | Settings + secondary ops |
| 6 | 11–12 | Admin + Marketing |
| 7 | 13–14 | Mobile + polish/QA |

---

## D. Phase tracking table

| Phase | Name | Owner | Status |
|---|---|---|---|
| 1 | Design system | | ☐ |
| 2 | App shell | | ☐ |
| 3 | Home | | ☐ |
| 4 | Search | | ☐ |
| 5 | Quotes list | | ☐ |
| 6 | Quote detail | | ☐ |
| 7 | Public quote | | ☐ |
| 8 | Bookings + Change | | ☐ |
| 9 | Settings | | ☐ |
| 10 | Money/CRM/Packages/AI | | ☐ |
| 11 | Admin | | ☐ |
| 12 | Marketing | | ☐ |
| 13 | Mobile | | ☐ |
| 14 | Polish / i18n / a11y | | ☐ |
| 15 | Stretch | | ☐ |

---

## E. Out of scope (do not add during this plan)

- Cabs / buses / holidays marketplace  
- Consumer reviews / SEO destination pages  
- Full live airline reissue (keep mock honesty)  
- NDC/LCC-specific UI until Phase 0 matrix unlocks  
- Replacing Partner API with agent JWT sharing  

---

*Master file for UI enhancement. Implementation should follow phases in order; update Status column as work ships. Companion visual source of truth: `docs/NewUIReference/`.*
