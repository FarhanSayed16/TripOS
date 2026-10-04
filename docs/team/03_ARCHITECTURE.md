# TripOS — Architecture Document

**Document type:** System architecture  
**Prepared / researched by:** Farhan Sayed  
**Date:** 2026-10-05  

---

## 1. Architectural style

TripOS is a **modular monolith** API plus a **Next.js** SPA/SSR frontend:

- One FastAPI app holds domain services and supplier adapters.  
- One Postgres database is the system of record.  
- Redis accelerates shopping and rate/L2B concerns.  
- A **worker process** drains a durable **outbox** for booking confirmation (not “fire-and-forget HTTP”).  

This keeps V1 operable for the team while leaving a clean seam to extract adapters or services later.

---

## 2. High-level context

**PlantUML:** [`diagrams/01_system_context.puml`](./diagrams/01_system_context.puml)

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Agent /     │────►│ TripOS Web   │────►│ TripOS API      │
│ Admin UI    │     │ (Next.js)    │     │ (FastAPI)       │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                 ┌─────────────────────────────────┼────────────────────┐
                 ▼                                 ▼                    ▼
           PostgreSQL                           Redis              Supplier
           (quotes,                           (cache /            adapters
            bookings,                          meters)            mock | TBO
            orgs, …)                                                │
                                                                    ▼
                                                              TBO sandbox/live
                                                              (when enabled)

Customer ──► Public /q/[token] ──► Pay (Razorpay/mock) ──► Webhook / offline
                                              │
                                              ▼
                                         Outbox worker ──► book()
```

---

## 3. Core domain flow (money path)

**PlantUML:** [`diagrams/02_money_path.puml`](./diagrams/02_money_path.puml)

```text
1. SEARCH     → adapters (+ optional Redis shopping cache) → NormalizedOffer[]
2. QUOTE      → OfferSnapshot + agent_markup + passengers → status draft/ready/sent
3. PAY LINK   → LIVE revalidate → create payment / link
4. CAPTURE    → webhook or mark-paid-offline → quote paid
5. CONFIRM    → worker: revalidate → adapter.book → Booking + PNR
6. SERVE      → documents / cancel / change (reissue honesty paths)
```

**Rule:** Browse may be cached (**indicative**). **Pay and book always revalidate live** (or simulated supplier) so fare honesty is preserved.

---

## 4. Adapter architecture

**PlantUML:** [`diagrams/03_inventory_adapters.puml`](./diagrams/03_inventory_adapters.puml)

Interface (`BaseAdapter`): `search`, `revalidate`, `book`, `cancel`, (+ status / map_error as applicable).

| Code | Purpose |
|---|---|
| `mock_supplier` | Deterministic pilot / CI inventory |
| `tbo` | Simulated PNRs **or** live HTTP (`TboLiveClient`) |

`SupplierStrategy`: `all` | `primary_only` | `failover`.  
Aggregation / dedupe prefers real supplier codes when merging mock + TBO.

**Single-supplier waiver (FC Phase 3):** pilot primary live feed = **TBO**; second live feed deferred until TripJack (or equivalent) is delivered commercially.

---

## 5. Bounded contexts (logical)

| Context | Covers |
|---|---|
| Identity & access | Users, JWT, org membership, platform admin |
| Organization | Branding, domains, white-label checklist, network/sub-agents |
| CRM | Customers, timeline |
| Inventory | Search, revalidate, fare rules, ancillaries/seats |
| Commerce | Quotes, markup ladder, pay links, refunds metadata |
| Fulfillment | Bookings, outbox jobs, cancel, change/reissue |
| Money ops | Wallet ledger, commissions (admin), FX display rates |
| Platform admin | L2B, partners, supplier health, audit export |
| Partner edge | API-key B2C/partner product surface |

---

## 6. Frontend architecture

- **Route groups:** `(agent)`, `(admin)`, `(auth)`, `(marketing)`, public `/q/[token]`  
- **State:** Redux Toolkit + RTK Query for API  
- **i18n:** EN / HI catalogs + locale bootstrap  
- **Design system:** CSS variables (Ink, Paper, Teal, Coral, Amber, Mint, Line, Focus)  

UI enhancement target: NewUIReference density while keeping TripOS brand (not generic blue SaaS).

---

## 7. Data & consistency

- Quotes snapshot offers so later search cache expiry does not mutate sold economics silently.  
- Booking confirm is **asynchronous** after payment (worker). UI shows attention states for failed / pending.  
- Soft-fail cancel: TripOS can mark cancelled even if supplier cancel errors (ops visibility retained).  

---

## 8. Cross-cutting concerns

| Concern | Approach |
|---|---|
| L2B protection | Shopping cache, org brakes, survival soft-brakes, AI block on critical |
| Multi-currency display | FX envelope; charge currency remains truth |
| Localization | EN/HI for agent + public quote |
| Observability | Sentry + structured logs (structlog) |
| Partner isolation | Separate auth (`X-API-Key`), rate limit, optional IP allowlist |

---

## 9. What is intentionally out of architecture (V1)

- In-app B2C storefront  
- WhatsApp Cloud Business API as primary send  
- Multi-supplier NDC merge as a requirement for pilot  
- Travclan Volt (reviewed; not selected for current build)  

---

## 10. PlantUML diagrams

| Diagram | File |
|---|---|
| System context | [`diagrams/01_system_context.puml`](./diagrams/01_system_context.puml) |
| Money path (sequence) | [`diagrams/02_money_path.puml`](./diagrams/02_money_path.puml) |
| Inventory adapters + L2B | [`diagrams/03_inventory_adapters.puml`](./diagrams/03_inventory_adapters.puml) |
| Deployment topology | [`diagrams/04_deployment.puml`](./diagrams/04_deployment.puml) |

Index: [`diagrams/README.md`](./diagrams/README.md)

---

## 11. References

- `docs/architecture/live-inventory-phases-0-7-explained.md`  
- `docs/architecture/inventory-v1-mock.md`  
- `docs/architecture/flight-commerce-implementation-plan.md`  
- `docs/architecture/FC_SINGLE_SUPPLIER_WAIVER.md`  
- `docs/architecture/v1-api-layout.md`  

---

*Prepared and researched by Farhan Sayed.*
