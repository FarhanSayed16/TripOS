"use client";

import {
  useGetAdminDeadLettersQuery,
  useGetAdminBookingsQuery,
  useGetAdminRefundsQuery,
  useUpdateAdminRefundStatusMutation,
} from "@/lib/api/adminApi";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, ServerCrash } from "lucide-react";
import { formatFailureReason } from "@/lib/failureLabels";
import { useState } from "react";

/**
 * Admin failures queue (FIX-P24-02 + FC Phase 2 refunds):
 * dead-letter jobs + failed bookings + refund status queue.
 * Gateway refund still issued in Razorpay; status tracked here.
 */
export default function AdminFailuresPage() {
  const { data: deadLetters, isLoading: loadingJobs } = useGetAdminDeadLettersQuery();
  const { data: bookings, isLoading: loadingBookings } = useGetAdminBookingsQuery();
  const { data: refundsData, isLoading: loadingRefunds } = useGetAdminRefundsQuery({
    limit: 50,
  });
  const [updateRefund, { isLoading: updatingRefund }] = useUpdateAdminRefundStatusMutation();
  const [tab, setTab] = useState<"jobs" | "bookings" | "refunds">("jobs");

  const failedBookings = bookings?.filter((b) => b.status === "failed") || [];
  const refunds = refundsData?.items || [];

  if (loadingJobs || loadingBookings || loadingRefunds) {
    return <div className="p-8 text-gray-500">Loading failures…</div>;
  }

  const markRefund = async (id: string, status: string) => {
    const gateway =
      status === "succeeded"
        ? prompt("Razorpay refund id (optional)") || undefined
        : undefined;
    try {
      await updateRefund({
        id,
        status,
        gateway_refund_id: gateway,
        notes: status === "succeeded" ? "Marked after Razorpay refund" : undefined,
      }).unwrap();
    } catch {
      alert("Failed to update refund status");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Failures</h1>
        <p className="text-gray-500">
          Dead-letter jobs, failed bookings, and refund queue. Issue money movement in
          Razorpay, then mark status here.
        </p>
      </div>

      <div className="flex space-x-2 border-b border-line flex-wrap">
        {(
          [
            ["jobs", "Dead-letter jobs", deadLetters?.length || 0, "amber"],
            ["bookings", "Failed bookings", failedBookings.length, "red"],
            ["refunds", "Refunds", refunds.length, "purple"],
          ] as const
        ).map(([key, label, count, color]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              tab === key
                ? color === "red"
                  ? "border-red-600 text-red-600"
                  : color === "purple"
                    ? "border-purple-600 text-purple-700"
                    : "border-focus text-focus"
                : "border-transparent text-gray-500 hover:text-ink"
            }`}
          >
            {label}
            {count > 0 && (
              <span className="ml-2 bg-gray-100 text-gray-700 py-0.5 px-2 rounded-full text-xs">
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {tab === "jobs" && (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-500 uppercase bg-surface">
                  <tr>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Payload</th>
                    <th className="px-4 py-3">Attempts</th>
                    <th className="px-4 py-3">Error</th>
                    <th className="px-4 py-3">Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {(deadLetters || []).map((job) => (
                    <tr
                      key={job.id}
                      className="border-b border-line last:border-0 hover:bg-gray-50/50 align-top"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 font-medium text-ink">
                          <ServerCrash className="w-4 h-4 text-amber-600" />
                          {job.type}
                        </div>
                        <div className="text-xs font-mono text-gray-400 mt-1">
                          {job.id.slice(0, 8)}…
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs max-w-[220px] truncate">
                        {JSON.stringify(job.payload)}
                      </td>
                      <td className="px-4 py-3">{job.attempts}</td>
                      <td className="px-4 py-3 text-xs text-red-600 max-w-[240px]">
                        {job.error_details || "—"}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">
                        {job.updated_at || "—"}
                      </td>
                    </tr>
                  ))}
                  {(deadLetters || []).length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                        No dead-letter jobs.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {tab === "bookings" && (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-500 uppercase bg-surface">
                  <tr>
                    <th className="px-4 py-3">Booking</th>
                    <th className="px-4 py-3">Org</th>
                    <th className="px-4 py-3">Reason</th>
                    <th className="px-4 py-3">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {failedBookings.map((b) => (
                    <tr key={b.id} className="border-b border-line last:border-0">
                      <td className="px-4 py-3 font-mono text-xs">{b.id.slice(0, 8)}…</td>
                      <td className="px-4 py-3">{b.organization_name}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-red-500" />
                          {formatFailureReason(b.failure_reason)}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">{b.created_at}</td>
                    </tr>
                  ))}
                  {failedBookings.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                        No failed bookings.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {tab === "refunds" && (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-500 uppercase bg-surface">
                  <tr>
                    <th className="px-4 py-3">Refund</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Reason</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {refunds.map((r) => (
                    <tr key={r.id} className="border-b border-line last:border-0 align-top">
                      <td className="px-4 py-3 font-mono text-xs">
                        {r.id.slice(0, 8)}…
                        {r.quote_id && (
                          <div className="text-gray-400 mt-1">quote {String(r.quote_id).slice(0, 8)}…</div>
                        )}
                      </td>
                      <td className="px-4 py-3 font-medium">
                        ₹{(r.amount / 100).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="capitalize">
                          {r.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600">
                        {r.reason || "—"}
                        {r.gateway_refund_id && (
                          <div className="font-mono mt-1">{r.gateway_refund_id}</div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          {r.status === "requested" && (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={updatingRefund}
                              onClick={() => markRefund(r.id, "processing")}
                            >
                              Processing
                            </Button>
                          )}
                          {(r.status === "requested" || r.status === "processing") && (
                            <>
                              <Button
                                size="sm"
                                disabled={updatingRefund}
                                onClick={() => markRefund(r.id, "succeeded")}
                              >
                                Succeeded
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                disabled={updatingRefund}
                                onClick={() => markRefund(r.id, "failed")}
                              >
                                Failed
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                  {refunds.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                        No refunds yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
