"use client";

import Link from "next/link";
import {
  AlertTriangle,
  Clock,
  CheckCircle2,
  Search,
  ArrowRight,
  TrendingUp,
  Wallet,
  Calendar,
  Users,
  Plane,
  Building,
  ArrowLeftRight,
  Sparkles,
  Bell
} from "lucide-react";
import { useGetBookingsQuery } from "@/lib/api/bookingsApi";
import { useGetQuotesQuery } from "@/lib/api/quotesApi";
import { useAuth } from "@/contexts/AuthContext";
import { StaggerContainer } from "@/components/PageTransition";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: failed = [], isLoading: loadingFailed } = useGetBookingsQuery({ status: "failed" });
  const { data: pendingBookings = [], isLoading: loadingPending } = useGetBookingsQuery({ status: "pending" });
  const { data: paidQuotes, isLoading: loadingPaid } = useGetQuotesQuery({ status: "paid" });

  const awaitingConfirm = (paidQuotes?.items || []).filter(
    (q) => !q.booking || q.booking.status === "pending"
  );
  const pendingQuoteIds = new Set(awaitingConfirm.map((q) => q.id));
  const extraPending = pendingBookings.filter((b) => !pendingQuoteIds.has(b.quote_id));

  const loading = loadingFailed || loadingPending || loadingPaid;
  const attentionCount = failed.length + awaitingConfirm.length + extraPending.length;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const firstName = user?.email?.split("@")[0] || "there";
  const todayDate = new Date().toLocaleDateString("en-US", { weekday: 'long', month: 'long', day: 'numeric' });

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-8">
      {/* ── Main Content ── */}
      <div className="space-y-8 min-w-0">
        
        {/* 1. Greeting Block */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <h1 className="page-title">{greeting}, {firstName}</h1>
            <p className="page-subtitle mt-1">
              {todayDate} &middot; Here's your attention desk.
            </p>
          </div>
          <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-mint bg-mint/10 px-3 py-1.5 rounded-full border border-mint/20 whitespace-nowrap">
            <div className="h-2 w-2 rounded-full bg-mint animate-pulse" />
            All systems operational
          </div>
        </div>

        {/* 2. Attention Alerts */}
        {!loading && attentionCount > 0 ? (
          <StaggerContainer className="grid gap-4 sm:grid-cols-2">
            {failed.length > 0 && (
              <div className="rounded-xl bg-coral/10 border border-coral/20 p-5 shadow-sm">
                <div className="flex items-center gap-3 mb-2">
                  <div className="h-8 w-8 rounded-full bg-coral/20 flex items-center justify-center">
                    <AlertTriangle className="h-4 w-4 text-coral" />
                  </div>
                  <div className="text-sm font-semibold text-red-900 tracking-wide">{failed.length} Failed Bookings</div>
                </div>
                <p className="text-sm text-red-800/80 mb-4">Requires manual support and refund processing.</p>
                <Link href="/app/bookings" className="text-sm font-medium text-coral hover:text-red-700 flex items-center gap-1 group">
                  Review failures <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </div>
            )}
            
            {(awaitingConfirm.length > 0 || extraPending.length > 0) && (
              <div className="rounded-xl bg-amber-50 border border-amber-200 p-5 shadow-sm">
                <div className="flex items-center gap-3 mb-2">
                  <div className="h-8 w-8 rounded-full bg-amber-100 flex items-center justify-center">
                    <Clock className="h-4 w-4 text-amber-600" />
                  </div>
                  <div className="text-sm font-semibold text-amber-900 tracking-wide">{awaitingConfirm.length + extraPending.length} Awaiting Confirm</div>
                </div>
                <p className="text-sm text-amber-800/80 mb-4">Paid quotes pending fulfillment and ticketing.</p>
                <Link href="/app/bookings" className="text-sm font-medium text-amber-700 hover:text-amber-800 flex items-center gap-1 group">
                  View pending <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </div>
            )}
          </StaggerContainer>
        ) : !loading && attentionCount === 0 ? (
          <div className="rounded-xl bg-surface border border-line p-6 flex items-center gap-4 shadow-sm">
            <div className="h-12 w-12 rounded-full bg-mint/10 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="w-6 h-6 text-mint" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-ink">You're all caught up!</h3>
              <p className="text-sm text-muted-foreground">No failed bookings or quotes awaiting confirmation.</p>
            </div>
          </div>
        ) : null}

        {/* 3. KPI Row */}
        <StaggerContainer className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card-stat p-5">
            <div className="stat-label">Bookings</div>
            <div className="mt-2 flex items-end justify-between">
              <span className="stat-value text-ink">124</span>
              <span className="text-xs font-medium text-mint flex items-center"><TrendingUp className="w-3 h-3 mr-1"/> +12%</span>
            </div>
          </div>
          <div className="card-stat p-5">
            <div className="stat-label">GMV (30d)</div>
            <div className="mt-2 flex items-end justify-between">
              <span className="stat-value text-ink">₹8.4L</span>
              <span className="text-xs font-medium text-mint flex items-center"><TrendingUp className="w-3 h-3 mr-1"/> +5%</span>
            </div>
          </div>
          <div className="card-stat p-5">
            <div className="stat-label">Wallet Balance</div>
            <div className="mt-2 flex items-end justify-between">
              <span className="stat-value text-ink">₹1.2L</span>
            </div>
          </div>
          <div className="card-stat p-5">
            <div className="stat-label">Customers</div>
            <div className="mt-2 flex items-end justify-between">
              <span className="stat-value text-ink">45</span>
              <span className="text-xs font-medium text-mint flex items-center"><TrendingUp className="w-3 h-3 mr-1"/> +2</span>
            </div>
          </div>
        </StaggerContainer>

        {/* 4. Embedded Search Widget */}
        <div className="card-elevated p-6">
          <div className="flex items-center gap-6 mb-6 border-b border-line pb-4">
            <button className="flex items-center gap-2 text-sm font-semibold text-teal border-b-2 border-teal pb-4 -mb-[18px]">
              <Plane className="w-4 h-4" /> Flights
            </button>
            <button className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-ink pb-4 -mb-[18px]">
              <Building className="w-4 h-4" /> Hotels
            </button>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:flex gap-3 items-center">
            <Input placeholder="From (DEL)" className="h-11 lg:w-40" />
            <button className="hidden lg:flex h-8 w-8 rounded-full bg-sand items-center justify-center hover:bg-line transition-colors flex-shrink-0">
              <ArrowLeftRight className="w-4 h-4 text-ink/70" />
            </button>
            <Input placeholder="To (BOM)" className="h-11 lg:w-40" />
            <div className="relative flex-1">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Dates" className="h-11 pl-9 w-full" defaultValue="Tomorrow" />
            </div>
            <div className="relative flex-1">
              <Users className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Pax" className="h-11 pl-9 w-full" defaultValue="1 Adult, Economy" />
            </div>
            <Input placeholder="Deal Code" className="h-11 font-mono text-sm lg:w-32" />
            <Button size="xl" variant="gradient" className="h-11 px-8 rounded-lg w-full lg:w-auto" asChild>
              <Link href="/app/search">Search</Link>
            </Button>
          </div>
        </div>

        {/* 5. Recent Bookings Table */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Recent Bookings</h2>
            <Link href="/app/bookings" className="text-sm font-medium text-teal hover:underline">View all</Link>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Route</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>PNR</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell>John Doe</TableCell>
                <TableCell>DEL &rarr; BOM</TableCell>
                <TableCell><Badge variant="confirmed">Confirmed</Badge></TableCell>
                <TableCell>X89B2M</TableCell>
                <TableCell className="text-right">₹12,450</TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" className="text-teal">Open quote</Button>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Acme Corp</TableCell>
                <TableCell>BLR &rarr; DXB</TableCell>
                <TableCell><Badge variant="pending">Pending</Badge></TableCell>
                <TableCell>—</TableCell>
                <TableCell className="text-right">₹45,800</TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" className="text-teal">Open quote</Button>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Jane Smith</TableCell>
                <TableCell>BOM &rarr; LHR</TableCell>
                <TableCell><Badge variant="live">Live</Badge></TableCell>
                <TableCell>Y7T89Q</TableCell>
                <TableCell className="text-right">₹89,200</TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" className="text-teal">Open quote</Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

      </div>

      {/* ── Right Rail ── */}
      <div className="space-y-6">
        
        {/* Wallet Summary */}
        <Card className="card-elevated border-none shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider flex items-center justify-between">
              Wallet <Wallet className="w-4 h-4 text-ink" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono text-ink tracking-tight mb-4">₹1,24,500</div>
            <div className="flex gap-2">
              <Button variant="default" className="w-full bg-ink text-white hover:bg-ink/90">Add money</Button>
            </div>
            <div className="mt-4 pt-4 border-t border-line">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Pending settlements</span>
                <span className="font-medium font-mono text-amber-600">₹45,800</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card className="card-elevated border-none shadow-sm">
          <CardHeader className="pb-3 border-b border-line mb-3">
            <CardTitle className="text-sm font-medium text-ink flex items-center gap-2">
              <Bell className="w-4 h-4" /> Notifications
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3 items-start">
              <div className="h-2 w-2 rounded-full bg-teal mt-1.5 flex-shrink-0" />
              <div>
                <p className="text-sm text-ink leading-tight">Your markup rules have been updated.</p>
                <span className="text-xs text-muted-foreground">2 hours ago</span>
              </div>
            </div>
            <div className="flex gap-3 items-start">
              <div className="h-2 w-2 rounded-full bg-coral mt-1.5 flex-shrink-0" />
              <div>
                <p className="text-sm text-ink leading-tight">Payment failed for Acme Corp booking.</p>
                <span className="text-xs text-muted-foreground">5 hours ago</span>
              </div>
            </div>
            <div className="flex gap-3 items-start">
              <div className="h-2 w-2 rounded-full bg-line mt-1.5 flex-shrink-0" />
              <div>
                <p className="text-sm text-ink leading-tight">System maintenance scheduled for Sunday.</p>
                <span className="text-xs text-muted-foreground">1 day ago</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Promo */}
        <div className="rounded-xl bg-gradient-to-br from-ink to-teal-dark p-6 text-white relative overflow-hidden shadow-md group cursor-pointer hover:shadow-lg transition-all">
          <div className="absolute -right-4 -top-4 w-24 h-24 bg-white/10 rounded-full blur-2xl group-hover:bg-white/20 transition-colors" />
          <Sparkles className="w-6 h-6 mb-3 text-teal-300" />
          <h3 className="font-medium text-lg mb-1 tracking-tight">AI Assistant</h3>
          <p className="text-sm text-white/80 mb-4">Draft quotes and search inventory with natural language.</p>
          <Link href="/app/ai" className="text-sm font-medium text-teal-200 hover:text-white flex items-center gap-1 transition-colors relative z-10">
            Try it now <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

      </div>
    </div>
  );
}
