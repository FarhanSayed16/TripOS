"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useGetBookingsQuery } from "@/lib/api/bookingsApi";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle, CheckCircle, Clock, XCircle } from "lucide-react";
import { format } from "date-fns";
import { formatFailureReason } from "@/lib/failureLabels";

export default function BookingsDashboard() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const { data: bookings, isLoading } = useGetBookingsQuery(statusFilter ? { status: statusFilter } : undefined);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="page-title">Bookings Ledger</h1>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-xl animate-shimmer" />
          ))}
        </div>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "confirmed":
        return <CheckCircle className="w-4 h-4 text-green-500 mr-2" />;
      case "failed":
        return <AlertCircle className="w-4 h-4 text-red-500 mr-2" />;
      case "pending":
        return <Clock className="w-4 h-4 text-yellow-500 mr-2" />;
      case "cancelled":
        return <XCircle className="w-4 h-4 text-gray-500 mr-2" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "confirmed":
        return "bg-green-100 text-green-800 border-green-200";
      case "failed":
        return "bg-red-100 text-red-800 border-red-200";
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "cancelled":
        return "bg-gray-100 text-gray-800 border-gray-200";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="page-title">Bookings Ledger</h1>
          <p className="page-subtitle mt-1">
            Track fulfillment outcomes and PNRs. Open a row to the quote page for full detail
            (cancel, audit, refunds).
          </p>
        </div>
        
        <div className="flex space-x-2 overflow-x-auto pb-2 md:pb-0 hide-scrollbar">
          {["All", "confirmed", "failed", "pending", "cancelled"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s === "All" ? undefined : s)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all capitalize whitespace-nowrap border ${
                (statusFilter === s || (s === "All" && !statusFilter))
                  ? "bg-teal-50 border-teal-200 text-teal-800 shadow-sm" 
                  : "bg-paper/50 border-line/50 text-muted-foreground hover:bg-paper hover:text-ink hover:border-line"
              }`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="table-container">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="table-header bg-surface/50 border-b border-line">
                <tr>
                  <th className="px-6 py-4 font-medium">Customer & Quote</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium">Supplier PNR</th>
                  <th className="px-6 py-4 font-medium">Date</th>
                  <th className="px-6 py-4 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line bg-white">
                {bookings?.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                      No bookings found.
                    </td>
                  </tr>
                ) : (
                  bookings?.map((booking) => (
                    <tr key={booking.id} className="table-row-interactive">
                      <td className="px-6 py-4">
                        <div className="font-medium text-ink">{booking.quote?.customer_name || "Unknown Customer"}</div>
                        <div className="text-xs text-gray-500 font-mono mt-1">Quote {booking.quote_id.split("-")[0]}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${getStatusBadge(booking.status)}`}>
                          {getStatusIcon(booking.status)}
                          {booking.status.toUpperCase()}
                        </span>
                        {booking.failure_reason && (
                          <div className="text-xs text-red-600 mt-1 max-w-[240px]">
                            {booking.failure_label || formatFailureReason(booking.failure_reason)}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {booking.supplier_pnr ? (
                          <span className="font-mono bg-teal/5 text-teal px-2.5 py-1 rounded-md text-xs border border-teal/15">
                            {booking.supplier_pnr}
                          </span>
                        ) : (
                          <span className="text-gray-400 italic">None</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-gray-500">
                        {format(new Date(booking.created_at), "MMM d, h:mm a")}
                      </td>
                      <td className="px-6 py-4 text-right space-x-3">
                        {booking.status === "confirmed" && (
                          <Link
                            href={`/app/bookings/${booking.id}/change`}
                            className="text-ink/70 hover:text-ink font-medium inline-flex items-center"
                          >
                            Change
                          </Link>
                        )}
                        <Link 
                          href={`/app/quotes/${booking.quote_id}`}
                          className="text-focus hover:text-focus/80 font-medium inline-flex items-center"
                        >
                          View quote →
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
      </div>
    </div>
  );
}
