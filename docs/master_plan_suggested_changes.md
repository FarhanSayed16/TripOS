# TripOS Master Plan — Suggested Changes

### Fresh review of the updated [tripos-master-plan.md](./tripos-master-plan.md)

**Status: APPLIED (2026-09-16)** — All 14 items folded into `tripos-master-plan.md`.

**V1 decisions locked while applying:**
- Outbox = **DB-polling** (no Redis required for pilot)
- Quotes = **one product type per quote** (flight-only or hotel-only)
- Expiry defaults = **4h flights / 12h hotels**

Keep this file as an audit trail only.

---

## 🔴 Should Fix Before Build
*(Originally proposed — now applied)*

---

### 1. Phase 20 — Outbox worker needs Redis/broker but Upstash is "optional"

**Location:** [Phase 20, lines 687–707](file:///d:/TripOS/docs/tripos-master-plan.md#L687-L707)

**Problem:** Phase 20 says the worker uses "Upstash Redis if Celery; or documented alternative." But Phase 2 (Docker) and Phase 27 (Deploy) both treat Upstash as optional ("skip if not yet"). If you're using Celery for the outbox worker, Redis is **required**, not optional. There's no clear decision on whether to use Celery+Redis or a simpler DB-polling outbox.

**Suggested change:** Add a decision item to Phase 20:

```markdown
### 20.2 Worker app
- [ ] **Decide:** Celery + Upstash Redis **or** DB-polling outbox (simpler for pilot)
- [ ] If Celery: Upstash Redis required from this phase onward (update Phase 2/27)
- [ ] If DB-poll: simple `SELECT pending LIMIT N FOR UPDATE SKIP LOCKED` loop; no Redis dependency
- [ ] Worker entry on Render
- [ ] Handlers registered
```

---

### 2. Phase 18 — No gate for quote expiry at webhook time

**Location:** [Phase 18, lines 648–653](file:///d:/TripOS/docs/tripos-master-plan.md#L648-L653)

**Problem:** 18.2 covers `payment_captured_quote_expired` as a status, which is good. But it doesn't specify **when** expiry is checked. The Razorpay payment link itself doesn't expire when the quote expires — the customer can still pay via the Razorpay link after the quote's `valid_until` has passed. You need to decide:

- Block at **pay-link creation** time ✅ (already in 18.1)
- Block at **webhook capture** time — the webhook fires, payment is captured by Razorpay, but your system discovers the quote expired. Now what? Auto-refund? Manual?

**Suggested change:** Add to 18.2:

```markdown
- [ ] Set Razorpay payment link expiry to match quote `valid_until` (or slightly after)
- [ ] If gateway link cannot expire: on webhook, check quote expiry → `payment_captured_quote_expired` → queue for manual refund decision
```

---

### 3. Phase 14 — No multi-item quote rules defined

**Location:** [Phase 14, lines 536–559](file:///d:/TripOS/docs/tripos-master-plan.md#L536-L559)

**Problem:** Can a single quote contain both a flight AND a hotel? The plan doesn't say. This matters because:
- Pax requirements differ (flight needs DOB/passport; hotel needs guest name only)
- If one item's revalidation fails, does the entire quote fail or just that item?
- Markup may be set per-item or per-quote

**Suggested change:** Add to 14.1:

```markdown
- [ ] **V1 rule:** One product type per quote (flight-only or hotel-only) OR mixed with per-item pax rules
- [ ] If mixed: revalidation failure on one item blocks entire pay (V1 simplicity)
- [ ] Markup per item (not per quote) for future flexibility
```

---

### 4. Phase 21 — No retry limit for booking confirm job

**Location:** [Phase 21, lines 711–736](file:///d:/TripOS/docs/tripos-master-plan.md#L711-L736)

**Problem:** 21.1 says "On timeout → retry then `booking_failed_supplier_timeout`" but doesn't specify:
- How many retries before giving up?
- What's the backoff interval?
- After max retries, does it go to `needs_manual_support` or `booking_failed_supplier_timeout`?

**Suggested change:** Add to 21.1:

```markdown
- [ ] Retry policy: max **3 attempts**, exponential backoff (30s, 2min, 10min)
- [ ] After max retries: `booking_failed_supplier_timeout` + `needs_manual_support`
- [ ] Each retry is a new outbox job (not blocking the worker)
```

---

### 5. Phase 9 — No token storage strategy specified

**Location:** [Phase 9, line 421](file:///d:/TripOS/docs/tripos-master-plan.md#L421)

**Problem:** Line 421 says "No long-lived tokens in localStorage (prefer memory + httpOnly refresh via BFF)" — good. But this means on page refresh, the access token in memory is lost. The plan needs to address:
- Does the BFF silently call `/refresh` on every page load?
- What happens if refresh fails (redirect to login)?
- Is there a "session restore" loading state in the UI?

**Suggested change:** Expand 9.2:

```markdown
- [ ] On page load: BFF calls `/refresh` silently → new access token in memory
- [ ] If refresh fails (expired/revoked): redirect to `/login`
- [ ] Show brief loading state during session restore (not a flash of login page)
```

---

## 🟡 Should Fix Before Pilot (Phase 29)

---

### 6. Phase 26 — Missing test: pax-less quote can't create pay link

**Location:** [Phase 26, lines 839–860](file:///d:/TripOS/docs/tripos-master-plan.md#L839-L860)

**Problem:** Phase 14 and 18 both enforce the "pax gate" but Phase 26 (E2E hardening) doesn't test it.

**Suggested change:** Add to 26.1:

```markdown
- [ ] Quote without pax → create-pay-link returns error (pax gate enforced)
```

---

### 7. Phase 27 — No rollback strategy for failed deploys

**Location:** [Phase 27, lines 864–900](file:///d:/TripOS/docs/tripos-master-plan.md#L864-L900)

**Problem:** Phase 27 covers deploy but not rollback. If a bad API deploy breaks payments during pilot:
- Can you rollback to the previous Render revision?
- Do migrations support downgrade (`alembic downgrade -1`)?
- Vercel has instant rollback — is the team aware?

**Suggested change:** Add to 27.1:

```markdown
- [ ] Document Render rollback (previous deploy) procedure
- [ ] Alembic migrations: ensure every migration has a `downgrade()` function
- [ ] Vercel: note instant rollback to previous deployment
```

---

### 8. Phase 29 — No agent training material mentioned

**Location:** [Phase 29, lines 932–950](file:///d:/TripOS/docs/tripos-master-plan.md#L932-L950)

**Problem:** 29.1 says "Training: Search → Quote → wa.me → Pay" but doesn't mention how:
- A short video walkthrough?
- A one-page PDF guide?
- Live demo call per agent?

For Indian travel agents who may not be tech-forward, training format matters.

**Suggested change:** Add to 29.1:

```markdown
- [ ] Create 1-page quick-start PDF or Notion doc (Search → Quote → Send → Booking)
- [ ] Record 3–5 min screen recording walkthrough (optional but high-impact)
- [ ] Schedule live demo with first 3 agents (Nilesh + Farhan)
```

---

### 9. Part D — Missing cross-cutting checklist for Public pages

**Location:** [Part D, lines 1210–1234](file:///d:/TripOS/docs/tripos-master-plan.md#L1210-L1234)

**Problem:** D1 covers backend modules, D2 covers Agent OS pages, but there's no checklist for **Public customer pages** (`/q/[token]`, pay return, status). These have different rules — no login, no agent data leak, mobile-first.

**Suggested change:** Add:

```markdown
## D5. Every Public customer page must include
- [ ] No agent cost / supplier cost / internal IDs visible
- [ ] Works without login (token-only access)
- [ ] Mobile-first layout with sticky Pay CTA
- [ ] Graceful expired/invalid token handling (not raw 404)
- [ ] Agency brand_name displayed if set
```

---

### 10. Phase 25 — No sandbox booking lifecycle test

**Location:** [Phase 25, lines 816–835](file:///d:/TripOS/docs/tripos-master-plan.md#L816-L835)

**Problem:** 25.3 exit says "Sandbox book path documented (even if limited)" — but doesn't require actually testing the full book → status → cancel cycle in sandbox. Some supplier sandboxes have quirks (delayed status, different cancel rules).

**Suggested change:** Add to 25.1:

```markdown
- [ ] Test full lifecycle in sandbox: search → revalidate → book → get_status → cancel (if supported)
- [ ] Document sandbox quirks / limitations (e.g., "TBO sandbox doesn't return real PNR")
```

---

## 🟢 Nice to Have / Polish

---

### 11. Phase 0.2b — Quote expiry "4h" may be too short for hotels

**Location:** [Line 121](file:///d:/TripOS/docs/tripos-master-plan.md#L121)

**Problem:** 4-hour default works for flights (which price-change frequently), but hotel rates are typically stable for 24–48 hours. A single default may cause unnecessary expired quotes for hotel-only bookings.

**Suggested change:** Consider:

```markdown
- [ ] Default expiry: **4h for flights, 12h for hotels** (or single 4h with agent-extend for hotels)
```

---

### 12. Part B — Phase overview table could include week estimates

**Location:** [Lines 44–88](file:///d:/TripOS/docs/tripos-master-plan.md#L44-L88)

**Problem:** The phase table shows phase number, name, and version band — but no time estimate. The implementation plan has week ranges, but they're not reflected here. Even rough estimates help Farhan plan.

**Suggested change:** Add a 4th column:

```markdown
| Phase | Name | Version band | ~Weeks |
|---|---|---|---|
| 0 | Team, commercial, credentials lock | Foundation | 0.5 |
| 1 | Monorepo & engineering standards | Foundation | 0.5 |
| 2 | Local environments & docker | Foundation | 0.5 |
| 3–4 | Backend core + schema | Foundation | 1 |
| 5–6 | Auth + Orgs | V1 | 1 |
| 7–8 | Frontend tokens + layouts | V1 | 1 |
| 9 | Auth frontend | V1 | 0.5 |
| 10 | CRM | V1 | 0.5 |
| 11–13 | Inventory + Search UI | V1 | 2 |
| 14–17 | Quotes + Messaging + Public | V1 | 2 |
| 18–21 | Payments + Worker + Bookings | V1 | 2 |
| 22–24 | Bookings UI + Audit + Admin | V1 | 1.5 |
| 25–28 | Real adapter + E2E + Deploy + Security | V1 | 2 |
| 29–31 | Pilot + Fixes + Gate | V1/V1.5 | 4 |
```

---

### 13. Phase 17 — No SEO/social meta for public quote pages

**Location:** [Phase 17, lines 610–632](file:///d:/TripOS/docs/tripos-master-plan.md#L610-L632)

**Problem:** When agents share `/q/[token]` links on WhatsApp, a rich preview (OG title, description, image) significantly increases customer trust and click-through. Without OG tags, WhatsApp shows a bare URL.

**Suggested change:** Add to 17.1:

```markdown
- [ ] OG meta tags on `/q/[token]`: title = "Travel Quote from {agency_name}", description = summary
- [ ] OG image: auto-generated or static branded card (can be simple)
```

---

### 14. Part E — Parallel track for "commercial answers" is missing

**Location:** [Part E, lines 1238–1245](file:///d:/TripOS/docs/tripos-master-plan.md#L1238-L1245)

**Problem:** Phase 0.2 has commercial questions (merchant of record, invoice party, platform fee rule, settlement path). These are Nilesh-led and could block Phases 14 (Quotes) and 18 (Payments) if not answered early enough. The parallel track table doesn't call this out.

**Suggested change:** Add a row:

```markdown
| Nilesh commercial answers (0.2) | Phases 1–10 | Blocking for Phase 14 (quotes pricing) and Phase 18 (payment merchant) |
```

---

## Summary

| # | Change | Severity | Phase | Status |
|---|---|---|---|---|
| 1 | Decide Celery+Redis vs DB-poll outbox | 🔴 | 20 | **Applied — DB-poll V1** |
| 2 | Quote expiry check at webhook + Razorpay link expiry | 🔴 | 18 | **Applied** |
| 3 | Multi-item quote rules | 🔴 | 14 | **Applied — one product type V1** |
| 4 | Booking confirm retry limit + backoff | 🔴 | 21 | **Applied** |
| 5 | Token storage / session restore | 🔴 | 9 | **Applied** |
| 6 | E2E test for pax gate | 🟡 | 26 | **Applied** |
| 7 | Deploy rollback strategy | 🟡 | 27 | **Applied** |
| 8 | Agent training material | 🟡 | 29 | **Applied** |
| 9 | Cross-cutting checklist for public pages | 🟡 | Part D | **Applied** |
| 10 | Sandbox full lifecycle test | 🟡 | 25 | **Applied** |
| 11 | Hotel-specific quote expiry default | 🟢 | 0.2b | **Applied — 4h/12h** |
| 12 | Week estimates in phase table | 🟢 | Part B | **Applied** |
| 13 | OG meta tags for public quote | 🟢 | 17 | **Applied** |
| 14 | Commercial answers as parallel track | 🟢 | Part E | **Applied** |
