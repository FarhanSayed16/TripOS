"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ShieldAlert, ShieldCheck, Activity, Power, PowerOff } from "lucide-react";
import { apiSlice } from "@/lib/apiSlice";

const adminSuppliersApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getSuppliers: builder.query<any, void>({
      query: () => "/admin/suppliers",
      providesTags: ["Suppliers"],
    }),
    toggleSupplier: builder.mutation<any, { code: string; disable: boolean }>({
      query: ({ code, disable }) => ({
        url: `/admin/suppliers/${code}/toggle?disable=${disable}`,
        method: "POST",
      }),
      invalidatesTags: ["Suppliers"],
    }),
  }),
});

export const { useGetSuppliersQuery, useToggleSupplierMutation } = adminSuppliersApi;

export default function SuppliersAdminPage() {
  const { data, isLoading } = useGetSuppliersQuery();
  const [toggleSupplier] = useToggleSupplierMutation();

  const handleToggle = async (code: string, currentIsOverride: boolean) => {
    if (confirm(`Are you sure you want to ${currentIsOverride ? 'enable' : 'disable'} this supplier?`)) {
      try {
        await toggleSupplier({ code, disable: !currentIsOverride }).unwrap();
      } catch (e) {
        alert("Failed to toggle supplier status.");
      }
    }
  };

  if (isLoading) {
    return <div className="p-8 text-gray-500">Loading suppliers...</div>;
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-ink">Suppliers & Strategies</h1>
        <p className="text-gray-500 mt-2">Manage inventory suppliers, view circuit breaker status, and configure failover strategies.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Global Routing Strategy</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 p-4 bg-sand/30 rounded-md border border-line">
            <div className="flex-1">
              <p className="font-semibold text-ink capitalize">{data?.global_strategy.replace('_', ' ')}</p>
              <p className="text-sm text-gray-500 mt-1">
                {data?.global_strategy === 'all' && "Queries all configured suppliers in parallel and merges results."}
                {data?.global_strategy === 'primary_only' && "Queries only the primary configured supplier."}
                {data?.global_strategy === 'failover' && "Queries suppliers sequentially for failover (active mode: all via inventory.py logic)."}
              </p>
            </div>
            <Badge variant="outline">Configured via ENV</Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data?.suppliers.map((supplier: any) => (
          <Card key={supplier.code} className={supplier.is_open ? 'border-red-200 bg-red-50/20' : ''}>
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-ink">{supplier.name}</h3>
                  <p className="text-sm text-gray-500 font-mono mt-1">{supplier.code}</p>
                </div>
                <Badge variant={supplier.status === "Active" ? "default" : supplier.status === "Failing" ? "destructive" : "secondary"}>
                  {supplier.status}
                </Badge>
              </div>
              {supplier.health && (
                <div className="grid grid-cols-3 gap-2 mb-4 text-xs text-gray-600">
                  <div className="bg-sand/40 rounded p-2">
                    <p className="text-gray-400">p95</p>
                    <p className="font-semibold text-ink">
                      {supplier.health.latency_p95_ms != null
                        ? `${supplier.health.latency_p95_ms} ms`
                        : "—"}
                    </p>
                  </div>
                  <div className="bg-sand/40 rounded p-2">
                    <p className="text-gray-400">Errors</p>
                    <p className="font-semibold text-ink">
                      {(supplier.health.error_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-sand/40 rounded p-2">
                    <p className="text-gray-400">Samples</p>
                    <p className="font-semibold text-ink">{supplier.health.sample_count}</p>
                  </div>
                </div>
              )}
              {data?.last_search_offer_counts?.supplier_counts?.[supplier.code] != null && (
                <p className="text-xs text-gray-500 mb-3">
                  Last search offers:{" "}
                  <span className="font-semibold text-ink">
                    {data.last_search_offer_counts.supplier_counts[supplier.code]}
                  </span>
                </p>
              )}

              <div className="space-y-4 mb-6">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-500 flex items-center gap-2">
                    <Activity className="w-4 h-4" /> Circuit State
                  </span>
                  <span className="font-semibold">{supplier.circuit_state}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-500 flex items-center gap-2">
                    {supplier.is_open ? <ShieldAlert className="w-4 h-4 text-red-500" /> : <ShieldCheck className="w-4 h-4 text-green-500" />} 
                    Routing Status
                  </span>
                  <span className={supplier.is_open ? "text-red-600 font-medium" : "text-green-600 font-medium"}>
                    {supplier.is_open ? 'Traffic Blocked' : 'Accepting Traffic'}
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-500">Recent Failures</span>
                  <span className="font-mono">{supplier.failures}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-500">In Config List</span>
                  <span>{supplier.is_configured ? 'Yes' : 'No'}</span>
                </div>
              </div>

              <button
                onClick={() => handleToggle(supplier.code, supplier.is_manual_override)}
                className={`w-full py-2 px-4 rounded-md font-medium flex items-center justify-center gap-2 transition-colors ${
                  supplier.is_manual_override 
                  ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                  : 'bg-red-50 text-red-600 hover:bg-red-100'
                }`}
              >
                {supplier.is_manual_override ? <Power className="w-4 h-4" /> : <PowerOff className="w-4 h-4" />}
                {supplier.is_manual_override ? 'Enable Supplier' : 'Disable (Kill Switch)'}
              </button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
