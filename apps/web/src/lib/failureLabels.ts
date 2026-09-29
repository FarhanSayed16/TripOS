/** Human-readable booking failure labels (FIX-P23-01). */
export const FAILURE_LABELS: Record<string, string> = {
  fare_changed: "Fare changed — paid amount no longer matches supplier price",
  sold_out: "Sold out — inventory no longer available",
  supplier_timeout: "Supplier timed out — may be retryable; needs support check",
  supplier_error: "Supplier error — needs manual support",
  missing_pax: "Missing passenger details — cannot complete booking",
  unknown: "Unknown failure — needs manual review",
};

export function formatFailureReason(reason?: string | null): string {
  if (!reason) return "";
  return FAILURE_LABELS[reason] || reason.replace(/_/g, " ");
}

export function needsManualSupportCopy(reason?: string | null): string {
  const label = formatFailureReason(reason) || "a supplier problem";
  return `Payment was received but booking needs manual support (${label}). Review the quote, contact the customer, and process a refund in Razorpay if you cannot rebook.`;
}
