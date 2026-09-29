"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  useGetPackageQuery, 
  useUpdatePackageMutation, 
  usePublishPackageMutation,
  useAddPackageItemMutation,
  useRemovePackageItemMutation
} from "@/lib/api/packagesApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Check, Trash2, Plus } from "lucide-react";
import Link from "next/link";

export default function PackageDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const { data: pkg, isLoading, refetch } = useGetPackageQuery(id);
  const [updatePackage] = useUpdatePackageMutation();
  const [publishPackage, { isLoading: isPublishing }] = usePublishPackageMutation();
  const [addItem, { isLoading: isAdding }] = useAddPackageItemMutation();
  const [removeItem] = useRemovePackageItemMutation();

  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    destination: "",
    duration_days: 1,
    base_price_paise: 0,
  });

  const [newItem, setNewItem] = useState({
    type: "flight",
    title: "",
    estimated_cost_paise: 0,
  });

  if (isLoading) return <div className="p-8">Loading package details...</div>;
  if (!pkg) return <div className="p-8 text-red-500">Package not found</div>;

  const handleEditInit = () => {
    setFormData({
      title: pkg.title,
      destination: pkg.destination,
      duration_days: pkg.duration_days,
      base_price_paise: pkg.base_price_paise,
    });
    setIsEditing(true);
  };

  const handleUpdate = async () => {
    await updatePackage({ id, data: formData });
    setIsEditing(false);
  };

  const handlePublish = async () => {
    if (pkg.items.length === 0) {
      alert("Add at least one item before publishing.");
      return;
    }
    if (confirm("Are you sure you want to publish this package? It will be visible to all agents.")) {
      await publishPackage(id);
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    await addItem({ 
      package_id: id, 
      data: {
        ...newItem,
        sort_order: pkg.items.length
      } 
    });
    setNewItem({ type: "flight", title: "", estimated_cost_paise: 0 });
  };

  const handleRemoveItem = async (itemId: string) => {
    if (confirm("Remove this item?")) {
      await removeItem({ package_id: id, item_id: itemId });
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
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/admin/packages" className="text-muted-foreground hover:text-ink">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-ink">{pkg.title}</h1>
              <Badge variant={pkg.status === "published" ? "default" : "secondary"}>
                {pkg.status}
              </Badge>
            </div>
            <p className="text-muted-foreground">{pkg.destination} • {pkg.duration_days} Days</p>
          </div>
        </div>
        <div className="flex gap-2">
          {pkg.status === "draft" && (
            <button
              onClick={handlePublish}
              disabled={isPublishing || pkg.items.length === 0}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium transition-colors disabled:opacity-50"
            >
              Publish Package
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Package Items</CardTitle>
            </CardHeader>
            <CardContent>
              {pkg.items.length === 0 ? (
                <div className="text-center py-6 text-muted-foreground bg-surface rounded-md border border-dashed border-line">
                  No items in this package yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {pkg.items.map((item) => (
                    <div key={item.id} className="flex justify-between items-center p-3 border border-line rounded-md hover:border-line">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{item.type}</Badge>
                          <span className="font-medium">{item.title}</span>
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">
                          Est. Cost: {formatCurrency(item.estimated_cost_paise)}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveItem(item.id)}
                        className="text-red-500 hover:text-red-700 p-2"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-6 pt-6 border-t border-line">
                <h3 className="text-sm font-medium mb-3">Add New Item</h3>
                <form onSubmit={handleAddItem} className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <select
                      className="border border-line rounded-md px-3 py-2 focus:outline-none focus:border-focus"
                      value={newItem.type}
                      onChange={(e) => setNewItem({ ...newItem, type: e.target.value })}
                    >
                      <option value="flight">Flight</option>
                      <option value="hotel">Hotel</option>
                      <option value="transfer">Transfer</option>
                      <option value="activity">Activity</option>
                    </select>
                    <input
                      type="text"
                      required
                      placeholder="Item Title"
                      className="col-span-2 border border-line rounded-md px-3 py-2 focus:outline-none focus:border-focus"
                      value={newItem.title}
                      onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
                    />
                  </div>
                  <div className="flex gap-3">
                    <input
                      type="number"
                      required
                      min="0"
                      placeholder="Estimated Cost (INR)"
                      className="flex-1 border border-line rounded-md px-3 py-2 focus:outline-none focus:border-focus"
                      value={newItem.estimated_cost_paise ? newItem.estimated_cost_paise / 100 : ""}
                      onChange={(e) => setNewItem({ ...newItem, estimated_cost_paise: Math.round(parseFloat(e.target.value) * 100) || 0 })}
                    />
                    <button
                      type="submit"
                      disabled={isAdding}
                      className="bg-surface hover:bg-line text-ink px-4 py-2 rounded-md font-medium flex items-center transition-colors disabled:opacity-50"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Item
                    </button>
                  </div>
                </form>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Details</CardTitle>
              {!isEditing && (
                <button onClick={handleEditInit} className="text-focus text-sm hover:underline">
                  Edit
                </button>
              )}
            </CardHeader>
            <CardContent>
              {isEditing ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-muted-foreground">Title</label>
                    <input
                      type="text"
                      className="w-full border border-line rounded-md px-2 py-1 text-sm mt-1"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Destination</label>
                    <input
                      type="text"
                      className="w-full border border-line rounded-md px-2 py-1 text-sm mt-1"
                      value={formData.destination}
                      onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-muted-foreground">Days</label>
                      <input
                        type="number"
                        className="w-full border border-line rounded-md px-2 py-1 text-sm mt-1"
                        value={formData.duration_days}
                        onChange={(e) => setFormData({ ...formData, duration_days: parseInt(e.target.value) || 1 })}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Base Price (₹)</label>
                      <input
                        type="number"
                        className="w-full border border-line rounded-md px-2 py-1 text-sm mt-1"
                        value={formData.base_price_paise / 100}
                        onChange={(e) => setFormData({ ...formData, base_price_paise: Math.round(parseFloat(e.target.value) * 100) || 0 })}
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      onClick={() => setIsEditing(false)}
                      className="px-3 py-1 text-sm text-muted-foreground hover:bg-surface rounded-md"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleUpdate}
                      className="px-3 py-1 text-sm bg-brand_primary text-white rounded-md hover:bg-brand_primary/90"
                    >
                      Save
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <div className="text-xs text-muted-foreground">Base Price</div>
                    <div className="font-medium">{formatCurrency(pkg.base_price_paise)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Duration</div>
                    <div className="font-medium">{pkg.duration_days} Days</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Destination</div>
                    <div className="font-medium">{pkg.destination}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Total Items</div>
                    <div className="font-medium">{pkg.items.length} items</div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
