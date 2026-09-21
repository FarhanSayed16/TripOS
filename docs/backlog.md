# TripOS Backlog

This document serves as the master backlog for future enhancements and features, organized by target versions.

## Ticket Format
Every idea must include the following details:
- **Title:** Brief description of the feature
- **Requester:** Who asked for this? (e.g., Agent, Admin, Farhan)
- **Version Tag:** Target release (e.g., V1.5, V2, V3)
- **Effort Estimate:** (Low / Medium / High)
- **Priority:** (P1 - Critical, P2 - High, P3 - Medium, P4 - Low)

---

## New Ideas (Triage)
*Empty after Sprint T triage (2026-09-19).*

---

## V1.5 Queue (Short-term Polish)
- [ ] ENH-02 WhatsApp message presets (Requester: Agents, Effort: Low, P2)
- [ ] ENH-03 Phone merge UX (Requester: Agents, Effort: Medium, P2)
- [ ] ENH-06 Next.js middleware for `/app` `/admin` (Requester: Farhan, Effort: Low, P2)
- [ ] Settings page (replace ComingSoon) (Requester: Agents, Effort: Medium, P2)
- [ ] Hosted smoke execution + secrets pack (Requester: Farhan, Effort: Medium, P1)
- [ ] Document vault boto3/R2 upload client (Requester: Farhan, Effort: Medium, P2)

---

## V2 Queue (Major Features)
- [ ] ENH-32 Package versioning UI / inventory-backed package items (Requester: Audit P32, Effort: High, P2)
- [ ] Real supplier httpx adapter (TBO/TripJack) + encrypted creds (Requester: Sahil, Effort: High, P1)
- [ ] Agent-facing analytics (ENH-31) (Requester: Agents, Effort: Medium, P3)
- [ ] Optional extract `apps/ai` service (if isolation needed) (Requester: Spec, Effort: High, P4)

---

## V3 Queue (Platform Expansion)
- [ ] ENH-33 Auto-settle commissions (Dangerous without commercial lock — Park until Phase 0 signed)
- [ ] ENH-34 WhatsApp Cloud API (wa.me remains V1/V2 by design)
- [ ] ENH-35 PWA / native mobile
- [ ] Full custom-domain DNS verify in production (Vercel domain link)
- [ ] ENH-36 Hotel full lifecycle beyond mock search

---

## Parked
- [ ] ENH-05 Compensate cancel on multi-item partial book (until multi-item book is real)
- [ ] Redis-backed rate limit / CB (until multi-instance)
- [ ] Search cache (explicitly deferred — see Phase 39 checklist)
- [ ] ENH-33 Auto-settle (await commercial lock)
