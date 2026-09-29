"use client";

import { useGetAdminBookingsQuery } from "@/lib/api/adminApi";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { ExternalLink, AlertTriangle, Search, FileText, CheckCircle2, XCircle } from "lucide-react";
import { useState } from "react";
import { formatFailureReason } from "@/lib/failureLabels";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { format } from "date-fns";

export default function AdminBookingsPage() {
  const { data: bookings, isLoading } = useGetAdminBookingsQuery();
  const [activeTab, setActiveTab] = useState<"all" | "confirmed" | "failed" | "cancelled">("all");
  const [searchQuery, setSearchQuery] = useState("");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal"></div>
      </div>
    );
  }

  const failedBookings = bookings?.filter((b) => b.status === "failed") || [];
  
  const filteredBookings = bookings?.filter(b => {
    if (activeTab !== "all" && b.status !== activeTab) return false;
    
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      if (!b.organization_name?.toLowerCase().includes(q) && 
          !b.quote_public_token?.toLowerCase().includes(q) &&
          !b.quote_id.toLowerCase().includes(q) &&
          !b.supplier_pnr?.toLowerCase().includes(q)) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="space-y-8 pb-10">
      <div>
        <h1 className="page-title text-2xl tracking-tight">Global Bookings</h1>
        <p className="page-subtitle mt-1">Monitor all bookings and failures across the platform.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="flex gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 hide-scrollbar bg-paper p-1 rounded-lg border border-line">
          {[
            { id: "all", label: "All Bookings" },
            { id: "confirmed", label: "Confirmed" },
            { id: "failed", label: "Failures Queue", badge: failedBookings.length > 0 ? failedBookings.length : null },
            { id: "cancelled", label: "Cancelled" },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-5 py-2 rounded-md text-sm font-medium transition-all capitalize whitespace-nowrap flex items-center gap-2 ${
                activeTab === tab.id 
                  ? "bg-surface shadow-sm text-ink font-semibold" 
                  : "text-muted-foreground hover:text-ink"
              }`}
            >
              {tab.label}
              {tab.badge && (
                <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${activeTab === tab.id ? 'bg-coral text-white' : 'bg-coral/10 text-coral'}`}>
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search PNR, Agency or Quote ID..." 
            className="pl-9 bg-paper border-line focus-visible:ring-teal h-11"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="table-container shadow-sm border border-line/80 bg-paper">
        <Table>
          <TableHeader className="bg-surface/50">
            <TableRow>
              <TableHead>Agency</TableHead>
              <TableHead>Quote ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Supplier PNR</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!filteredBookings || filteredBookings.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-24 bg-surface/30">
                  <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                    <div className="h-16 w-16 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-5">
                      <FileText className="w-6 h-6 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-ink mb-1">No bookings found</h3>
                    <p className="text-sm text-muted-foreground">Adjust filters to see results.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredBookings.map((booking) => (
                <TableRow key={booking.id} className="table-row-interactive group hover:bg-teal/[0.02]">
                  <TableCell className="font-medium text-ink py-4">{booking.organization_name || "Unknown Agency"}</TableCell>
                  <TableCell className="py-4">
                    <span className="font-mono text-ink text-sm">
                      {booking.quote_public_token ? booking.quote_public_token.toUpperCase() : booking.quote_id.slice(0, 8).toUpperCase()}
                    </span>
                  </TableCell>
                  <TableCell className="py-4">
                    {booking.status === "confirmed" && (
                      <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 gap-1.5 pr-2">
                        <CheckCircle2 className="w-3 h-3" /> Confirmed
                      </Badge>
                    )}
                    {booking.status === "failed" && (
                      <div className="flex flex-col gap-1 items-start">
                        <Badge className="bg-coral/10 text-coral-dark border-coral/30 gap-1.5 pr-2">
                          <AlertTriangle className="w-3 h-3" /> Failed
                        </Badge>
                        {booking.failure_reason && (
                          <span className="text-[10px] text-coral font-medium flex items-center bg-coral/5 px-1.5 py-0.5 rounded">
                            {formatFailureReason(booking.failure_reason)}
                          </span>
                        )}
                      </div>
                    )}
                    {booking.status === "cancelled" && (
                      <Badge className="bg-gray-100 text-gray-700 border-gray-200 gap-1.5 pr-2">
                        <XCircle className="w-3 h-3" /> Cancelled
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="py-4">
                    {booking.supplier_pnr ? (
                      <span className="font-mono bg-sand/50 border border-line/50 px-2 py-0.5 rounded text-sm text-ink">{booking.supplier_pnr}</span>
                    ) : (
                      <span className="text-muted-foreground text-sm">—</span>
                    )}
                  </TableCell>
                  <TableCell className="py-4 text-muted-foreground text-sm">
                    {format(new Date(booking.created_at), "MMM d, yyyy h:mm a")}
                  </TableCell>
                  <TableCell className="py-4 text-right">
                    {booking.quote_public_token ? (
                      <a 
                        href={`/q/${booking.quote_public_token}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center text-sm font-medium text-teal hover:text-teal-dark hover:underline opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        View Quote <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
                      </a>
                    ) : (
                      <span className="text-muted-foreground text-xs opacity-0 group-hover:opacity-100 transition-opacity">No link</span>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
