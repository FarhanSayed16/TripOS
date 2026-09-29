# FC Phase 0 — Flight Commerce lock (2026-09-28)

**Status:** Engineering templates **CLOSED** · Commercial fills **PENDING**  
**Plan:** `docs/architecture/flight-commerce-implementation-plan.md`

---

## Decisions locked by engineering

| Decision | Value | Owner to override |
|---|---|---|
| Primary supplier for adapter work | **TBO** until Nilesh picks otherwise | Nilesh |
| Simulated TBO still available | Yes — when `TBO_LIVE_ENABLED=false` or creds missing | — |
| Live mode | `TBO_LIVE_ENABLED=true` + credentials required | Sahil |
| Charge currency V1 | **INR** | Nilesh |
| Display FX | FC Phase 4 | — |
| Locales V1 | **en**, **hi** | — |
| B2C product | Separate company; TripOS Partner API = FC Phase 8 | All |
| L2B provisional | warn 80 / critical 120 until Sahil contract truth | Sahil |
| NDC adapter | **OFF** (`FC_NDC_ENABLED=false`) until matrix says yes | Sahil/Nilesh |
| LCC distinct feed | **OFF** (`FC_LCC_ENABLED=false`) until matrix says yes | Sahil/Nilesh |
| Reissue automation | Mock on (`FC_REISSUE_ENABLED=true`); live needs matrix yes | — |

## Templates created

| Doc | Purpose |
|---|---|
| [`FC_CAPABILITY_MATRIX.md`](./FC_CAPABILITY_MATRIX.md) | What supplier APIs support |
| [`../ops/FC_STAGING_SECRETS_CHECKLIST.md`](../ops/FC_STAGING_SECRETS_CHECKLIST.md) | Staging env names |
| Credential pack `01-supplier-sandbox.md` | Secrets intake (existing) |
| `SUPPLIER_L2B_CONTRACT.md` | L2B clauses (existing) |

## Sign-off

| Person | Date | Notes |
|---|---|---|
| Farhan | 2026-09-28 | FC Phase 0 engineering templates + Phase 1 live spine scaffold |
| Nilesh | | Primary supplier confirm |
| Sahil | | Matrix + sandbox keys + L2B truth |
