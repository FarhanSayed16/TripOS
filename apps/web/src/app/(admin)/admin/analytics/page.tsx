"use client";

import { useGetAdminAnalyticsQuery, useGetAdminL2bOrgsQuery } from "@/lib/api/adminApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, TrendingUp, Users, DollarSign, Activity, BarChart3, LineChart as LineChartIcon } from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from "recharts";

// Mock timeseries data for the charts since the API currently only returns totals
const mockRevenueData = [
  { name: "Mon", revenue: 45000, bookings: 12 },
  { name: "Tue", revenue: 52000, bookings: 15 },
  { name: "Wed", revenue: 48000, bookings: 14 },
  { name: "Thu", revenue: 61000, bookings: 18 },
  { name: "Fri", revenue: 59000, bookings: 17 },
  { name: "Sat", revenue: 85000, bookings: 25 },
  { name: "Sun", revenue: 78000, bookings: 22 },
];

export default function AdminAnalyticsPage() {
  const { data: analytics, isLoading, error } = useGetAdminAnalyticsQuery(30);
  const { data: l2bOrgs } = useGetAdminL2bOrgsQuery({ days: 7, limit: 10 });

  if (isLoading) {
    return (
      <div className="flex h-[400px] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 rounded-full border-2 border-teal border-t-transparent animate-spin" />
          <span className="text-sm text-muted-foreground">Loading platform analytics...</span>
        </div>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="p-8 text-coral bg-coral/10 border border-coral/20 rounded-xl">
        Error loading analytics. Please try again.
      </div>
    );
  }

  // Format currency
  const formatCurrency = (paise: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(paise / 100);
  };

  // Color-code failure rate
  const failureRatePercent = (analytics.booking_failure_rate * 100).toFixed(1);
  let failureRateColor = "text-mint";
  if (analytics.booking_failure_rate > 0.25) {
    failureRateColor = "text-coral";
  } else if (analytics.booking_failure_rate > 0.1) {
    failureRateColor = "text-amber-500";
  }

  // Process L2B org data for chart
  const l2bChartData = (l2bOrgs?.orgs || []).slice(0, 7).map(org => ({
    name: org.organization_name?.slice(0, 8) || org.organization_id.slice(0, 8),
    looks: org.looks,
    bookings: org.confirmed_bookings,
  }));

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-end border-b border-line pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-ink">Platform Analytics</h1>
          <p className="text-sm text-muted-foreground mt-1">Live platform metrics & Look-to-Book monitoring.</p>
        </div>
        <Badge variant="outline" className="bg-surface border-line text-xs font-mono py-1 px-3">
          Last 30 Days
        </Badge>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-line shadow-sm bg-surface card-elevated">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Active Agents</CardTitle>
            <div className="h-8 w-8 rounded-lg bg-teal/10 flex items-center justify-center">
              <Users className="w-4 h-4 text-teal" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">{analytics.monthly_active_transacting_agents}</div>
            <p className="text-xs text-muted-foreground mt-2 font-medium">Across {analytics.active_orgs} active organizations</p>
          </CardContent>
        </Card>

        <Card className="border-line shadow-sm bg-surface card-elevated">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Total GMV</CardTitle>
            <div className="h-8 w-8 rounded-lg bg-mint/10 flex items-center justify-center">
              <DollarSign className="w-4 h-4 text-mint" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">{formatCurrency(analytics.total_gmv_paise)}</div>
            <p className="text-xs text-muted-foreground mt-2 font-medium">Avg {formatCurrency(analytics.avg_gmv_per_agent_paise)} per agent</p>
          </CardContent>
        </Card>

        <Card className="border-line shadow-sm bg-surface card-elevated">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Failure Rate</CardTitle>
            <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${
              analytics.booking_failure_rate > 0.25 ? 'bg-coral/10' : 'bg-surface border border-line'
            }`}>
              <Activity className={`w-4 h-4 ${
                analytics.booking_failure_rate > 0.25 ? 'text-coral' : 'text-muted-foreground'
              }`} />
            </div>
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold font-mono tracking-tight ${failureRateColor}`}>
              {failureRatePercent}%
            </div>
            <p className="text-xs text-muted-foreground mt-2 font-medium">
              {analytics.failed_bookings} failed / {analytics.total_bookings} total bookings
            </p>
          </CardContent>
        </Card>

        <Card className={`shadow-sm card-elevated border ${
          analytics.l2b_survival?.active 
            ? 'bg-coral/5 border-coral/30' 
            : analytics.l2b_7d?.status === "warn" 
              ? 'bg-amber-500/5 border-amber-500/30' 
              : 'bg-surface border-line'
        }`}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className={`text-sm font-semibold uppercase tracking-wider ${
              analytics.l2b_survival?.active ? 'text-coral' : 'text-muted-foreground'
            }`}>Platform L2B</CardTitle>
            <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${
              analytics.l2b_survival?.active ? 'bg-coral/10' : 'bg-surface border border-line'
            }`}>
              <TrendingUp className={`w-4 h-4 ${
                analytics.l2b_survival?.active ? 'text-coral' : 'text-muted-foreground'
              }`} />
            </div>
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold font-mono tracking-tight ${
              analytics.l2b_survival?.active 
                ? 'text-coral-dark' 
                : analytics.l2b_7d?.status === "warn" 
                  ? 'text-amber-700' 
                  : 'text-ink'
            }`}>
              {analytics.l2b_7d?.l2b_ratio ?? "—"}
            </div>
            <p className="text-xs text-muted-foreground mt-2 font-medium">
              {analytics.l2b_7d?.looks ?? 0} looks / {analytics.l2b_7d?.confirmed_bookings ?? 0} confirmed
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-4">
        <Card className="border-line shadow-sm bg-surface overflow-hidden">
          <CardHeader className="bg-paper/50 border-b border-line">
            <CardTitle className="text-sm flex items-center gap-2 text-ink uppercase tracking-wide font-semibold">
              <LineChartIcon className="w-4 h-4 text-teal" />
              Revenue Overview (7 Days)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={mockRevenueData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--teal))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--teal))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--line))" />
                  <XAxis 
                    dataKey="name" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fontSize: 12, fill: "hsl(var(--ink)/0.5)" }} 
                    dy={10}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fontSize: 12, fill: "hsl(var(--ink)/0.5)" }}
                    tickFormatter={(value) => `₹${value / 1000}k`}
                    dx={-10}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "hsl(var(--paper))", borderColor: "hsl(var(--line))", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}
                    itemStyle={{ color: "hsl(var(--ink))", fontSize: "14px", fontWeight: "600" }}
                    labelStyle={{ color: "hsl(var(--ink)/0.5)", fontSize: "12px", marginBottom: "4px" }}
                    formatter={(value) => [`₹${Number(value ?? 0).toLocaleString()}`, "Revenue"]}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="revenue" 
                    stroke="hsl(var(--teal))" 
                    strokeWidth={3}
                    fillOpacity={1} 
                    fill="url(#colorRevenue)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-line shadow-sm bg-surface overflow-hidden">
          <CardHeader className="bg-paper/50 border-b border-line">
            <CardTitle className="text-sm flex items-center gap-2 text-ink uppercase tracking-wide font-semibold">
              <BarChart3 className="w-4 h-4 text-coral" />
              L2B Distribution by Top Orgs
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="h-[300px] w-full">
              {l2bChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={l2bChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--line))" />
                    <XAxis 
                      dataKey="name" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fontSize: 12, fill: "hsl(var(--ink)/0.5)" }}
                      dy={10} 
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fontSize: 12, fill: "hsl(var(--ink)/0.5)" }}
                      dx={-10}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: "hsl(var(--paper))", borderColor: "hsl(var(--line))", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}
                      cursor={{ fill: "hsl(var(--line)/0.5)" }}
                    />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />
                    <Bar dataKey="looks" name="Searches (Looks)" fill="hsl(var(--ink)/0.2)" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="bookings" name="Bookings" fill="hsl(var(--teal))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center">
                  <p className="text-sm text-muted-foreground">No L2B data available for charting.</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* L2B Table Data */}
      <Card className="border-line shadow-sm bg-surface mt-6">
        <CardHeader className="bg-paper/50 border-b border-line">
          <CardTitle className="text-sm font-semibold uppercase tracking-wide text-ink">Org L2B Offenders (7d)</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {!l2bOrgs?.orgs?.length ? (
            <div className="p-8 text-center text-sm text-muted-foreground">No org usage recorded yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-sand/30">
                  <tr className="text-left text-muted-foreground border-b border-line">
                    <th className="py-3 px-6 font-medium text-xs uppercase tracking-wider">Organization</th>
                    <th className="py-3 px-6 font-medium text-xs uppercase tracking-wider">Looks</th>
                    <th className="py-3 px-6 font-medium text-xs uppercase tracking-wider">Confirmed</th>
                    <th className="py-3 px-6 font-medium text-xs uppercase tracking-wider">L2B Ratio</th>
                    <th className="py-3 px-6 font-medium text-xs uppercase tracking-wider text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {l2bOrgs.orgs.map((o) => (
                    <tr key={o.organization_id} className="hover:bg-sand/10 transition-colors">
                      <td className="py-3 px-6 font-medium text-ink">
                        {o.organization_name || o.organization_id.slice(0, 8)}
                      </td>
                      <td className="py-3 px-6 font-mono text-muted-foreground">{o.looks.toLocaleString()}</td>
                      <td className="py-3 px-6 font-mono text-muted-foreground">{o.confirmed_bookings.toLocaleString()}</td>
                      <td className="py-3 px-6 font-mono font-medium text-ink">{o.l2b_ratio}</td>
                      <td className="py-3 px-6 text-right">
                        <Badge
                          className={
                            o.status === "critical"
                              ? "bg-coral/10 text-coral border-coral/20 hover:bg-coral/20"
                              : o.status === "warn"
                                ? "bg-amber-500/10 text-amber-700 border-amber-500/20 hover:bg-amber-500/20"
                                : "bg-surface border-line text-muted-foreground"
                          }
                        >
                          {o.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
