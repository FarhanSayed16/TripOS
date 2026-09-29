"use client";

import { useGetAdminPaymentsQuery } from "@/lib/api/adminApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function AdminPaymentsPage() {
  const { data: payments, isLoading } = useGetAdminPaymentsQuery();

  if (isLoading) {
    return <div className="p-8 text-gray-500">Loading payments...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Global Payments</h1>
        <p className="text-gray-500">Monitor all transactions processed across the platform.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-500 uppercase bg-surface">
                <tr>
                  <th className="px-4 py-3">Agency</th>
                  <th className="px-4 py-3">Quote ID</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Gateway Order</th>
                  <th className="px-4 py-3">Date</th>
                </tr>
              </thead>
              <tbody>
                {payments?.map((payment) => (
                  <tr key={payment.id} className="border-b border-line last:border-0 hover:bg-gray-50/50">
                    <td className="px-4 py-3 font-medium text-ink">{payment.organization_name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">
                      {payment.quote_id.slice(0, 8)}...
                    </td>
                    <td className="px-4 py-3 font-medium">
                      ₹{(payment.amount / 100).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      {payment.status === "captured" && <Badge className="bg-green-100 text-green-800 border-green-200">Captured</Badge>}
                      {payment.status === "created" && <Badge variant="outline" className="text-gray-600">Created</Badge>}
                      {payment.status === "failed" && <Badge variant="destructive">Failed</Badge>}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">
                      {payment.gateway_order_id || "-"}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {new Date(payment.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
                {(!payments || payments.length === 0) && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                      No payments found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
