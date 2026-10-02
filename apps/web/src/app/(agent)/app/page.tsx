"use client";

import Link from "next/link";
import {
  AlertTriangle,
  Clock,
  CheckCircle2,
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
import { useGetCustomersQuery } from "@/lib/api/crmApi";
import { useGetWalletSummaryQuery } from "@/lib/api/walletApi";
import { useGetNotificationsQuery } from "@/lib/api/notificationsApi";

import { StaggerContainer } from "@/components/PageTransition";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "cn";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useMemo, useState } from "react";
import { format } from "date-fns";
import { useRouter } from "next/navigation";

export default function DashboardPage() {

  const router = useRouter();
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [searchTab, setSearchTab] = useState<"flights" | "hotels">("flights");
  const { data: failed = [], isLoading: loadingFailed } = useGetBookingsQuery({ status: "failed" });
  const { data: pendingBookings = [], isLoading: loadingPending } = useGetBookingsQuery({ status: "pending" });
  const { data: allBookings = [] } = useGetBookingsQuery(undefined);
  const { data: paidQuotes, isLoading: loadingPaid } = useGetQuotesQuery({ status: "paid" });
  const { data: customersData } = useGetCustomersQuery({ limit: 1 });
  const { data: walletSummary } = useGetWalletSummaryQuery();

  const awaitingConfirm = (paidQuotes?.items || []).filter(
    (q) => !q.booking || q.booking.status === "pending"
  );
  const pendingQuoteIds = new Set(awaitingConfirm.map((q) => q.id));
  const extraPending = pendingBookings.filter((b) => !pendingQuoteIds.has(b.quote_id));

  const loading = loadingFailed || loadingPending || loadingPaid;
  const attentionCount = failed.length + awaitingConfirm.length + extraPending.length;

  // Computed KPIs from live data
  const bookingCount = allBookings.length;
  const gmvPaise = useMemo(() => allBookings.reduce((s, b) => s + (b.quote?.total_price || 0), 0), [allBookings]);
  const gmvFormatted = useMemo(() => {
    const val = gmvPaise / 100;
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K`;
    return `₹${val.toLocaleString()}`;
  }, [gmvPaise]);
  const walletBalance = useMemo(() => {
    const val = (walletSummary?.available_paise || 0) / 100;
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K`;
    return `₹${val.toLocaleString()}`;
  }, [walletSummary]);
  const walletPending = useMemo(() => {
    const val = (walletSummary?.pending_paise || 0) / 100;
    return `₹${val.toLocaleString()}`;
  }, [walletSummary]);
  const customerCount = customersData?.total ?? customersData?.items?.length ?? 0;

  // Recent bookings — latest 5
  const recentBookings = useMemo(() => {
    return [...allBookings]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5);
  }, [allBookings]);



  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-8">
      {/* ── Main Content ── */}
      <div className="space-y-8 min-w-0">
        


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
              <span className="stat-value text-ink">{bookingCount}</span>
              <Calendar className="w-5 h-5 text-muted-foreground/40" />
            </div>
          </div>
          <div className="card-stat p-5">
            <div className="stat-label">GMV (all time)</div>
            <div className="mt-2 flex items-end justify-between">
              <span className="stat-value text-ink">{gmvFormatted}</span>
              <TrendingUp className="w-5 h-5 text-mint/40" />
            </div>
          </div>
          <div className="card-stat p-5">
            <div className="stat-label">Wallet Balance</div>
            <div className="mt-2 flex items-end justify-between">
              <span className="stat-value text-ink">{walletBalance}</span>
              <Wallet className="w-5 h-5 text-muted-foreground/40" />
            </div>
          </div>
          <div className="card-stat p-5">
            <div className="stat-label">Customers</div>
            <div className="mt-2 flex items-end justify-between">
              <span className="stat-value text-ink">{customerCount}</span>
              <Users className="w-5 h-5 text-muted-foreground/40" />
            </div>
          </div>
        </StaggerContainer>

        {/* 4. Embedded Search Widget */}
        <div className="card-elevated p-6">
          <div className="flex items-center gap-6 mb-6 border-b border-line pb-4">
            <button
              type="button"
              onClick={() => setSearchTab("flights")}
              className={`flex items-center gap-2 text-sm pb-4 -mb-[18px] ${
                searchTab === "flights"
                  ? "font-semibold text-teal border-b-2 border-teal"
                  : "font-medium text-muted-foreground hover:text-ink"
              }`}
            >
              <Plane className="w-4 h-4" /> Flights
            </button>
            <button
              type="button"
              onClick={() => setSearchTab("hotels")}
              className={`flex items-center gap-2 text-sm pb-4 -mb-[18px] ${
                searchTab === "hotels"
                  ? "font-semibold text-teal border-b-2 border-teal"
                  : "font-medium text-muted-foreground hover:text-ink"
              }`}
            >
              <Building className="w-4 h-4" /> Hotels
            </button>
          </div>
          
          <form
            className="grid grid-cols-1 sm:grid-cols-2 lg:flex gap-3 items-center"
            onSubmit={(e) => {
              e.preventDefault();
              const params = new URLSearchParams({ tab: searchTab });
              if (from) params.set("from", from.trim().toUpperCase());
              if (to) params.set("to", to.trim().toUpperCase());
              router.push(`/app/search?${params.toString()}`);
            }}
          >
            {searchTab === "flights" ? (
              <>
                <Input
                  placeholder="From (DEL)"
                  className="h-11 lg:w-40"
                  value={from}
                  onChange={(e) => setFrom(e.target.value)}
                  aria-label="Origin"
                />
                <button
                  type="button"
                  onClick={() => {
                    setFrom(to);
                    setTo(from);
                  }}
                  className="hidden lg:flex h-8 w-8 rounded-full bg-sand items-center justify-center hover:bg-line transition-colors flex-shrink-0"
                  aria-label="Swap origin and destination"
                >
                  <ArrowLeftRight className="w-4 h-4 text-ink/70" />
                </button>
                <Input
                  placeholder="To (BOM)"
                  className="h-11 lg:w-40"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  aria-label="Destination"
                />
              </>
            ) : (
              <Input
                placeholder="City or hotel"
                className="h-11 lg:flex-1"
                value={to}
                onChange={(e) => setTo(e.target.value)}
                aria-label="Hotel city"
              />
            )}
            <Button type="submit" size="xl" variant="gradient" className="h-11 px-8 rounded-lg w-full lg:w-auto">
              Search
            </Button>
          </form>
        </div>

        {/* 5. Recent Bookings Table */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Recent Bookings</h2>
            <Link href="/app/bookings" className="text-sm font-medium text-teal hover:underline">View all</Link>
          </div>
          {recentBookings.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              No bookings yet. Search inventory to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>PNR</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Date</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentBookings.map((booking) => (
                  <TableRow key={booking.id}>
                    <TableCell>{booking.quote?.customer_name || "Customer"}</TableCell>
                    <TableCell>
                      <Badge variant={booking.status === "confirmed" ? "confirmed" : booking.status === "failed" ? "failed" : "pending"}>
                        {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono">{booking.supplier_pnr || "—"}</TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {typeof booking.quote?.total_price === "number"
                        ? `₹${(booking.quote.total_price / 100).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                        : "—"}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground text-sm">
                      {format(new Date(booking.created_at), "MMM d")}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link 
                        href={`/app/quotes/${booking.quote_id}`}
                        className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "text-teal")}
                      >
                        Open quote
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
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
            <div className="text-3xl font-bold font-mono text-ink tracking-tight mb-4">{walletBalance}</div>
            <div className="flex gap-2">
              <Link
                href="/app/wallet"
                className={cn(
                  buttonVariants({ variant: "default" }),
                  "w-full bg-ink text-white hover:bg-ink/90 inline-flex items-center justify-center"
                )}
              >
                Add money
              </Link>
            </div>
            <div className="mt-4 pt-4 border-t border-line">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Pending settlements</span>
                <span className="font-medium font-mono text-amber-600">{walletPending}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <DashboardNotifications />

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

const severityDot: Record<string, string> = {
  error: "bg-coral",
  warning: "bg-amber-400",
  success: "bg-mint",
  info: "bg-teal",
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function DashboardNotifications() {
  const { data: notifications = [], isLoading } = useGetNotificationsQuery({ limit: 5 });

  return (
    <Card className="card-elevated border-none shadow-sm">
      <CardHeader className="pb-3 border-b border-line mb-3">
        <CardTitle className="text-sm font-medium text-ink flex items-center gap-2">
          <Bell className="w-4 h-4" /> Notifications
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : notifications.length === 0 ? (
          <div className="flex gap-3 items-start">
            <div className="h-2 w-2 rounded-full bg-mint mt-1.5 flex-shrink-0" />
            <div>
              <p className="text-sm text-ink leading-tight">All caught up — no pending actions.</p>
              <span className="text-xs text-muted-foreground">Now</span>
            </div>
          </div>
        ) : (
          notifications.map((n) => (
            <div key={n.id} className="flex gap-3 items-start">
              <div className={`h-2 w-2 rounded-full mt-1.5 flex-shrink-0 ${severityDot[n.severity] || severityDot.info}`} />
              <div>
                <p className={`text-sm leading-tight ${n.is_read ? "text-muted-foreground" : "text-ink font-medium"}`}>
                  {n.title}
                </p>
                <span className="text-xs text-muted-foreground">{timeAgo(n.created_at)}</span>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
