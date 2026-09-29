"use client";

import { useGetAdminCommissionsQuery, useSettleCommissionsMutation } from "@/lib/api/adminApi";
import { getAccessToken } from "@/lib/apiSlice";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";
import { Download, Building, CheckCircle2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";

function formatInr(paise: number) {
  return `₹${(paise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

async function downloadStatement(orgId?: string) {
  const qs = orgId ? `?org_id=${orgId}` : "";
  const token = getAccessToken();
  const res = await fetch(`/api/v1/admin/commissions/statement.csv${qs}`, {
    credentials: "include",
    headers: token ? { authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    throw new Error("Failed to download statement");
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `commission-statement-${orgId || "all"}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function AdminCommissionsPage() {
  const { data, isLoading, refetch } = useGetAdminCommissionsQuery();
  const [settle, { isLoading: settling }] = useSettleCommissionsMutation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="h-8 w-8 rounded-full border-2 border-teal border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-10 max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="page-title text-2xl tracking-tight">Commissions</h1>
          <p className="page-subtitle mt-1">
            Settle available balances and export statement CSVs for agencies.
          </p>
        </div>
        <Button variant="outline" onClick={() => downloadStatement().catch(console.error)} className="bg-paper shadow-sm gap-2">
          <Download className="w-4 h-4" /> Export All CSV
        </Button>
      </div>

      <Card className="bg-paper border-line shadow-sm">
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-surface/50">
              <TableRow>
                <TableHead>Organization</TableHead>
                <TableHead className="text-right">Pending</TableHead>
                <TableHead className="text-right">Available</TableHead>
                <TableHead className="text-right">Settled</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(!data || data.length === 0) ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-20 bg-surface/30">
                    <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                      <div className="h-12 w-12 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-4">
                        <Building className="w-5 h-5 text-muted-foreground" />
                      </div>
                      <h3 className="text-lg font-semibold text-ink mb-1">No commission data</h3>
                      <p className="text-sm text-muted-foreground">Agencies have not earned commissions yet.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                data.map((row) => (
                  <TableRow key={row.organization_id} className="hover:bg-surface">
                    <TableCell className="font-medium text-ink py-4">
                      {row.organization_name}
                    </TableCell>
                    <TableCell className="text-right py-4">
                      <span className="font-mono text-muted-foreground">{formatInr(row.pending_paise)}</span>
                    </TableCell>
                    <TableCell className="text-right py-4">
                      <span className="font-mono text-teal font-bold tracking-tight bg-teal/5 px-2 py-1 rounded">
                        {formatInr(row.available_paise)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right py-4">
                      <span className="font-mono text-emerald-600 font-medium">
                        {formatInr(row.settled_paise)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right py-4">
                      <div className="flex justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="shadow-sm gap-1 text-muted-foreground"
                          onClick={() => downloadStatement(row.organization_id).catch(console.error)}
                        >
                          <Download className="w-3 h-3" /> CSV
                        </Button>
                        <Button
                          size="sm"
                          className="bg-emerald-600 hover:bg-emerald-700 shadow-sm gap-1"
                          disabled={settling || row.available_paise <= 0}
                          onClick={async () => {
                            await settle(row.organization_id);
                            refetch();
                          }}
                        >
                          <CheckCircle2 className="w-3 h-3" /> Settle
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
