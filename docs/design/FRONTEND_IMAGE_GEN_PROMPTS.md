# TripOS — Frontend image-generation prompts

**Use with:** ChatGPT (DALL·E / image gen) or Gemini image generation  
**Companion:** [`FRONTEND_UX_PLAN.md`](./FRONTEND_UX_PLAN.md)

## How to run

1. Paste **Prompt 0 (system)** once at the start of the chat.  
2. Paste **Prompt 1, then 2, then 3…** one at a time. Ask for **one desktop frame (1440×900)** per prompt unless noted.  
3. After each image: reply “approved” or “revise: …” before the next frame.  
4. Optional: ask for a **mobile 390×844** variant of frames 2, 3, 5.

### Global negative constraints (repeat if the model drifts)

```text
Do NOT use: purple/indigo gradients, Inter/Roboto as the hero font, cream+#terracotta newspaper layouts,
royal blue SaaS chrome like TripCore/TravelPro clones, rainbow feature icons, emoji in the UI chrome,
fake airline logo walls, cab booking modules, heavy multi-layer drop shadows, glassmorphism, neon glow.
Do NOT invent a B2C storefront. This is a B2B agent OS named TripOS.
```

---

## Prompt 0 — System / design bible (paste first)

```text
You are designing TripOS, a B2B travel Agent Operating System used by Indian travel agencies.

Product facts:
- Agents search flights/hotels, build quotes with markup, send WhatsApp/pay links, manage bookings, wallet/commissions.
- Charge currency is usually INR; display FX may convert for browsing (must show footnote).
- Locales: English and Hindi.
- Inventory can be live, simulated, or mock — always badge honesty.
- No consumer OTA, no reviews, no cabs in V1.

Visual system (must follow exactly):
- Background: warm paper off-white (#F7F6F2)
- Surfaces: white panels with 1px cool-gray hairline borders, soft radius 12px, almost no shadow
- Primary accent: deep teal (#0D9488 range) for primary buttons and active nav
- Text: near-black ink with cool green undertone (#0F1C1A)
- Status: mint green confirmed, amber pending, coral failed
- Typography: distinctive geometric sans for UI (not Inter/Roboto/Arial); monospace for PNR, money, IDs
- Density: professional ops desk — calm, readable tables and list rows; not a marketing dashboard full of promo cards

Output style for every frame:
- High-fidelity UI mockup, desktop web app
- Annotated only if I ask; otherwise clean UI
- English UI labels (we will localize later)
- Brand wordmark “TripOS” visible in the shell
```

---

## Prompt 1 — Design system board

```text
Create a single design-system board for TripOS (desktop, landscape).

Include labeled swatches: Ink, Paper, Surface, Teal, Coral, Amber, Mint, Focus, Line.
Include type specimens: page title, section title, body, caption, mono money/PNR.
Include components: primary/secondary/ghost/destructive buttons; text input; status chips (Confirmed, Pending, Failed, Live, Simulated, Mock); table header row; nav item active/inactive; alert banner (amber warning).

Layout: clean white/paper background, grid of specimens, TripOS wordmark top-left.
No app screenshot yet — components only.
```

---

## Prompt 2 — Agent shell + Home dashboard

```text
TripOS agent desktop app shell + Home (1440×900).

LEFT NAV (240px, paper/ink contrast, not navy-blue SaaS):
Sections: Workspace (Home active, Search, AI Assistant), Operations (Quotes, Bookings, Packages, Customers, Network), Money (Wallet, Payments), System (Settings).
Footer: agent name + Logout. No “View Plans” promo card.

TOP BAR: page title “Home”, subtle org brand name, locale EN|HI toggle, notification bell.

MAIN:
1) Greeting: “Good morning, Sahil” + one-line subtitle “Attention desk for today’s bookings.”
2) Attention strip (coral/amber): Failed bookings · Paid awaiting confirm — with counts.
3) KPI row (4 flat panels): Bookings · GMV ₹ · Wallet ₹ · Customers — small trend optional, no rainbow icons.
4) Compact flight search widget (From/To/Date/Pax + Deal code field + Search Flights CTA in teal).
5) Recent bookings table: Customer, Route, Status chip, PNR mono, Amount, “Open quote”.

RIGHT RAIL (narrow, Home only): Wallet balance + Add money; 3 notification lines.

Follow TripOS visual system from Prompt 0. No cab tabs. No purple.
```

---

## Prompt 3 — Search results (flights)

```text
TripOS agent Search Flights results page (1440×900), same left nav with Search active.

TOP: search summary “DEL → BOM · 15 Nov · 1 adult” + Edit search.
Filters row: Sort (Recommended/Price/Duration/Stops), Max stops, Airline, Max price.
Footnote: “Showing USD display · Charge currency INR · Rate as of …” (small muted text).

RESULTS: vertical list rows (not big hotel cards). Each row shows:
- Airline + title
- Fare family chip (Basic / Flex / Premium)
- Inventory badge: Live | Simulated | Mock
- Segment lines: DEL→BOM · MK101 · mkt MK (op AI) · 08:00
- Duration / stops
- Deal code chip if present
- Price: large display amount + smaller “INR charge” if different
- Select button

Include one selected row state (teal outline). Empty promo clutter forbidden.
```

---

## Prompt 4 — Quote detail (markup ladder + extras)

```text
TripOS Quote detail page /app/quotes/[id] (1440×900).

Header: Quote ID mono, status Ready, customer name, Valid until.
LEFT column:
- Flight offer summary with fare family + segments
- Fare rules link
- Ancillaries panel: baggage/meal selected lines
- Seat selection summary (e.g. 12A)
- Passengers list

RIGHT column sticky price panel (critical):
Price ladder with + signs:
Supplier cost
+ Platform fee
+ Agent markup (editable input)
+ Extras
= Customer total (large)
Display FX line under total if enabled
CTA stack: Mark ready / Create pay link / Send WhatsApp / Cancel

Show inventory_mode badge. Calm ops aesthetic, teal CTAs, coral Cancel outline.
```

---

## Prompt 5 — Public customer quote (`/q/[token]`)

```text
TripOS public quote page for the traveler (no agent nav). Desktop 1440×900, centered max-width ~720px.

Org brand name + optional logo (white-label).
Quote summary: route, dates, passengers (no supplier cost, no agent markup breakdown).
Total due with display currency and footnote “You will be charged in INR”.
Primary teal Pay button.
Secondary: View fare conditions.
Locale switcher EN | हिन्दी top-right.
Warm paper background, generous whitespace, trustworthy and simple — not a flashy OTA.
```

---

## Prompt 6 — Bookings ledger + Change (reissue)

```text
Split concept into ONE frame with two zones OR a clear primary Bookings page:

A) Bookings ledger table: Customer, Status chips, PNR mono, Date, actions “Change” + “View quote”.

B) Overlay or side panel “Change booking” with amber honesty banner:
“Mock reissue scaffold — fee estimate only. Supplier PNR/tickets are not rewritten automatically.”
Fields: Change type (Date/Route/Name), New date, Get quote, Diff ₹1500, buttons Collect & confirm (mock) / Awaiting payment.

Same TripOS shell. No fake “instant airline reissue success” celebration.
```

---

## Prompt 7 — Settings (currency, locale, deal codes, white-label)

```text
TripOS agent Settings page (1440×900).

Tabs or sections:
1) Organization — brand name, primary color, logo
2) Display — Preferred currency (INR/USD/AED…), Default locale EN/HI
3) Deal codes — list of corp/promo codes + add field
4) AI preferences — opt-in toggle, preferred airlines, max stops
5) Custom domain / white-label checklist — steps with done/pending: Brand, Logo, Domain added, DNS TXT, Production

Keep forms quiet; teal save button; monospace for TXT record hint tripos-verify=…
```

---

## Prompt 8 — Admin overview + Partners

```text
TripOS Platform Admin (distinct from agent): darker ink sidebar labeled “TripOS Admin”.

MAIN Overview:
- Amber/critical banner: “Global L2B survival mode active — cache TTL widened”
- Cards: Open failures, Pending refunds, Supplier health
- Mini table of recent failed bookings with failure labels

SECOND panel or lower section Partners:
Table of partner apps: Name, Key prefix, Env test/live, Active, Rotate key
Create form: Org select, Name, Webhook URL — after create show one-time API key in amber callout “Copy now — not shown again”

No agent-style teal marketing chrome; still use TripOS tokens, more austere.
```

---## Prompt 9 — Marketing landing (`/`)

```text
TripOS marketing landing page (desktop). Brand-first composition.

FIRST VIEWPORT ONLY should contain:
- TripOS wordmark as the hero-level brand (largest text)
- One headline about Agent OS / B2B agencies (not “endless possibilities” hype)
- One short supporting sentence
- CTA group: Login · Request access
- One full-bleed atmospheric travel image (edge-to-edge background), no floating cards on the hero, no stats strip in the first viewport

Below fold (second screen in same image or note “scroll”):
- Three feature blocks: Live inventory honesty, Quote → WhatsApp → Pay, Wallet & commissions
- How it works: Search → Quote → Collect → Confirm
- Footer

Avoid purple gradients, avoid fake partner logo walls, avoid Inter, avoid TripCore blue clone.
```

---

## Prompt 10 — Mobile agent shell (optional)

```text
TripOS agent mobile (390×844).

Bottom tabs: Home · Search · Quotes · More.
Home: greeting, attention alert, 2 KPI chips, primary Search CTA, recent list.
Use same TripOS tokens. Thumb-friendly teal button. No hamburger-only dead ends.
```

---

## Master “one-shot” prompt (if you want a single long paste)

Use only if the tool allows a long brief; otherwise prefer Prompts 0→9 sequentially.

```text
Design a complete TripOS B2B Agent OS UI kit and key screens as a multi-panel presentation board (or separate images if needed).

Screens required: (1) Design tokens board (2) Agent Home (3) Flight search results with fare families, codeshare segments, FX footnote (4) Quote detail with supplier→markup→customer price ladder and ancillaries (5) Public pay quote (6) Bookings + mock reissue change panel with honesty banner (7) Settings currency/locale/deal codes/white-label (8) Admin L2B + Partner API keys (9) Marketing hero brand-first.

Visual system: warm paper #F7F6F2, ink text, teal primary #0D9488, coral/amber/mint status, hairline borders, minimal shadow, geometric sans + mono for money/PNR. Not generic blue SaaS travel admin. Not purple. Not cream/terracotta editorial. Not B2C OTA. Product name TripOS always visible.

Indian B2B agency context; INR charge currency; optional display FX; EN/HI. Inventory badges Live/Simulated/Mock required on offers.
```

---

## Revision snippets (paste after an image)

**Too blue / SaaS clone**

```text
Revise: replace royal blue with deep teal accent; lighten chrome to warm paper; reduce shadows; keep TripOS wordmark.
```

**Too much marketing clutter**

```text
Revise: remove promo cards, fake stats, rainbow icons; denser ops table aesthetic; one primary CTA per section.
```

**Missing honesty**

```text
Revise: add Live/Simulated/Mock badges and INR charge footnote; add mock-reissue warning banner where change booking is shown.
```

**Wrong product**

```text
Revise: this is B2B agent software, not a consumer flight booking website. Remove traveler reviews, deals carousels, and cab booking.
```

---

## Mapping prompts → plan sections

| Prompt | Plan section |
|---|---|
| 0–1 | §1 Design system |
| 2 | §2.2 Home |
| 3 | §2.2 Search + §3 FX/families/segments |
| 4 | §2.2 Quote + §4 Flow C |
| 5 | §2.3 Public |
| 6 | §2.2 Bookings/Change |
| 7 | §2.2 Settings |
| 8 | §2.4 Admin |
| 9 | §2.1 Marketing |
| 10 | Mobile parity |

---

*After images are approved, implement against `FRONTEND_UX_PLAN.md` §9 order — do not redesign from scratch in code without updating this plan.*
