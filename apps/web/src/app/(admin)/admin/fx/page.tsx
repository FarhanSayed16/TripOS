"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  useGetFxRatesQuery,
  useUpsertFxRateMutation,
  useSeedFxRatesMutation,
} from "@/lib/api/adminApi";
import { Banknote, Globe, Zap, CheckCircle2 } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function AdminFxRatesPage() {
  const { data, isLoading, refetch } = useGetFxRatesQuery();
  const [upsert, { isLoading: saving }] = useUpsertFxRateMutation();
  const [seed, { isLoading: seeding }] = useSeedFxRatesMutation();
  const [quoteCurrency, setQuoteCurrency] = useState("USD");
  const [rate, setRate] = useState("0.012");
  const [msg, setMsg] = useState<string | null>(null);

  const onSave = async () => {
    try {
      await upsert({
        base_currency: data?.charge_currency || "INR",
        quote_currency: quoteCurrency,
        rate: parseFloat(rate),
        source: "manual",
      }).unwrap();
      setMsg("Rate saved successfully.");
      refetch();
      setTimeout(() => setMsg(null), 3000);
    } catch {
      setMsg("Failed to save rate.");
    }
  };

  const onSeed = async () => {
    try {
      const res = await seed().unwrap();
      setMsg(`Seeded ${res.seeded} pairs: ${res.pairs.join(", ")}`);
      refetch();
      setTimeout(() => setMsg(null), 5000);
    } catch {
      setMsg("Seed failed.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="h-8 w-8 rounded-full border-2 border-teal border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-10 max-w-5xl mx-auto">
      <div>
        <h1 className="page-title text-2xl tracking-tight">FX Rates</h1>
        <p className="page-subtitle mt-1">
          Manage display rates relative to the platform charge currency ({data?.charge_currency || "INR"}).
        </p>
      </div>

      {msg && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-lg flex items-center gap-2 shadow-sm animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          <span className="font-medium text-sm">{msg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upsert Form */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="bg-paper border-line shadow-sm">
            <CardHeader className="bg-surface/50 border-b border-line pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Banknote className="w-4 h-4 text-teal" /> Add / Update Rate
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-ink">Quote Currency</label>
                <select
                  className="w-full border border-line rounded-md h-10 px-3 bg-surface focus:ring-2 focus:ring-teal/20 text-sm"
                  value={quoteCurrency}
                  onChange={(e) => setQuoteCurrency(e.target.value)}
                >
                  {["USD", "AED", "EUR", "GBP"].map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-ink">
                  Rate <span className="text-muted-foreground font-normal">(units of Quote per 1 {data?.charge_currency || "INR"})</span>
                </label>
                <Input
                  className="font-mono bg-surface"
                  value={rate}
                  onChange={(e) => setRate(e.target.value)}
                />
              </div>

              <div className="pt-4 border-t border-line">
                <Button onClick={onSave} disabled={saving} className="w-full bg-teal hover:bg-teal-dark shadow-sm">
                  {saving ? "Saving…" : "Save Rate"}
                </Button>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-sand/30 border-line shadow-sm border-dashed">
             <CardContent className="p-4 text-center">
               <p className="text-xs text-muted-foreground mb-3">Auto-seed demo FX rates for testing environments.</p>
               <Button variant="outline" size="sm" onClick={onSeed} disabled={seeding} className="w-full">
                 <Zap className="w-3.5 h-3.5 mr-2" />
                 {seeding ? "Seeding…" : "Seed Demo Rates"}
               </Button>
             </CardContent>
          </Card>
        </div>

        {/* Rates Table */}
        <div className="lg:col-span-2">
          <Card className="bg-paper border-line shadow-sm">
            <CardHeader className="bg-surface/50 border-b border-line pb-4 flex flex-row justify-between items-center">
              <div>
                <CardTitle className="text-lg">Active Rates</CardTitle>
                <CardDescription>All configured cross-rates for the platform.</CardDescription>
              </div>
              {data?.fx_provider_enabled === false && (
                <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                  Manual Only Mode
                </Badge>
              )}
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-surface/50">
                  <TableRow>
                    <TableHead>Pair</TableHead>
                    <TableHead>Rate</TableHead>
                    <TableHead>Last Updated</TableHead>
                    <TableHead>Source</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(data?.items || []).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-20 bg-surface/30">
                        <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                          <div className="h-12 w-12 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-4">
                            <Globe className="w-5 h-5 text-muted-foreground" />
                          </div>
                          <h3 className="text-lg font-semibold text-ink mb-1">No rates configured</h3>
                          <p className="text-sm text-muted-foreground">Seed demo pairs or add one manually.</p>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    data?.items.map((r) => (
                      <TableRow key={r.id} className="hover:bg-surface">
                        <TableCell className="font-medium text-ink flex items-center gap-2">
                          <div className="flex items-center">
                            <span className="text-xs bg-sand px-1.5 py-0.5 rounded border border-line">{r.base_currency}</span>
                            <span className="mx-1 text-muted-foreground">→</span>
                            <span className="text-xs bg-teal/10 text-teal px-1.5 py-0.5 rounded border border-teal/20 font-bold">{r.quote_currency}</span>
                          </div>
                        </TableCell>
                        <TableCell className="font-mono font-bold text-ink text-base tracking-tight">
                          {r.rate}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {r.as_of ? new Date(r.as_of).toLocaleString() : "—"}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="uppercase text-[10px] text-muted-foreground">{r.source}</Badge>
                          {!r.is_active && <Badge variant="secondary" className="ml-1">Inactive</Badge>}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
