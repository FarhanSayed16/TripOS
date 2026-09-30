"use client";

import { useGetWalletSummaryQuery, useGetWalletLedgerQuery } from "@/lib/api/walletApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Download, Wallet, Clock, CheckCircle } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const API_BASE_URL = "/api/v1";

export default function WalletPage() {
  const { user } = useAuth();
  const { data: summary, isLoading: isLoadingSummary } = useGetWalletSummaryQuery();
  const { data: ledger, isLoading: isLoadingLedger } = useGetWalletLedgerQuery();

  if (isLoadingSummary || isLoadingLedger) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="h-8 w-8 rounded-full border-2 border-teal border-t-transparent animate-spin" />
      </div>
    );
  }

  const formatCurrency = (paise: number = 0) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(paise / 100);
  };

  const handleExport = () => {
    // In a real app, use the API token from context/storage
    const token = localStorage.getItem("token");
    window.open(`${API_BASE_URL}/wallet/ledger/export?token=${token}`, "_blank");
  };

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="page-title text-2xl tracking-tight">Wallet & Commissions</h1>
          <p className="page-subtitle mt-1">Track your earnings and pending payouts.</p>
        </div>
        <Button
          onClick={handleExport}
          variant="outline"
          className="gap-2 bg-paper shadow-sm"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-paper border-line shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Pending</CardTitle>
            <Clock className="h-4 w-4 text-amber" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">{formatCurrency(summary?.pending_paise)}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-paper border-line shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Available</CardTitle>
            <Wallet className="h-4 w-4 text-teal" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">{formatCurrency(summary?.available_paise)}</div>
          </CardContent>
        </Card>

        <Card className="bg-paper border-line shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Total Settled</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">{formatCurrency(summary?.total_settled_paise)}</div>
          </CardContent>
        </Card>
      </div>

      <div className="table-container shadow-sm border border-line/80 bg-paper">
        <Table>
          <TableHeader className="bg-surface/50">
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(!ledger?.items || ledger.items.length === 0) ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-24 bg-surface/30">
                  <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                    <div className="h-16 w-16 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-5">
                      <Wallet className="w-6 h-6 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-ink mb-1">No transactions</h3>
                    <p className="text-sm text-muted-foreground">You haven't earned any commissions yet.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              ledger.items.map((entry) => (
                <TableRow key={entry.id} className="table-row-interactive hover:bg-teal/[0.02]">
                  <TableCell className="py-4 text-muted-foreground">
                    {new Date(entry.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="py-4">
                    <div className="font-medium text-ink">
                      {entry.type === "commission_earned" ? "Commission Earned" : "Payout"}
                    </div>
                    {entry.description && (
                      <div className="text-xs text-muted-foreground mt-0.5">{entry.description}</div>
                    )}
                    {entry.booking_id && (
                      <div className="text-xs text-muted-foreground mt-1 font-mono">Ref: {entry.booking_id.substring(0, 8).toUpperCase()}</div>
                    )}
                  </TableCell>
                  <TableCell className="py-4">
                    {entry.status === "available" && <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Available</Badge>}
                    {entry.status === "settled" && <Badge className="bg-blue-50 text-blue-700 border-blue-200">Settled</Badge>}
                    {entry.status === "pending" && <Badge className="text-amber-700 border-amber-200 bg-amber-50">Pending</Badge>}
                    {entry.status === "failed" && <Badge className="bg-coral/10 text-coral border-coral/20">Failed</Badge>}
                  </TableCell>
                  <TableCell className="py-4 text-right">
                    <span className={`font-mono font-medium ${entry.amount_paise > 0 ? "text-emerald-600" : "text-ink"}`}>
                      {entry.amount_paise > 0 ? "+" : ""}{formatCurrency(entry.amount_paise)}
                    </span>
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
