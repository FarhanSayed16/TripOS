"use client";

import { useGetPackagesQuery, useDeletePackageMutation } from "@/lib/api/packagesApi";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { Plus, Edit, Trash2 } from "lucide-react";

export default function AdminPackagesPage() {
  const { data, isLoading } = useGetPackagesQuery();
  const [deletePackage] = useDeletePackageMutation();

  if (isLoading) {
    return <div className="p-8 text-muted-foreground">Loading packages...</div>;
  }

  const packages = data?.items || [];

  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to delete this package?")) {
      await deletePackage(id);
    }
  };

  const formatCurrency = (paise: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(paise / 100);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-ink">Curated Packages</h1>
          <p className="text-muted-foreground">Manage standard travel packages for agents.</p>
        </div>
        <Link 
          href="/admin/packages/new"
          className="bg-brand_primary hover:bg-brand_primary/90 text-white px-4 py-2 rounded-md font-medium flex items-center transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Package
        </Link>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase bg-surface">
                <tr>
                  <th className="px-4 py-3">Title & Destination</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3">Base Price</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {packages.map((pkg) => (
                  <tr key={pkg.id} className="border-b border-line last:border-0 hover:bg-surface/50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-ink">{pkg.title}</div>
                      <div className="text-xs text-muted-foreground">{pkg.destination}</div>
                    </td>
                    <td className="px-4 py-3">{pkg.duration_days} Days</td>
                    <td className="px-4 py-3 font-medium">
                      {formatCurrency(pkg.base_price_paise)}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={pkg.status === "published" ? "default" : "secondary"}>
                        {pkg.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/admin/packages/${pkg.id}`}
                          className="text-focus hover:text-focus/80 p-1"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </Link>
                        <button
                          onClick={() => handleDelete(pkg.id)}
                          className="text-red-500 hover:text-red-700 p-1"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {packages.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                      No packages found. Click "Create Package" to get started.
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
