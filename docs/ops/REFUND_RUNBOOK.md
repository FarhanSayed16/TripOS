# Refund Runbook

## Overview
This runbook describes the procedure for manually processing a refund when a booking fails after payment capture.

## Prerequisites
- Access to the TripOS Admin Dashboard.
- Access to the Razorpay Dashboard (or other payment gateway).

## Procedure
1. **Identify Failed Bookings**
   - Check the `dead_letter_queue` in the Admin Dashboard for `booking_confirm` jobs that have exceeded retry limits.
   - Or, look at the Bookings tab for bookings with status `failed`.

2. **Determine Refund Reason**
   - Check the `failure_reason` on the booking (e.g., `supplier_timeout`, `fare_changed`, `sold_out`).
   - Confirm that payment was indeed captured (Payment status should be `captured`).

3. **Issue Refund via Gateway**
   - Log into the Razorpay Dashboard.
   - Locate the transaction using the `gateway_payment_id` from the TripOS Payment record.
   - Click "Issue Refund" and select the full amount.

4. **Update TripOS Records**
   - No automatic webhook handles manual refunds yet.
   - Manually update the payment record to `refunded` in the database.
   - (Optional) Notify the agent that the refund has been processed.
