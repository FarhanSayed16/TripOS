"use client";

import { useState } from "react";
import {
  useGetPartnerAppsQuery,
  useCreatePartnerAppMutation,
  useRotatePartnerKeyMutation,
  useGetAdminOrganizationsQuery,
} from "@/lib/api/adminApi";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { KeyRound, RefreshCw, Plus, CheckCircle2 } from "lucide-react";

export default function AdminPartnersPage() {
  const { data: partners, isLoading, refetch } = useGetPartnerAppsQuery();
  const { data: orgs } = useGetAdminOrganizationsQuery();
  const [createApp, { isLoading: creating }] = useCreatePartnerAppMutation();
  const [rotateKey] = useRotatePartnerKeyMutation();

  const [orgId, setOrgId] = useState("");
  const [name, setName] = useState("Sandbox B2C");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const orgList = Array.isArray(orgs) ? orgs : (orgs as any)?.items || [];

  const handleCreate = async () => {
    setError(null);
    setCreatedKey(null);
    setCreatedSecret(null);
    if (!orgId || !name.trim()) {
      setError("Organization and name are required");
      return;
    }
    try {
      const res = await createApp({
        organization_id: orgId,
        name: name.trim(),
        env: "test",
        webhook_url: webhookUrl.trim() || undefined,
      }).unwrap();
      setCreatedKey(res.api_key || null);
      setCreatedSecret(res.webhook_secret || null);
      refetch();
    } catch (e: any) {
      setError(e?.data?.detail || e?.message || "Create failed");
    }
  };

  return (
    <div className="space-y-8 pb-10 max-w-6xl mx-auto">
      <div>
        <h1 className="page-title text-2xl tracking-tight">Partner Apps</h1>
        <p className="page-subtitle mt-1">
          Manage API keys for external B2C brands and integrated partners.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Create Form */}
        <div className="lg:col-span-1">
          <Card className="bg-paper border-line shadow-sm sticky top-6">
            <CardHeader className="bg-surface/50 border-b border-line pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Plus className="w-4 h-4 text-teal" />
                Create Partner App
              </CardTitle>
              <CardDescription>Generate credentials for an agency.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-ink">Organization</label>
                <select
                  className="w-full border border-line rounded-md h-10 px-3 bg-surface focus:ring-2 focus:ring-teal/20 text-sm"
                  value={orgId}
                  onChange={(e) => setOrgId(e.target.value)}
                >
                  <option value="">Select agency…</option>
                  {orgList.map((o: any) => (
                    <option key={o.id} value={o.id}>
                      {o.brand_name || o.name || o.id}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-ink">App Name</label>
                <Input
                  className="bg-surface"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Mobile App"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-ink flex justify-between">
                  Webhook URL <span className="text-muted-foreground font-normal">(Optional)</span>
                </label>
                <Input
                  className="bg-surface"
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  placeholder="https://…"
                />
              </div>
              
              <div className="pt-4 border-t border-line">
                <Button onClick={handleCreate} disabled={creating} className="w-full bg-teal hover:bg-teal-dark shadow-sm">
                  {creating ? "Creating…" : "Generate API Key"}
                </Button>
                {error && <p className="text-sm text-coral mt-3 text-center">{error}</p>}
              </div>

              {createdKey && (
                <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg animate-in fade-in slide-in-from-top-2">
                  <div className="flex items-center gap-2 mb-2">
                    <KeyRound className="w-4 h-4 text-amber-600" />
                    <p className="font-semibold text-amber-900 text-sm">Copy credentials now</p>
                  </div>
                  <p className="text-xs text-amber-700 mb-3">These keys will never be shown again.</p>
                  
                  <div className="space-y-2">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-amber-700/70">API Key</span>
                      <p className="font-mono text-xs bg-white border border-amber-200 p-2 rounded break-all select-all text-amber-900">{createdKey}</p>
                    </div>
                    {createdSecret && (
                      <div>
                        <span className="text-[10px] uppercase font-bold text-amber-700/70">Webhook Secret</span>
                        <p className="font-mono text-xs bg-white border border-amber-200 p-2 rounded break-all select-all text-amber-900">{createdSecret}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Partners List */}
        <div className="lg:col-span-2">
          <Card className="bg-paper border-line shadow-sm">
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-surface/50">
                  <TableRow>
                    <TableHead>App Name</TableHead>
                    <TableHead>Prefix</TableHead>
                    <TableHead>Environment</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">Loading...</TableCell>
                    </TableRow>
                  ) : (!partners || partners.length === 0) ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-20 bg-surface/30">
                        <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                          <div className="h-12 w-12 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-4">
                            <KeyRound className="w-5 h-5 text-muted-foreground" />
                          </div>
                          <h3 className="text-lg font-semibold text-ink mb-1">No partner apps</h3>
                          <p className="text-sm text-muted-foreground">Generate an API key to get started.</p>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    partners.map((p) => (
                      <TableRow key={p.id} className="hover:bg-surface">
                        <TableCell className="font-medium text-ink">{p.name}</TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground">{p.key_prefix}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="bg-sand/50 uppercase text-[10px] tracking-wide">{p.env}</Badge>
                        </TableCell>
                        <TableCell>
                          {p.is_active ? (
                            <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Active</Badge>
                          ) : (
                            <Badge variant="secondary">Inactive</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-amber-600 hover:text-amber-700 hover:bg-amber-50 border-amber-200 gap-1.5"
                            onClick={async () => {
                              if (confirm("Are you sure? This will invalidate the existing key immediately.")) {
                                const res = await rotateKey(p.id).unwrap();
                                setCreatedKey(res.api_key || null);
                                setCreatedSecret(res.webhook_secret || null);
                                refetch();
                              }
                            }}
                          >
                            <RefreshCw className="w-3 h-3" />
                            Rotate Key
                          </Button>
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
