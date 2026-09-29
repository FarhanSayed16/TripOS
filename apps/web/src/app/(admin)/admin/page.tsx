"use client";

import { useGetAdminOrganizationsQuery, useGetAdminBookingsQuery, useGetAdminPaymentsQuery } from "@/lib/api/adminApi";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Building, Ticket, AlertTriangle, CreditCard, Activity, ArrowRight } from "lucide-react";
import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";
import { formatFailureReason } from "@/lib/failureLabels";

export default function AdminPage() {
  const { data: orgs, isLoading: isLoadingOrgs } = useGetAdminOrganizationsQuery();
  const { data: bookings, isLoading: isLoadingBookings } = useGetAdminBookingsQuery();
  const { data: payments, isLoading: isLoadingPayments } = useGetAdminPaymentsQuery();

  if (isLoadingOrgs || isLoadingBookings || isLoadingPayments) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="h-8 w-8 rounded-full border-2 border-teal border-t-transparent animate-spin" />
      </div>
    );
  }

  const activeOrgs = orgs?.filter((o) => o.status === "active")?.length || 0;
  const pendingOrgs = orgs?.filter((o) => o.status === "pending_approval")?.length || 0;
  
  const failedBookings = bookings?.filter((b) => b.status === "failed") || [];
  const openFailures = failedBookings.length;
  
  const pendingRefunds = payments?.filter((p) => p.status === "refunded")?.length || 0; // Mock logic
  const totalPayments = payments?.reduce((acc, p) => acc + (p.status === "captured" ? p.amount : 0), 0) || 0;

  // Mock Supplier Health Data
  const suppliers = [
    { name: "TBO (Flights)", status: "healthy", latency: "1.2s", errorRate: "0.5%" },
    { name: "TripJack (LCC)", status: "degraded", latency: "4.5s", errorRate: "8.2%" },
    { name: "Amadeus (GDS)", status: "healthy", latency: "0.8s", errorRate: "0.1%" },
  ];

  return (
    <div className="space-y-8 pb-10 max-w-7xl mx-auto">
      <div>
        <h1 className="page-title text-2xl tracking-tight">Admin Overview</h1>
        <p className="page-subtitle mt-1">Platform-wide statistics, health, and KPIs.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        
        {/* Failures KPI */}
        <Card className={`bg-paper border-line shadow-sm hover:shadow-md transition-shadow ${openFailures > 0 ? "border-coral/50 bg-coral/5" : ""}`}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className={`text-sm font-semibold uppercase tracking-wider text-muted-foreground ${openFailures > 0 ? "text-coral-dark" : ""}`}>Open Failures</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${openFailures > 0 ? "text-coral" : "text-emerald-500"}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold font-mono tracking-tight text-ink ${openFailures > 0 ? "text-coral-dark" : ""}`}>{openFailures}</div>
            {openFailures > 0 && (
              <Link href="/admin/bookings" className="text-xs text-coral font-medium underline underline-offset-2 mt-1.5 block">
                Requires manual intervention
              </Link>
            )}
            {openFailures === 0 && (
              <p className="text-xs text-emerald-600 mt-1.5 font-medium">All systems normal</p>
            )}
          </CardContent>
        </Card>

        {/* Refunds KPI */}
        <Card className="bg-paper border-line shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Pending Refunds</CardTitle>
            <CreditCard className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">{pendingRefunds}</div>
            <Link href="/admin/failures" className="text-xs text-amber-600 hover:text-amber-700 font-medium underline underline-offset-2 mt-1.5 block">
              Process refunds in Gateway
            </Link>
          </CardContent>
        </Card>

        {/* Supplier Health KPI */}
        <Card className="bg-paper border-line shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Supplier Health</CardTitle>
            <Activity className="h-4 w-4 text-teal" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">
              <span className="text-emerald-500">2</span> <span className="text-muted-foreground text-lg">/ 3</span>
            </div>
            <p className="text-xs text-amber-600 mt-1.5 font-medium flex items-center bg-amber-50 px-2 py-1 rounded inline-flex">
              TripJack experiencing latency
            </p>
          </CardContent>
        </Card>
        
        {/* Active Agents KPI */}
        <Card className="bg-paper border-line shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Active Agencies</CardTitle>
            <Building className="h-4 w-4 text-teal" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">{activeOrgs}</div>
            {pendingOrgs > 0 && (
              <Link href="/admin/agents" className="text-xs text-blue-600 hover:text-blue-700 font-medium underline underline-offset-2 mt-1.5 block">
                {pendingOrgs} pending approval
              </Link>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Failed Bookings Table */}
        <Card className="bg-paper border-line shadow-sm">
          <CardHeader className="bg-surface/50 border-b border-line pb-4 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg">Recent Failed Bookings</CardTitle>
              <CardDescription>Bookings requiring manual fulfillment or refund.</CardDescription>
            </div>
            <Link href="/admin/bookings" className="text-xs font-medium text-teal hover:underline flex items-center">
              View All <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-surface/50">
                <TableRow>
                  <TableHead>Agency</TableHead>
                  <TableHead>Quote / PNR</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {failedBookings.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center py-12 text-muted-foreground">
                      No failed bookings! 🎉
                    </TableCell>
                  </TableRow>
                ) : (
                  failedBookings.slice(0, 5).map(b => (
                    <TableRow key={b.id} className="hover:bg-coral/5">
                      <TableCell className="font-medium">{b.organization_name}</TableCell>
                      <TableCell>
                        <span className="font-mono text-sm">{b.quote_public_token?.toUpperCase() || b.quote_id.slice(0,8).toUpperCase()}</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-[10px] text-coral font-medium bg-coral/5 px-2 py-1 rounded">
                          {formatFailureReason(b.failure_reason)}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Supplier Health List */}
        <Card className="bg-paper border-line shadow-sm">
          <CardHeader className="bg-surface/50 border-b border-line pb-4">
            <CardTitle className="text-lg">Supplier Health</CardTitle>
            <CardDescription>Live integration status and latencies.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-surface/50">
                <TableRow>
                  <TableHead>Supplier</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Latency</TableHead>
                  <TableHead>Errors</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {suppliers.map(s => (
                  <TableRow key={s.name} className="hover:bg-surface">
                    <TableCell className="font-medium text-ink">{s.name}</TableCell>
                    <TableCell>
                      {s.status === 'healthy' ? (
                        <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Healthy</Badge>
                      ) : (
                        <Badge className="bg-amber-50 text-amber-700 border-amber-200">Degraded</Badge>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-sm text-muted-foreground">{s.latency}</TableCell>
                    <TableCell className="font-mono text-sm text-muted-foreground">{s.errorRate}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
