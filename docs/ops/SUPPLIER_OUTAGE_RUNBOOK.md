# Supplier Outage Runbook

## Overview
This runbook describes the procedure to follow when a supplier API (e.g., TBO, TripJack) is experiencing an outage.

## Detection
- Circuit breaker will automatically log `circuit_breaker_opened` if a supplier fails > 5 times consecutively.
- Admin dashboard (`/admin/suppliers`) will show the supplier status in red (Traffic Blocked).

## Procedure
1. **Verify Outage**
   - Check Sentry for spikes in `InventoryRevalidateError` or timeouts.
   - Ping the supplier's API status page or sandbox if available.

2. **Engage Kill Switch (Optional, but recommended)**
   - Even though the circuit breaker is automatic, engaging the manual override ensures the supplier isn't periodically hit during the "HALF_OPEN" recovery phase if the outage is known to be prolonged.
   - Go to Admin Dashboard -> Suppliers & Strategies.
   - Click **"Disable (Kill Switch)"** for the affected supplier.

3. **Notify Agents (If severe)**
   - If the outage affects the primary supplier, notify agents via email or a platform banner that some inventory may be unavailable.

4. **Monitor and Restore**
   - Periodically check the supplier's status page.
   - Once resolved, go to the Admin Dashboard and click **"Enable Supplier"** to remove the manual override.
   - Monitor Sentry to ensure traffic flows smoothly again.
