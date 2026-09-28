# Pack 01 — Supplier sandbox (TBO / TripJack)

**Copy to:** `secrets/01-supplier-sandbox.md`  
**Filled by:** Sahil / Nilesh  
**Needed before:** FC Phase 1 live spine / Master Plan Phase 25  
**L2B / shopping clauses:** also fill [`../SUPPLIER_L2B_CONTRACT.md`](../SUPPLIER_L2B_CONTRACT.md)  
**Capability matrix (FC Phase 0):** also fill [`../FC_CAPABILITY_MATRIX.md`](../FC_CAPABILITY_MATRIX.md)

---

- Supplier name: `[ TBO / TripJack / Other ]`
- Environment: `[ sandbox / production ]` — use sandbox for V1 build
- Base URL:
- Auth method: `[ API key / user+password / token / other ]`
- Credentials: *(store only in secrets / password manager)*
- Rate limits:
- Products available: `[ flights / hotels / both ]`
- Sample search request notes / Postman collection link:
- Book / cancel / status quirks:
- Refund / void window notes:
- Support contact at supplier:
- Date credentials shared with Farhan:

---

## L2B / Look-to-Book (required before heavy live search)

Full questionnaire: `docs/phase-0/SUPPLIER_L2B_CONTRACT.md`. Paste contract answers here when copying to `secrets/`.

| Item | Answer |
|---|---|
| What counts as a “look”? | `[ search / revalidate / both / other — paste clause ]` |
| Max L2B allowed | `[ e.g. 100:1 ]` |
| Measurement window | `[ month / 30d / other ]` |
| Min bookings / month | `[ number / none ]` |
| Shopping / fare-cache API exists? | `[ Yes / No / Unknown ]` — product name: `________` |
| Must revalidate before ticket? | `[ Yes / No ]` |

**Engineering provisional (until Sahil overrides):** warn **80** · critical **120** · looks = live search + revalidate · no shopping API assumed → Redis shopping cache is our control.
