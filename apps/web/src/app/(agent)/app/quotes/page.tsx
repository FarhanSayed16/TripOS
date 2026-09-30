"use client";

import { useState } from "react";
import Link from "next/link";
import { format } from "date-fns";
import { Plus, Search, FileText, Link as LinkIcon, Eye } from "lucide-react";

import { useGetQuotesQuery } from "@/lib/api/quotesApi";
import { useGetCustomersQuery } from "@/lib/api/crmApi";
import { useGetMyOrganizationQuery } from "@/lib/api/orgApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toast";

export default function QuotesPage() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  
  const { data, isLoading, error } = useGetQuotesQuery(
    statusFilter ? { status: statusFilter } : {}
  );
  
  const { data: customersData } = useGetCustomersQuery({ limit: 50 });
  const { data: org } = useGetMyOrganizationQuery();

  const copyPublicLink = async (publicToken?: string) => {
    if (!publicToken) {
      toast.add({
        type: "error",
        title: "No public link yet",
        description: "Mark the quote ready to generate a shareable link.",
      });
      return;
    }
    const url = `${window.location.origin}/q/${publicToken}`;
    try {
      await navigator.clipboard.writeText(url);
      toast.add({
        type: "success",
        title: "Link copied",
        description: url,
      });
    } catch {
      toast.add({
        type: "error",
        title: "Could not copy",
        description: url,
      });
    }
  };
  const getStatusBadge = (status: string) => {
    const variant = ({
      draft: "draft",
      ready: "ready",
      sent: "sent",
      paid: "paid",
      expired: "expired",
      cancelled: "cancelled",
    } as Record<string, any>)[status] || "outline";
    return <Badge variant={variant}>{status.charAt(0).toUpperCase() + status.slice(1)}</Badge>;
  };

  const getCustomerName = (customerId: string) => {
    if (!customersData?.items) return "Loading...";
    const customer = customersData.items.find((c: any) => c.id === customerId);
    if (!customer) return `Customer ${customerId.substring(0, 4)}`;
    return `${customer.first_name} ${customer.last_name}`;
  };

  const getItinerarySummary = (quote: any) => {
    if (!quote.items || quote.items.length === 0) return "Empty Quote";
    
    // In a real app we'd look at the item details (origin/destination)
    // For now we just count types or use basic logic
    const flights = quote.items.filter((i: any) => i.item_type === 'flight' || !i.item_type).length;
    const hotels = quote.items.filter((i: any) => i.item_type === 'hotel').length;
    
    if (flights > 0 && hotels > 0) return `${flights} Flight${flights > 1 ? 's' : ''} + ${hotels} Hotel${hotels > 1 ? 's' : ''}`;
    if (flights > 0) return `${flights} Flight${flights > 1 ? 's' : ''} (Roundtrip)`;
    if (hotels > 0) return `${hotels} Hotel${hotels > 1 ? 's' : ''}`;
    return `${quote.items.length} Item${quote.items.length > 1 ? 's' : ''}`;
  };

  // Filter local search
  const filteredQuotes = data?.items?.filter(q => {
    if (!searchQuery) return true;
    const lowerQ = searchQuery.toLowerCase();
    const cName = getCustomerName(q.customer_id).toLowerCase();
    return q.id.toLowerCase().includes(lowerQ) || cName.includes(lowerQ);
  });

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="page-title text-2xl tracking-tight">Active Quotes</h1>
          <p className="page-subtitle mt-1">Manage and track all customer quotes.</p>
        </div>
        <Link href="/app/search">
          <Button className="rounded-lg px-6 h-11 bg-teal hover:bg-teal-dark text-white font-medium transition-all shadow-sm gap-2">
            <Plus className="w-4 h-4" />
            New Quote
          </Button>
        </Link>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="flex gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 hide-scrollbar bg-paper p-1 rounded-lg border border-line">
          {["", "paid", "ready", "draft"].map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-5 py-2 rounded-md text-sm font-medium transition-all capitalize whitespace-nowrap ${
                statusFilter === status 
                  ? "bg-surface shadow-sm text-ink font-semibold" 
                  : "text-muted-foreground hover:text-ink"
              }`}
            >
              {status || "All Quotes"}
            </button>
          ))}
        </div>
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search ID or Customer..." 
            className="pl-9 bg-paper border-line focus-visible:ring-teal h-11"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="table-container shadow-sm border border-line/80 bg-paper">
        <Table>
          <TableHeader className="bg-surface/50">
            <TableRow>
              <TableHead className="w-[180px]">Quote & Date</TableHead>
              <TableHead className="w-[200px]">Customer</TableHead>
              <TableHead>Itinerary</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Value</TableHead>
              <TableHead className="w-[100px] text-right"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-10 w-full rounded" /></TableCell>
                  <TableCell><Skeleton className="h-10 w-full rounded" /></TableCell>
                  <TableCell><Skeleton className="h-10 w-full rounded" /></TableCell>
                  <TableCell><Skeleton className="h-6 w-16 rounded-full" /></TableCell>
                  <TableCell className="text-right"><Skeleton className="h-6 w-20 ml-auto" /></TableCell>
                  <TableCell></TableCell>
                </TableRow>
              ))
            ) : error ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-12 text-coral">
                  Failed to load quotes. Please try again.
                </TableCell>
              </TableRow>
            ) : !filteredQuotes || filteredQuotes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-24 bg-surface/30">
                  <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                    <div className="h-16 w-16 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-5">
                      <FileText className="w-6 h-6 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-ink mb-1">No quotes found</h3>
                    <p className="text-sm text-muted-foreground mb-6">
                      {searchQuery || statusFilter ? "Try adjusting your filters or search." : "You haven't created any quotes yet."}
                    </p>
                    {(!searchQuery && !statusFilter) && (
                      <Link href="/app/search">
                        <Button className="rounded-lg px-6 bg-teal hover:bg-teal-dark">Build your first quote</Button>
                      </Link>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredQuotes.map((quote) => {
                const total = quote.items?.reduce((sum: number, item: any) => sum + item.customer_total, 0) || 0;
                
                return (
                  <TableRow key={quote.id} className="table-row-interactive group cursor-pointer transition-colors hover:bg-teal/[0.02]">
                    <TableCell className="font-medium align-top py-4">
                      <div className="flex flex-col">
                        <span className="font-mono text-ink">#{quote.id.substring(0, 8).toUpperCase()}</span>
                        <span className="text-[11px] text-muted-foreground mt-0.5">
                          {format(new Date(quote.created_at), "MMM d, HH:mm")}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="align-top py-4">
                      <div className="flex flex-col">
                        <span className="text-ink font-medium">{getCustomerName(quote.customer_id)}</span>
                        <span className="text-[11px] text-muted-foreground mt-0.5">{org?.brand_name || "Agency"}</span>
                      </div>
                    </TableCell>
                    <TableCell className="align-top py-4">
                      <span className="text-sm text-muted-foreground">{getItinerarySummary(quote)}</span>
                    </TableCell>
                    <TableCell className="align-top py-4">
                      {getStatusBadge(quote.status)}
                    </TableCell>
                    <TableCell className="text-right align-top py-4">
                      <span className="font-mono text-ink font-semibold tracking-tight text-base">
                        ₹{(total / 100).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </span>
                    </TableCell>
                    <TableCell className="text-right align-middle py-4">
                      <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-ink hover:bg-surface" title="Copy Link" onClick={(e) => { e.preventDefault(); e.stopPropagation(); void copyPublicLink(quote.public_token); }}>
                          <LinkIcon className="w-4 h-4" />
                        </Button>
                        <Link href={`/app/quotes/${quote.id}`}>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-teal hover:text-teal-dark hover:bg-teal/10" title="View Quote">
                            <Eye className="w-4 h-4" />
                          </Button>
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
