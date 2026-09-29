"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useGetCustomersQuery } from "@/lib/api/crmApi";
import { CustomerForm } from "@/components/crm/CustomerForm";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Users, Plus, Search, Loader2 } from "lucide-react";
import { format } from "date-fns";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function CustomersPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    const timeoutId = setTimeout(() => setDebouncedSearch(searchQuery), 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const { data, isLoading, isFetching } = useGetCustomersQuery({
    page: 1,
    limit: 50,
    search: debouncedSearch || undefined,
  });

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="page-title text-2xl tracking-tight">Customers</h1>
          <p className="page-subtitle mt-1">Manage your agency&apos;s clients and contacts.</p>
        </div>
        <div className="flex gap-3">
          {typeof data?.total === "number" && data.total > 0 && (
            <div className="flex items-center px-4 bg-surface border border-line rounded-md text-sm font-medium text-muted-foreground shadow-sm">
              {data.total} Total
            </div>
          )}
          <Button onClick={() => setIsDialogOpen(true)} className="bg-teal hover:bg-teal-dark shadow-sm">
            <Plus className="w-4 h-4 mr-2" /> Add Customer
          </Button>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Add New Customer</DialogTitle>
            </DialogHeader>
            <CustomerForm onSuccess={() => setIsDialogOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search by name, phone or email..." 
            className="pl-9 bg-paper border-line focus-visible:ring-teal h-11"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {isFetching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-teal animate-spin" />}
        </div>
      </div>

      <div className="table-container shadow-sm border border-line/80 bg-paper">
        <Table>
          <TableHeader className="bg-surface/50">
            <TableRow>
              <TableHead>Customer Name</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Email</TableHead>
              <TableHead className="text-right">Added On</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-24 bg-surface/30">
                  <div className="flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-teal" /></div>
                </TableCell>
              </TableRow>
            ) : data?.items?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-24 bg-surface/30">
                  <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                    <div className="h-16 w-16 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-5">
                      <Users className="w-6 h-6 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-ink mb-1">No customers found</h3>
                    <p className="text-sm text-muted-foreground mb-6">Get started by adding your first customer.</p>
                    <Button onClick={() => setIsDialogOpen(true)} variant="outline" className="shadow-sm">
                      <Plus className="w-4 h-4 mr-2" /> Add Customer
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              data?.items?.map((customer: any) => (
                <TableRow key={customer.id} className="table-row-interactive hover:bg-teal/[0.02]">
                  <TableCell className="font-medium py-4">
                    <Link
                      href={`/app/customers/${customer.id}`}
                      className="flex items-center gap-3 text-ink hover:text-teal group transition-colors"
                    >
                      <div className="h-9 w-9 rounded-full bg-teal/10 flex items-center justify-center text-teal font-medium flex-shrink-0 group-hover:bg-teal group-hover:text-white transition-colors">
                        {customer.first_name?.charAt(0)}{customer.last_name?.charAt(0)}
                      </div>
                      {customer.first_name} {customer.last_name}
                    </Link>
                  </TableCell>
                  <TableCell className="py-4 text-ink">{customer.phone_e164}</TableCell>
                  <TableCell className="py-4 text-muted-foreground">{customer.email || "—"}</TableCell>
                  <TableCell className="py-4 text-right text-muted-foreground text-sm">
                    {format(new Date(customer.created_at), "MMM d, yyyy")}
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
