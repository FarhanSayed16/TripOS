# Packages V1 honesty (FIX-P32-01)

**Status:** Snapshot-only prototype (Sprint Q).

- Packages store **estimated_cost_paise** items — not live supplier offers.
- `POST /packages/{id}/to-quote` creates a draft quote with **synthetic OfferSnapshots** (FK-safe).
- Default markup = 10% of estimated cost + `PLATFORM_FEE_PAISE`.
- **Not** a substitute for inventory search → revalidate → pay → book.
- Versioning deferred (ENH-32). Treat publish as CRM catalog, not inventory SKU.

**Exit proof:** unit/source tests in `tests/test_sprint_qrst.py`. Live pay→book from package = out of scope until inventory-backed items exist.
