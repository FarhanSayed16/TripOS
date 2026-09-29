"use client";

import { useState } from "react";
import Link from "next/link";
import { format } from "date-fns";
import { CreditCard, Search, FileText, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";

import { useGetPaymentsQuery } from "@/lib/api/paymentsApi";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

export default function PaymentsPage() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const { data, isLoading, error } = useGetPaymentsQuery(
    statusFilter ? { status: statusFilter } : {}
  );

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="page-title text-2xl tracking-tight">Payments</h1>
          <p className="page-subtitle mt-1">Track all payment links and captured funds.</p>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="flex gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 hide-scrollbar bg-paper p-1 rounded-lg border border-line">
          {[
            { id: "", label: "All Payments" },
            { id: "pending", label: "Pending" },
            { id: "captured", label: "Captured" },
            { id: "failed", label: "Failed" },
            { id: "refunded", label: "Refunded" },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-5 py-2 rounded-md text-sm font-medium transition-all capitalize whitespace-nowrap flex items-center gap-2 ${
                statusFilter === tab.id 
                  ? "bg-surface shadow-sm text-ink font-semibold" 
                  : "text-muted-foreground hover:text-ink"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search Gateway Order ID..." 
            className="pl-9 bg-paper border-line focus-visible:ring-teal h-11"
          />
        </div>
      </div>

      <div className="table-container shadow-sm border border-line/80 bg-paper">
        <Table>
          <TableHeader className="bg-surface/50">
            <TableRow>
              <TableHead>Quote Link</TableHead>
              <TableHead>Gateway Order ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Generated At</TableHead>
              <TableHead className="text-right">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-40" /></TableCell>
                  <TableCell><Skeleton className="h-6 w-24 rounded-full" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                  <TableCell className="text-right"><Skeleton className="h-4 w-20 ml-auto" /></TableCell>
                </TableRow>
              ))
            ) : error ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-12 text-coral bg-coral/5">
                  Failed to load payments.
                </TableCell>
              </TableRow>
            ) : data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-24 bg-surface/30">
                  <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                    <div className="h-16 w-16 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-5">
                      <CreditCard className="w-6 h-6 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-ink mb-1">No payments found</h3>
                    <p className="text-sm text-muted-foreground">You haven't generated any payment links yet.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              data?.items.map((payment) => (
                <TableRow key={payment.id} className="table-row-interactive hover:bg-teal/[0.02]">
                  <TableCell className="font-medium py-4">
                    <Link href={`/app/quotes/${payment.quote_id}`} className="inline-flex items-center text-sm font-medium text-teal hover:text-teal-dark hover:underline">
                      View Quote <FileText className="w-3.5 h-3.5 ml-1.5" />
                    </Link>
                  </TableCell>
                  <TableCell className="py-4">
                    <span className="font-mono bg-sand/50 border border-line/50 px-2 py-0.5 rounded text-sm text-ink">{payment.gateway_order_id}</span>
                  </TableCell>
                  <TableCell className="py-4">
                    {payment.status === "captured" && (
                      <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 gap-1 pr-2">
                        <CheckCircle2 className="w-3 h-3" /> Captured
                      </Badge>
                    )}
                    {payment.status === "pending" && (
                      <Badge className="bg-amber-50 text-amber-700 border-amber-200 gap-1 pr-2">
                        <Clock className="w-3 h-3" /> Pending
                      </Badge>
                    )}
                    {payment.status === "failed" && (
                      <Badge className="bg-coral/10 text-coral-dark border-coral/30 gap-1 pr-2">
                        <AlertTriangle className="w-3 h-3" /> Failed
                      </Badge>
                    )}
                    {payment.status === "refunded" && (
                      <Badge className="bg-gray-100 text-gray-700 border-gray-200 gap-1 pr-2">
                        <XCircle className="w-3 h-3" /> Refunded
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="py-4 text-muted-foreground text-sm">
                    {format(new Date(payment.created_at), "MMM d, yyyy h:mm a")}
                  </TableCell>
                  <TableCell className="text-right py-4 font-bold font-mono text-ink tracking-tight">
                    ₹{(payment.amount / 100).toLocaleString(undefined, { maximumFractionDigits: 0 })}
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
