"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Users, Plus, Building, User, Mail, ShieldCheck } from "lucide-react";
import { apiSlice } from "@/lib/apiSlice";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";

const networkApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getNetwork: builder.query<
      {
        sub_agents: any[];
        network_gmv_paise: number;
        master_override_bps: number;
      },
      void
    >({
      query: () => "/organizations/network",
      providesTags: ["Network"],
    }),
    addSubAgent: builder.mutation<any, any>({
      query: (body) => ({
        url: "/organizations/sub-agents",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Network"],
    }),
  }),
});

export const { useGetNetworkQuery, useAddSubAgentMutation } = networkApi;

export default function NetworkPage() {
  const { data: network, isLoading } = useGetNetworkQuery();
  const [addSubAgent, { isLoading: isAdding }] = useAddSubAgentMutation();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formData, setFormData] = useState({
    brand_name: "",
    admin_email: "",
    admin_first_name: "",
    admin_last_name: "",
  });

  const [createdResult, setCreatedResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await addSubAgent(formData).unwrap();
      setCreatedResult(res);
      setFormData({ brand_name: "", admin_email: "", admin_first_name: "", admin_last_name: "" });
    } catch (err: any) {
      alert("Failed to add sub-agent: " + (err?.data?.detail || "Unknown error"));
    }
  };

  const subAgents = network?.sub_agents ?? [];
  const gmvPaise = network?.network_gmv_paise ?? 0;
  const overrideBps = network?.master_override_bps ?? 2000;

  if (isLoading) return (
    <div className="flex items-center justify-center p-12">
      <div className="h-8 w-8 rounded-full border-2 border-teal border-t-transparent animate-spin" />
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="page-title text-2xl tracking-tight">Distributor Network</h1>
          <p className="page-subtitle mt-1">Manage your sub-agents and view network performance.</p>
        </div>
        <Button onClick={() => setIsFormOpen(!isFormOpen)} className="bg-teal hover:bg-teal-dark shadow-sm">
          <Plus className="w-4 h-4 mr-2" /> Add Sub-Agent
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-paper border-line shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Total Sub-Agents</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">{subAgents.length}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-paper border-line shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Network GMV</CardTitle>
            <Building className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">
              ₹{(gmvPaise / 100).toLocaleString("en-IN")}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Paid quotes across sub-agents</p>
          </CardContent>
        </Card>

        <Card className="bg-paper border-line shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Master Override</CardTitle>
            <ShieldCheck className="h-4 w-4 text-teal" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono tracking-tight text-ink">{(overrideBps / 100).toFixed(0)}%</div>
            <p className="text-xs text-muted-foreground mt-1">Commission on sub-agent bookings</p>
          </CardContent>
        </Card>
      </div>

      {isFormOpen && (
        <Card className="bg-surface border-teal/20 shadow-sm animate-in fade-in slide-in-from-top-4">
          <CardHeader className="bg-teal/5 border-b border-teal/10">
            <CardTitle className="text-lg">Register New Sub-Agent</CardTitle>
            <CardDescription>Create an organization and default admin account.</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {createdResult ? (
              <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-md shadow-sm">
                <p className="font-bold mb-2">Sub-agent created successfully!</p>
                <div className="space-y-1 font-mono text-sm mb-4">
                  <p>Email: <span className="font-semibold">{createdResult.admin_email}</span></p>
                  <p>Temp Password: <span className="font-semibold">{createdResult.default_password}</span></p>
                </div>
                <Button className="bg-emerald-600 hover:bg-emerald-700 text-white" onClick={() => { setCreatedResult(null); setIsFormOpen(false); }}>Close</Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-ink flex items-center gap-2"><Building className="w-4 h-4 text-muted-foreground"/> Agency Brand Name</label>
                  <Input
                    required
                    type="text"
                    className="bg-paper"
                    value={formData.brand_name}
                    onChange={e => setFormData({...formData, brand_name: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-ink flex items-center gap-2"><Mail className="w-4 h-4 text-muted-foreground"/> Admin Email</label>
                  <Input
                    required
                    type="email"
                    className="bg-paper"
                    value={formData.admin_email}
                    onChange={e => setFormData({...formData, admin_email: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-ink flex items-center gap-2"><User className="w-4 h-4 text-muted-foreground"/> Admin First Name</label>
                  <Input
                    required
                    type="text"
                    className="bg-paper"
                    value={formData.admin_first_name}
                    onChange={e => setFormData({...formData, admin_first_name: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-ink flex items-center gap-2"><User className="w-4 h-4 text-muted-foreground"/> Admin Last Name</label>
                  <Input
                    required
                    type="text"
                    className="bg-paper"
                    value={formData.admin_last_name}
                    onChange={e => setFormData({...formData, admin_last_name: e.target.value})}
                  />
                </div>
                <div className="md:col-span-2 flex justify-end mt-4 gap-3 pt-4 border-t border-line">
                  <Button type="button" variant="outline" onClick={() => setIsFormOpen(false)}>Cancel</Button>
                  <Button type="submit" disabled={isAdding} className="bg-teal hover:bg-teal-dark shadow-sm">Create Sub-Agent</Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      )}

      <div className="table-container shadow-sm border border-line/80 bg-paper">
        <Table>
          <TableHeader className="bg-surface/50">
            <TableRow>
              <TableHead>Agency Name</TableHead>
              <TableHead>Joined</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">GMV</TableHead>
              <TableHead className="text-right">Master Split</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {subAgents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-24 bg-surface/30">
                  <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                    <div className="h-16 w-16 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-5">
                      <Users className="w-6 h-6 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-ink mb-1">No sub-agents</h3>
                    <p className="text-sm text-muted-foreground">You haven't added any sub-agents to your network yet.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              subAgents.map(org => (
                <TableRow key={org.id} className="table-row-interactive hover:bg-teal/[0.02]">
                  <TableCell className="font-medium text-ink py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-teal/10 flex items-center justify-center border border-teal/20 text-teal">
                        <Building className="w-4 h-4" />
                      </div>
                      {org.brand_name}
                    </div>
                  </TableCell>
                  <TableCell className="py-4 text-muted-foreground">
                    {org.created_at ? new Date(org.created_at).toLocaleDateString() : "—"}
                  </TableCell>
                  <TableCell className="py-4">
                    {org.status === 'active' ? (
                      <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Active</Badge>
                    ) : (
                      <Badge className="bg-amber-50 text-amber-700 border-amber-200">Inactive</Badge>
                    )}
                  </TableCell>
                  <TableCell className="py-4 text-right">
                    <span className="font-mono text-ink font-medium">₹{((org.gmv_paise || 0) / 100).toLocaleString("en-IN")}</span>
                  </TableCell>
                  <TableCell className="py-4 text-right">
                    <span className="text-teal font-medium">{(overrideBps / 100).toFixed(0)}%</span>
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
