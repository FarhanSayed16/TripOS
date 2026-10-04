# TripOS — Impact Document

**Document type:** Business & product impact  
**Prepared / researched by:** Farhan Sayed  
**Date:** 2026-10-05  

---

## 1. Who benefits

| Stakeholder | Impact |
|---|---|
| **Travel agents / agencies** | One OS for search → quote → pay → book instead of WhatsApp + Excel + supplier portals |
| **Agency customers** | Clean branded quote + pay link; no exposure of agent net cost |
| **Platform (TripOS)** | Transaction visibility, L2B control, partner API for future B2C brands |
| **Operations** | Attention desk for failed bookings / paid-not-confirmed; admin L2B & supplier health |

---

## 2. Problem → outcome

| Before | After (TripOS) |
|---|---|
| Manual markup math | Quote with supplier → fee → markup → customer total |
| Payment chasing on chat | Payment link + status on quote/booking |
| “Did it book?” uncertainty | Worker confirm + PNR / failure reasons on Home & Bookings |
| Supplier look storms | Shopping cache + L2B meters + survival brakes |
| Opaque inventory truth | Live / Simulated / Mock badges |

---

## 3. Commercial model (planned)

From product planning docs (not all live in billing yet):

1. **Primary (near-term):** Transaction margin / commission on fulfilled bookings  
2. **Later:** SaaS subscription for agencies  
3. **Later:** White-label / Partner API / adjacent financial services  

Pilot1 focus remains **transacting agents**, not feature sprawl.

---

## 4. Engineering impact already delivered

| Capability | Why it matters |
|---|---|
| End-to-end mock commerce loop | Train pilots & prove UX without burning supplier L2B |
| TBO adapter spine (sim + live gate) | Path to real inventory without rewrite |
| Pay-time revalidate | Reduces fare-surprise after customer pays |
| Soft cancel + failure taxonomy | Safer ops when suppliers fail |
| Partner API (FC Phase 8) | Separate B2C product can plug in without forking TripOS |
| EN/HI + FX display | Fits Indian agency reality |
| Postman handoff pack | Leadership/QA can verify APIs without reading code |

---

## 5. Risk impact if we skip hardening

| Risk | Impact | Mitigation in product |
|---|---|---|
| Uncached live search | Supplier cutoff / cost | Redis shopping cache + indicative UI |
| Pay then fare change | Trust + refunds | Revalidate before pay & book |
| Pay then book fail | Stuck money | Attention desk + refund SOP |
| One org hammers search | Platform L2B collapse | Org brakes + survival mode |
| Local ticket files in prod | Data loss | Vault must be S3/R2 in production |
| AI open live search | L2B explosion | AI off by default; block on critical |

---

## 6. Metrics that matter

| Metric | Intent |
|---|---|
| Monthly Active Transacting Agents | North-star |
| Quotes → Paid → Confirmed conversion | Funnel health |
| Platform / org L2B ratio | Supplier relationship health |
| Failed booking rate + time-to-resolution | Ops quality |
| Partner API usage (when enabled) | Ecosystem growth |

Admin surfaces already expose analytics / L2B endpoints for these.

---

## 7. What leadership should treat as “not done yet”

Honest impact framing:

- **Product OS:** largely buildable and demoable on mock.  
- **Live commerce:** blocked on supplier credentials, hosted smoke, and payment test capture.  
- **Second live supplier:** commercially waived for now.  
- **Volt/Travclan:** not part of current impact plan.

---

## 8. Summary statement

TripOS’s impact is to turn Indian agency operations into a **reliable, honest, measurable** Agent OS—protecting both **agent trust** (money path) and **supplier relationships** (L2B)—while keeping a clean path for a **separate B2C brand** via Partner API.

---

*Prepared and researched by Farhan Sayed.*
