"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Globe, Trash2, Check, Copy } from "lucide-react";
import { apiSlice } from "@/lib/apiSlice";

const brandingApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getDomains: builder.query<any[], void>({
      query: () => "/organizations/domains",
      providesTags: ["Domains"],
    }),
    addDomain: builder.mutation<any, { domain: string }>({
      query: (body) => ({
        url: "/organizations/domains",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Domains"],
    }),
    deleteDomain: builder.mutation<void, string>({
      query: (id) => ({
        url: `/organizations/domains/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Domains"],
    }),
    updateOrg: builder.mutation<any, { primary_color: string; logo_url: string }>({
      query: (body) => ({
        url: "/organizations/me",
        method: "PATCH",
        body,
      }),
    }),
  }),
});

export const { useGetDomainsQuery, useAddDomainMutation, useDeleteDomainMutation, useUpdateOrgMutation } = brandingApi;

export default function BrandingAdminPage() {
  const { data: domains, isLoading } = useGetDomainsQuery();
  const [addDomain, { isLoading: isAdding }] = useAddDomainMutation();
  const [deleteDomain] = useDeleteDomainMutation();
  const [updateOrg] = useUpdateOrgMutation();

  const [newDomain, setNewDomain] = useState("");
  const [primaryColor, setPrimaryColor] = useState("#0D9488");
  const [logoUrl, setLogoUrl] = useState("");
  const [copied, setCopied] = useState(false);

  const handleAddDomain = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDomain.trim()) return;
    try {
      await addDomain({ domain: newDomain }).unwrap();
      setNewDomain("");
    } catch (err: any) {
      alert("Failed to add domain: " + (err?.data?.detail || "Unknown error"));
    }
  };

  const handleDeleteDomain = async (id: string) => {
    if (confirm("Remove this domain?")) {
      await deleteDomain(id);
    }
  };

  const handleSaveBranding = async () => {
    try {
      await updateOrg({ primary_color: primaryColor, logo_url: logoUrl }).unwrap();
      alert("Branding saved!");
    } catch (e) {
      alert("Failed to save branding.");
    }
  };

  const handleCopyCNAME = () => {
    navigator.clipboard.writeText("cname.tripos.com");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading) return <div className="p-8 text-muted-foreground">Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-ink flex items-center gap-2">
          <Globe className="w-8 h-8 text-brand_primary" />
          White-Label & Branding
        </h1>
        <p className="text-muted-foreground mt-2">Manage your agency's public presentation and custom domains.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Brand Appearance</CardTitle>
            <CardDescription>Customize how your quotes look to your customers.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-ink/80 mb-1">Primary Color (Hex)</label>
              <div className="flex gap-3">
                <input
                  type="color"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="h-10 w-10 p-1 border border-line rounded"
                />
                <input
                  type="text"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="flex-1 px-3 py-2 border border-line rounded-md text-ink"
                  placeholder="#0D9488"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-ink/80 mb-1">Logo URL</label>
              <input
                type="text"
                value={logoUrl}
                onChange={(e) => setLogoUrl(e.target.value)}
                className="w-full px-3 py-2 border border-line rounded-md text-ink"
                placeholder="https://example.com/logo.png"
              />
            </div>
            <Button onClick={handleSaveBranding} className="w-full bg-ink text-white">Save Branding</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Custom Domains</CardTitle>
            <CardDescription>Host quotes on your own domain.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <form onSubmit={handleAddDomain} className="flex gap-2">
              <input
                type="text"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                placeholder="quotes.youragency.com"
                className="flex-1 px-3 py-2 border border-line rounded-md text-ink"
              />
              <Button type="submit" disabled={isAdding || !newDomain} className="bg-brand_primary text-white">
                Add
              </Button>
            </form>

            <div className="space-y-3">
              {domains?.map(d => (
                <div key={d.id} className="p-3 border border-line rounded-md bg-sand/30 flex justify-between items-center">
                  <div>
                    <p className="font-medium text-ink">{d.domain}</p>
                    <Badge variant={d.is_verified ? "default" : "secondary"} className="mt-1">
                      {d.is_verified ? "Verified" : "Pending Verification"}
                    </Badge>
                  </div>
                  <button onClick={() => handleDeleteDomain(d.id)} className="text-muted-foreground/60 hover:text-red-500">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
              {domains?.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">No custom domains added.</p>
              )}
            </div>

            <div className="bg-blue-50 p-4 rounded-md border border-blue-100 text-sm text-blue-800">
              <p className="font-semibold mb-1">DNS Setup Instructions</p>
              <p>To verify your domain, create a CNAME record pointing to:</p>
              <div className="mt-2 flex items-center gap-2">
                <code className="bg-paper px-2 py-1 rounded border border-blue-200 font-mono flex-1">cname.tripos.com</code>
                <Button variant="outline" size="sm" onClick={handleCopyCNAME} className="h-8 shrink-0">
                  {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
