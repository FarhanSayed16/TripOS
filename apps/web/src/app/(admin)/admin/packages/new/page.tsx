"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCreatePackageMutation } from "@/lib/api/packagesApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function NewPackagePage() {
  const router = useRouter();
  const [createPackage, { isLoading }] = useCreatePackageMutation();
  
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    destination: "",
    duration_days: 1,
    base_price_paise: 0,
    cover_image_url: ""
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const pkg = await createPackage({
        ...formData,
        description: formData.description || null,
        cover_image_url: formData.cover_image_url || null,
      }).unwrap();
      router.push(`/admin/packages/${pkg.id}`);
    } catch (err) {
      alert("Failed to create package. Check console for details.");
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-4">
        <Link href="/admin/packages" className="text-gray-500 hover:text-ink">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-ink">Create Package</h1>
          <p className="text-gray-500">Define the basic details of the new package.</p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-ink mb-1">Title</label>
              <input
                type="text"
                required
                className="w-full border border-line rounded-md px-3 py-2 focus:outline-none focus:border-focus"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="e.g. Exotic Bali Getaway"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-ink mb-1">Destination</label>
              <input
                type="text"
                required
                className="w-full border border-line rounded-md px-3 py-2 focus:outline-none focus:border-focus"
                value={formData.destination}
                onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
                placeholder="e.g. Bali, Indonesia"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Duration (Days)</label>
                <input
                  type="number"
                  required
                  min="1"
                  className="w-full border border-line rounded-md px-3 py-2 focus:outline-none focus:border-focus"
                  value={formData.duration_days}
                  onChange={(e) => setFormData({ ...formData, duration_days: parseInt(e.target.value) || 1 })}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Base Price (INR)</label>
                <input
                  type="number"
                  required
                  min="0"
                  className="w-full border border-line rounded-md px-3 py-2 focus:outline-none focus:border-focus"
                  value={formData.base_price_paise / 100}
                  onChange={(e) => setFormData({ ...formData, base_price_paise: Math.round(parseFloat(e.target.value) * 100) || 0 })}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-ink mb-1">Cover Image URL (Optional)</label>
              <input
                type="url"
                className="w-full border border-line rounded-md px-3 py-2 focus:outline-none focus:border-focus"
                value={formData.cover_image_url}
                onChange={(e) => setFormData({ ...formData, cover_image_url: e.target.value })}
                placeholder="https://example.com/image.jpg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink mb-1">Description (Optional)</label>
              <textarea
                className="w-full border border-line rounded-md px-3 py-2 focus:outline-none focus:border-focus min-h-[100px]"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                disabled={isLoading}
                className="bg-brand_primary hover:bg-brand_primary/90 text-white px-6 py-2 rounded-md font-medium transition-colors disabled:opacity-50"
              >
                {isLoading ? "Creating..." : "Create Package"}
              </button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
