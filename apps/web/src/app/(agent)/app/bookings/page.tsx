"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { useGetBookingsQuery } from "@/lib/api/bookingsApi";
import { AlertCircle, CheckCircle, Clock, XCircle, CalendarDays, TrendingUp } from "lucide-react";
import { format } from "date-fns";
import { formatFailureReason } from "@/lib/failureLabels";
import { StaggerContainer } from "@/components/PageTransition";

export default function BookingsDashboard() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const { data: bookings, isLoading } = useGetBookingsQuery(statusFilter ? { status: statusFilter } : undefined);
  const { data: allBookings } = useGetBookingsQuery(undefined);

  // KPI calculations
  const kpis = useMemo(() => {
    if (!allBookings) return { total: 0, confirmed: 0, pending: 0, failed: 0 };
    return {
      total: allBookings.length,
      confirmed: allBookings.filter(b => b.status === "confirmed").length,
      pending: allBookings.filter(b => b.status === "pending").length,
      failed: allBookings.filter(b => b.status === "failed").length,
    };
  }, [allBookings]);

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
        return <CheckCircle className="w-4 h-4 text-mint mr-2" />;
      case "failed":
        return <AlertCircle className="w-4 h-4 text-coral mr-2" />;
      case "pending":
        return <Clock className="w-4 h-4 text-amber-500 mr-2" />;
      case "cancelled":
        return <XCircle className="w-4 h-4 text-muted-foreground mr-2" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "confirmed":
        return "bg-mint/10 text-mint border-mint/20";
      case "failed":
        return "bg-coral/10 text-coral border-coral/20";
      case "pending":
        return "bg-amber-500/10 text-amber-700 border-amber-500/20";
      case "cancelled":
        return "bg-surface text-muted-foreground border-line";
      default:
        return "bg-surface text-muted-foreground border-line";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
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
                  ? "bg-teal/10 border-teal/20 text-teal shadow-sm" 
                  : "bg-paper/50 border-line/50 text-muted-foreground hover:bg-paper hover:text-ink hover:border-line"
              }`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Strip (§8.2) */}
      <StaggerContainer className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card-stat p-5">
          <div className="stat-label">Total Bookings</div>
          <div className="mt-2 flex items-end justify-between">
            <span className="stat-value text-ink">{kpis.total}</span>
            <CalendarDays className="w-5 h-5 text-muted-foreground/40" />
          </div>
        </div>
        <div className="card-stat accent-green p-5">
          <div className="stat-label">Confirmed</div>
          <div className="mt-2 flex items-end justify-between">
            <span className="stat-value text-mint">{kpis.confirmed}</span>
            <CheckCircle className="w-5 h-5 text-mint/40" />
          </div>
        </div>
        <div className="card-stat accent-amber p-5">
          <div className="stat-label">Pending</div>
          <div className="mt-2 flex items-end justify-between">
            <span className="stat-value text-amber-500">{kpis.pending}</span>
            <Clock className="w-5 h-5 text-amber-500/40" />
          </div>
        </div>
        <div className="card-stat accent-coral p-5">
          <div className="stat-label">Failed</div>
          <div className="mt-2 flex items-end justify-between">
            <span className="stat-value text-coral">{kpis.failed}</span>
            <AlertCircle className="w-5 h-5 text-coral/40" />
          </div>
        </div>
      </StaggerContainer>

      <div className="table-container table-card-mobile">
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
              <tbody className="divide-y divide-line bg-paper">
                {bookings?.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-muted-foreground">
                      No bookings found.
                    </td>
                  </tr>
                ) : (
                  bookings?.map((booking) => (
                    <tr key={booking.id} className="table-row-interactive">
                      <td data-label="Customer" className="px-6 py-4">
                        <div className="font-medium text-ink">{booking.quote?.customer_name || "Unknown Customer"}</div>
                        <div className="text-xs text-muted-foreground font-mono mt-1">Quote {booking.quote_id.split("-")[0]}</div>
                      </td>
                      <td data-label="Status" className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${getStatusBadge(booking.status)}`}>
                          {getStatusIcon(booking.status)}
                          {booking.status.toUpperCase()}
                        </span>
                        {booking.failure_reason && (
                          <div className="text-xs text-coral mt-1 max-w-[240px]">
                            {booking.failure_label || formatFailureReason(booking.failure_reason)}
                          </div>
                        )}
                      </td>
                      <td data-label="PNR" className="px-6 py-4">
                        {booking.supplier_pnr ? (
                          <span className="font-mono bg-teal/5 text-teal px-2.5 py-1 rounded-md text-xs border border-teal/15">
                            {booking.supplier_pnr}
                          </span>
                        ) : (
                          <span className="text-muted-foreground/60 italic">None</span>
                        )}
                      </td>
                      <td data-label="Date" className="px-6 py-4 text-muted-foreground">
                        {format(new Date(booking.created_at), "MMM d, h:mm a")}
                      </td>
                      <td data-label="" className="px-6 py-4 text-right space-x-3">
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
