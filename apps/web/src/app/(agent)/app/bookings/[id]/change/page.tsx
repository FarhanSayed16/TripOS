"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  useGetBookingQuery,
  useQuoteBookingChangeMutation,
  useConfirmBookingChangeMutation,
  BookingChange,
} from "@/lib/api/bookingsApi";
import { Button } from "@/components/ui/button";

export default function BookingChangePage() {
  const params = useParams();
  const bookingId = String(params.id || "");
  const { data: booking, isLoading } = useGetBookingQuery(bookingId, {
    skip: !bookingId,
  });
  const [quoteChange, { isLoading: quoting }] = useQuoteBookingChangeMutation();
  const [confirmChange, { isLoading: confirming }] = useConfirmBookingChangeMutation();

  const [changeType, setChangeType] = useState("date");
  const [newDate, setNewDate] = useState("");
  const [result, setResult] = useState<BookingChange | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleQuote = async () => {
    setError(null);
    try {
      const res = await quoteChange({
        bookingId,
        change_type: changeType,
        request_payload: changeType === "date" && newDate ? { new_departure_date: newDate } : {},
      }).unwrap();
      setResult(res);
    } catch (e: any) {
      setError(e?.data?.detail || e?.message || "Failed to quote change");
    }
  };

  const handleConfirm = async (paymentCollected: boolean) => {
    if (!result) return;
    setError(null);
    try {
      const res = await confirmChange({
        changeId: result.id,
        payment_collected: paymentCollected,
      }).unwrap();
      setResult(res);
    } catch (e: any) {
      setError(e?.data?.detail || e?.message || "Failed to confirm change");
    }
  };

  if (isLoading) {
    return <div className="p-8">Loading booking…</div>;
  }

  if (!booking) {
    return (
      <div className="p-8 space-y-4">
        <p>Booking not found.</p>
        <Link href="/app/bookings" className="text-focus">
          ← Back
        </Link>
      </div>
    );
  }

  const diffInr =
    result?.supplier_diff_paise != null
      ? (result.supplier_diff_paise / 100).toFixed(2)
      : null;

  return (
    <div className="max-w-xl mx-auto space-y-6 py-6">
      <div>
        <Link href="/app/bookings" className="text-sm text-muted-foreground hover:text-ink">
          ← Bookings
        </Link>
        <h1 className="page-title mt-2">Change booking</h1>
        <p className="page-subtitle mt-1">
          PNR {booking.supplier_pnr || "—"} · {booking.quote?.customer_name}
        </p>
        <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-md p-2 mt-2">
          Mock reissue scaffold — fee estimates only. Confirm does not change supplier
          PNR or tickets; use airline/desk SOP for live changes until contracted.
        </p>
      </div>

      <div className="rounded-xl border border-line bg-paper p-5 space-y-4">
        <label className="block text-sm font-medium">
          Change type
          <select
            className="mt-1 w-full border border-line rounded-md px-3 py-2 text-sm"
            value={changeType}
            onChange={(e) => setChangeType(e.target.value)}
          >
            <option value="date">Date change</option>
            <option value="route">Route change</option>
            <option value="name">Name correction</option>
            <option value="other">Other</option>
          </select>
        </label>

        {changeType === "date" && (
          <label className="block text-sm font-medium">
            New departure date
            <input
              type="date"
              className="mt-1 w-full border border-line rounded-md px-3 py-2 text-sm"
              value={newDate}
              onChange={(e) => setNewDate(e.target.value)}
            />
          </label>
        )}

        <Button onClick={handleQuote} disabled={quoting} className="w-full">
          {quoting ? "Quoting…" : "Get change quote"}
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 text-red-800 text-sm p-3">
          {error}
        </div>
      )}

      {result && (
        <div className="rounded-xl border border-line bg-paper p-5 space-y-3">
          <p className="text-sm font-medium">
            Status: <span className="uppercase">{result.status}</span>
          </p>
          {diffInr != null && (
            <p className="text-sm">
              Supplier difference: ₹{diffInr} {result.currency}
            </p>
          )}
          {result.sop_hint && (
            <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-md p-3">
              {result.sop_hint}
            </p>
          )}
          {result.status === "confirmed" && (
            <p className="text-sm text-green-700">
              Change request recorded as confirmed (mock). Update supplier ticket
              offline if this is a live booking.
            </p>
          )}
          {result.status === "quoted" && !result.manual_sop && (
            <div className="flex flex-col gap-2">
              <Button onClick={() => handleConfirm(true)} disabled={confirming}>
                Collect difference & confirm (mock)
              </Button>
              <Button
                variant="outline"
                onClick={() => handleConfirm(false)}
                disabled={confirming}
              >
                Mark awaiting payment
              </Button>
            </div>
          )}
          {result.status === "awaiting_payment" && (
            <Button onClick={() => handleConfirm(true)} disabled={confirming} className="w-full">
              Payment collected — confirm
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
