# TripOS — Frontend UX Plan & Design Spec

**Product:** TripOS B2B Agent OS (not a B2C storefront)  
**Audience:** Travel agents + agency admins + platform admins  
**Purpose of this doc:** (1) Single source of truth for what every screen should show and how it should feel. (2) Checklist to verify the current Next.js app against backend (FC 0–8). (3) Input for ChatGPT / Gemini image generation — see companion [`FRONTEND_IMAGE_GEN_PROMPTS.md`](./FRONTEND_IMAGE_GEN_PROMPTS.md).

**Implementation master (phased build vs current + NewUIReference):** [`FRONTEND_UI_ENHANCEMENT_MASTER_PLAN.md`](./FRONTEND_UI_ENHANCEMENT_MASTER_PLAN.md) — **use this to execute UI work.**

**Owners:** Farhan (FE build) · design review with Sahil/Nilesh for commercial surfaces  
**Last updated:** 2026-09-29

---

## 0. How to use this plan

| Step | Action |
|---|---|
| 1 | Read **Design system** (§1) — do not invent ad-hoc blues/purples |
| 2 | Use **Screen inventory** (§2) as the checklist vs `apps/web` |
| 3 | Use **Feature → UI map** (§3) to confirm FC APIs have a home in the UI |
| 4 | Paste prompts from the companion file into ChatGPT/Gemini **one frame at a time** |
| 5 | Mark gaps in §5; only then change React code |

**Non-goals:** Building a consumer OTA site, reviews/UGC, SEO destination pages (those belong in a separate B2C brand via Partner API).

---

## 1. Design system (TripOS visual language)

### 1.1 What we keep from product today

Existing tokens (styleguide): **Ink**, **Paper**, **Teal**, **Coral**, **Amber**, **Mint**, **Focus**, **Line**.

TripOS should feel like a **calm operations desk for Indian travel agents** — not a generic “blue SaaS travel” dashboard (TripCore / TravelPro style references). Those references are useful for **layout ideas only** (KPI row, search widget, price ladder). Do **not** copy:

- Default royal/vibrant blue as brand primary
- Rainbow multi-color feature icons
- Heavy drop-shadow card stacks
- “Grow your business / View plans” promo clutter in the nav
- Fake airline logo walls on marketing unless contracted

### 1.2 Recommended visual direction (for redesign + image gen)

| Token | Role | Guidance |
|---|---|---|
| **Ink** `#0F1C1A` (approx) | Text, sidebar, headers | Near-black with a cool green undertone |
| **Paper** `#F7F6F2` | App chrome background | Warm off-white, not pure white flood |
| **Surface** `#FFFFFF` | Panels / tables | Flat; 1px `Line` border; **no** multi-layer shadows |
| **Teal** | Primary actions, active nav | Single brand accent — buttons, links, focus rings |
| **Coral** | Destructive / failed bookings | Failures, cancel, alerts |
| **Amber** | Pending / warn / L2B warn | Soft caution, never neon |
| **Mint** | Confirmed / success | Status chips only |
| **Focus** | Keyboard / active field | Slightly brighter than Teal |

**Typography**

- UI: one confident sans (e.g. **DM Sans** or **Söhne-like** geometric) — avoid Inter/Roboto defaults in mockups when possible
- Numbers / PNR / money: tabular mono (e.g. **JetBrains Mono** or **IBM Plex Mono**)
- Hindi locale: same family with Noto Sans Devanagari fallback; never shrink Hindi to fit English layouts

**Layout rules**

- Desktop agent: **left nav (240px) + main**; optional **right rail only on Home** (wallet + attention), not on every page
- Dense tables OK for bookings/quotes; search results are **list rows**, not hotel-OTA card grids
- **One job per page** — don’t put markup engine + seat map + CRM on one scroll
- Mobile: bottom tab bar (Home / Search / Quotes / More) — already partially present; keep parity

**Motion**

- Page enter: short fade/slide (existing `PageTransition`)
- Offer select / quote ready: subtle confirm pulse on primary CTA
- Avoid decorative parallax and hero animations inside the app shell

### 1.3 Taken from reference images (structure only)

Useful patterns to adapt:

1. **Home:** greeting + KPI strip + embedded search + recent bookings  
2. **Search:** tabbed Flights / Hotels (Cabs **out of scope** for V1)  
3. **Markup honesty:** supplier → platform fee → agent markup → customer total (we already have quote line items; surface this clearly)  
4. **Marketing landing:** hero + how-it-works + CTA (keep TripOS brand; rewrite copy for Agent OS)

Ignore from references: Cabs module, fake “Top Destinations” photo bars unless we have real analytics, dark-blue TravelPro chrome, multi-color icon candy.

---

## 2. Screen inventory (current routes + intended UX)

### 2.1 Auth & marketing

| Route | Purpose | UX intent |
|---|---|---|
| `/` | Marketing | Brand-first hero (TripOS name large), one headline, one CTA “Request access / Login”, no fake stats wall |
| `/login` `/signup` `/verify` `/forgot-password` `/reset-password` | Auth | Quiet paper background; teal primary; clear error states (localized EN/HI) |

### 2.2 Agent app (`/app/...`)

| Route | Purpose | Must show |
|---|---|---|
| `/app` | Home / attention desk | Greeting; **attention strip** (failed / pending / paid-awaiting); KPI chips (bookings, GMV if available, wallet, customers); quick search CTA; recent quotes/bookings |
| `/app/search` | Inventory search | Flight/Hotel tabs; origin/dest/date/pax; **deal code**; filters (stops, airline, price, sort); offer rows with **fare family**, **segments (mkt vs op)**, inventory mode badge (live/sim/mock), FX display amount + footnote |
| `/app/ai` | Copilot | Natural language → search/draft; show locale; never invent prices |
| `/app/quotes` | Quote list | Status filters; customer; totals in display + charge currency |
| `/app/quotes/new` | Build quote | Selected offers cart; markup inputs; extras summary |
| `/app/quotes/[id]` | Quote detail (canonical booking home) | Items + extras; fare rules; passengers; pay link; cancel; refunds; audit; seat/ancillary panels when enabled |
| `/app/quotes/[id]/send` | Send | WhatsApp/email preview; locale templates |
| `/app/bookings` | Ledger | Status chips; PNR; **Change** for confirmed; link to quote |
| `/app/bookings/[id]/change` | Reissue scaffold | Honest **mock/SOP** banner; change type; quote diff; confirm |
| `/app/customers` `/app/customers/[id]` `/app/crm` `/app/crm/[id]` | CRM | Customer profile; timeline; quotes linked |
| `/app/packages` | Packages | Browse/publish packages for agents |
| `/app/network` | Sub-agents | Master/sub GMV; invite |
| `/app/wallet` `/app/payments` | Money | Wallet summary; commission pending/available; payment list |
| `/app/followups` | Follow-ups | Task list |
| `/app/settings` | Org/user | Branding, **preferred currency**, **locale**, **deal codes**, AI prefs opt-in, domains/white-label checklist link |
| `/app/more` | Overflow | Mobile nav overflow |

### 2.3 Public customer surfaces

| Route | Purpose | Must show |
|---|---|---|
| `/q/[token]` | Public quote | Sanitized offer; **display currency** + charge footnote; pay CTA; locale |
| `/q/[token]/status` | Post-pay status | Booking outcome without agent costs |
| `/quote/[id]` | Legacy/public alias | Align with `/q/[token]` behavior |

### 2.4 Platform admin (`/admin/...`)

| Route | Purpose | Must show |
|---|---|---|
| `/admin` | Overview | Ops health; L2B survival banner if critical |
| `/admin/agents` | Orgs | Approve/reject |
| `/admin/bookings` `/admin/failures` `/admin/payments` | Ops | Failures with reason labels; refunds |
| `/admin/suppliers` | Supplier health | Circuit, latency, offer counts |
| `/admin/fx` | FX rates | CRUD display rates; charge currency note |
| `/admin/commissions` | Settle | Table + CSV export |
| `/admin/partners` | Partner apps | Create key (show once); rotate; usage/L2B |
| `/admin/packages` `/admin/branding` `/admin/analytics` | Content/ops | Keep lean |

---

## 3. Feature → UI map (backend must be visible)

| Backend capability | Where it appears in UI | Done if… |
|---|---|---|
| Live / simulated / mock inventory | Offer badge + search footnote | Agent never mistakes SIM for live |
| Fare families | Offer row + family compare on quote | Basic/Flex/Premium distinguishable |
| Ancillaries / seats | Quote detail panels | Add bag/meal/seat; totals update |
| Fare rules | Quote + search secondary action | Cancel/change text readable |
| Cancel + refund | Quote detail | Soft-fail supplier cancel still shows cancelled + ops note |
| Display FX | Search, quote, public quote | Footnote “charge INR” when display ≠ charge |
| EN/HI | Settings + Accept-Language + catalogs | Toggle locale; Hindi strings on agent + public |
| Deal codes | Search form + Settings | Code applied shows on offer |
| Segments / codeshare | Offer row | `mkt XX (op YY)` visible |
| Reissue | Bookings → Change | Mock banner always visible |
| White-label checklist | Settings / domains | Steps + TXT hint |
| Partner API | Admin → Partners only | No agent JWT shared to B2C |
| L2B brakes | Admin banner; agent 429 message | Clear copy, not raw error |
| AI prefs | Settings + AI search | Opt-in only |

---

## 4. Key interaction flows (frame order for design)

### Flow A — Search → Quote → Pay → Booked

1. Home → Search Flights  
2. Results with family + segments + FX  
3. Select offer(s) → New quote → set markup + extras  
4. Passengers → Mark ready → Send / Pay link  
5. Public quote pay  
6. Booking confirmed on quote + bookings ledger  

### Flow B — Failure / cancel / refund

1. Failed booking attention on Home  
2. Quote shows failure label + support path  
3. Cancel → status cancelled; refund requested chip if paid  

### Flow C — Markup transparency (agent)

On quote item / price panel always show ladder:

`Supplier cost → Platform fee → Agent markup → Extras → Customer total`  
(+ display conversion line if FX on)

### Flow D — Admin ops morning

1. L2B banner if critical  
2. Failures queue  
3. Commissions settle + CSV  
4. Partners / FX as needed  

---

## 5. Frontend gap checklist (verify against live app)

Use this as a QA pass. Mark each ☐ / ☑.

### Visual / UX

- [ ] Consistent Ink/Teal/Paper tokens on all agent pages (no random blue primary)
- [ ] No purple / cream-serif / newspaper aesthetics
- [ ] Tables readable; empty states with one CTA
- [ ] Loading skeletons on search, quotes, bookings
- [ ] Error toasts use localized AppError messages

### Feature completeness (likely gaps to design for)

- [ ] Settings: deal codes editor + AI preferences toggles  
- [ ] Search: deal code field polish + segment lines on every flight row  
- [ ] Quote: seat map + ancillaries panel polish (Phase 6)  
- [ ] Quote: fare rules drawer  
- [ ] Public quote: HI locale + FX footnote  
- [ ] Home: real KPIs wired (not placeholder)  
- [ ] Admin partners / commissions / FX discoverable in nav  
- [ ] Reissue page honesty banner (mock)  
- [ ] White-label checklist UI  

### Out of scope for this FE plan

- Cabs  
- B2C catalog / reviews  
- Full live NDC/LCC UIs (flags off until Phase 0 matrix)

---

## 6. Information architecture (nav)

```text
Agent
├── Workspace: Home · Search · AI
├── Operations: Quotes · Bookings · Packages · Customers · Network
├── Money: Wallet · Payments
└── System: Follow-ups · Settings · More

Admin
├── Overview · Analytics · Agents
├── Ops: Bookings · Failures · Payments · Suppliers
├── Commercial: Commissions · FX · Packages · Branding
└── Platform: Partners
```

---

## 7. Content & microcopy principles

- Prefer verbs agents use: Search, Quote, Send, Collect, Cancel, Change  
- Always say **display** vs **charge** when currencies differ  
- Never hide `inventory_mode`  
- Reissue: “Mock estimate — supplier ticket not rewritten”  
- Partner keys: “Shown once — store securely”  

---

## 8. Deliverables from image generation

After running prompts in [`FRONTEND_IMAGE_GEN_PROMPTS.md`](./FRONTEND_IMAGE_GEN_PROMPTS.md), collect:

1. Design system board (colors, type, components)  
2. Agent shell + Home  
3. Search results  
4. Quote detail (markup ladder + extras)  
5. Public quote  
6. Bookings + Change (reissue)  
7. Admin overview + Partners  
8. Marketing landing  

Name files `TripOS-FE-01-…png` and attach to this folder or Figma later.

---

## 9. Implementation order (after designs approved)

1. Token pass (CSS variables + typography) across agent shell  
2. Home KPI + attention polish  
3. Search results density (families, segments, FX, deal code)  
4. Quote detail (ladder, extras, fare rules, cancel)  
5. Settings (currency, locale, deal codes, white-label)  
6. Admin partners/commissions/FX polish  
7. Public quote EN/HI + FX  
8. Marketing landing refresh  

---

*This plan is the FE counterpart to `flight-commerce-implementation-plan.md`. Backend FC 0–8 scaffolds are assumed available; this doc owns presentation and verification.*
