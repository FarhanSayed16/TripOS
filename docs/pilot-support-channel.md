# Pilot support channel

## Purpose

Single place for pilot agencies to ask for help during Phase 29 without DMing randomly.

## Recommended setup

1. Create a WhatsApp **group**: `TripOS Pilot Support`
2. Admins: Farhan (+ Nilesh optional)
3. Invite only approved pilot agents (one primary contact per agency)
4. Pin a message with links:
   - App URL
   - Quickstart: `docs/agent-quickstart.md` (or Notion/PDF export)
   - “If booking failed after pay: send quote id + screenshot”

## Response norms

| Severity | Target reply |
|---|---|
| Pay captured / no PNR | Same business day (Farhan) |
| Login / approval | Same day |
| Feature request | Log friction; no promise of ship date |

## Escalation

1. Agent posts in group with agency + quote id  
2. Farhan checks Admin → Failures + quote audit  
3. Refunds: Razorpay Dashboard per [`ops/RAZORPAY_REFUND_SOP.md`](./ops/RAZORPAY_REFUND_SOP.md)  
4. Commercial disputes: Nilesh  

## Optional

- Separate internal group: `TripOS Ops` (Farhan + Nilesh only) for dead-letters and commercial  
- Loom / screen recording of the demo script (record once; reuse for all demos)  
