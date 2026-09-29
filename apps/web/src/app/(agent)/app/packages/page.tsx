"use client";

import { useGetPackagesQuery, usePackageToQuoteMutation } from "@/lib/api/packagesApi";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { MapPin, Clock, ArrowRight } from "lucide-react";
import Image from "next/image";
import { Button } from "@/components/ui/button";

export default function PackagesPage() {
  const { data, isLoading } = useGetPackagesQuery({ status: "published" });
  const [toQuote, { isLoading: isConverting }] = usePackageToQuoteMutation();
  const { user } = useAuth();
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="h-8 w-8 rounded-full border-2 border-teal border-t-transparent animate-spin" />
      </div>
    );
  }

  const packages = data?.items || [];

  const handleCreateQuote = async (packageId: string) => {
    // In a real app, you might prompt the agent to select a customer first.
    const customerIdStr = prompt("Enter Customer UUID to create quote for (or cancel):");
    if (!customerIdStr) return;
    
    try {
      const quote = await toQuote({ package_id: packageId, customer_id: customerIdStr }).unwrap();
      router.push(`/app/quotes/${quote.id}`);
    } catch (err: any) {
      alert(`Error creating quote: ${err.data?.detail || "Unknown error"}`);
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
    <div className="space-y-8 pb-10">
      <div>
        <h1 className="page-title text-2xl tracking-tight">Curated Packages</h1>
        <p className="page-subtitle mt-1">Pre-built travel packages ready to be converted into quotes.</p>
      </div>

      {packages.length === 0 ? (
        <div className="table-container bg-surface/30 shadow-sm border border-line py-24 text-center rounded-xl">
          <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
            <div className="h-16 w-16 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-5">
              <MapPin className="w-6 h-6 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-ink mb-1">No Packages Available</h3>
            <p className="text-sm text-muted-foreground">Check back later or ask your admin to publish packages.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {packages.map((pkg) => (
            <Card key={pkg.id} className="overflow-hidden flex flex-col bg-paper border-line shadow-sm hover:shadow-md transition-shadow">
              {pkg.cover_image_url ? (
                <div className="h-48 relative w-full bg-gray-100 border-b border-line">
                  <img
                    src={pkg.cover_image_url}
                    alt={pkg.title}
                    className="object-cover w-full h-full"
                  />
                </div>
              ) : (
                <div className="h-48 bg-surface border-b border-line flex items-center justify-center text-gray-400">
                  <MapPin className="w-10 h-10 opacity-20" />
                </div>
              )}
              
              <CardHeader className="pb-3 pt-5">
                <CardTitle className="text-lg text-ink leading-tight">{pkg.title}</CardTitle>
                <CardDescription className="flex items-center gap-1.5 mt-1.5 text-xs text-muted-foreground">
                  <MapPin className="w-3.5 h-3.5" /> {pkg.destination}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="flex-1 pb-4">
                <p className="text-sm text-muted-foreground line-clamp-3 mb-6">
                  {pkg.description || "No description provided."}
                </p>
                
                <div className="flex justify-between items-end border-t border-line/60 pt-4 mt-auto">
                  <div>
                    <div className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground mb-0.5">Starting from</div>
                    <div className="text-xl font-bold text-ink font-mono tracking-tight">{formatCurrency(pkg.base_price_paise)}</div>
                  </div>
                  <div className="flex items-center text-xs font-medium text-ink bg-surface border border-line px-2 py-1 rounded">
                    <Clock className="w-3.5 h-3.5 mr-1.5 text-teal" /> {pkg.duration_days} Days
                  </div>
                </div>
              </CardContent>
              
              <CardFooter className="pt-0 pb-5 px-6">
                <Button
                  onClick={() => handleCreateQuote(pkg.id)}
                  disabled={isConverting}
                  className="w-full bg-teal hover:bg-teal-dark shadow-sm gap-2"
                >
                  Create Quote
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
