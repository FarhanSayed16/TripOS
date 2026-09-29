"use client";

import { useGetAdminOrganizationsQuery, useApproveOrganizationMutation, useRejectOrganizationMutation } from "@/lib/api/adminApi";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, X, Search, FileText } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { format } from "date-fns";

export default function AdminAgentsPage() {
  const { data: orgs, isLoading } = useGetAdminOrganizationsQuery();
  const [approveOrg, { isLoading: isApproving }] = useApproveOrganizationMutation();
  const [rejectOrg, { isLoading: isRejecting }] = useRejectOrganizationMutation();
  
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal"></div>
      </div>
    );
  }

  const handleApprove = async (id: string) => {
    try {
      await approveOrg(id).unwrap();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async (id: string) => {
    try {
      await rejectOrg(id).unwrap();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredOrgs = orgs?.filter(org => {
    if (statusFilter && org.status !== statusFilter) return false;
    if (searchQuery && !org.brand_name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-8 pb-10">
      <div>
        <h1 className="page-title text-2xl tracking-tight">Agencies</h1>
        <p className="page-subtitle mt-1">Approve and manage travel agencies on the platform.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="flex gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 hide-scrollbar bg-paper p-1 rounded-lg border border-line">
          {["", "active", "pending_approval", "inactive"].map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-5 py-2 rounded-md text-sm font-medium transition-all capitalize whitespace-nowrap ${
                statusFilter === status 
                  ? "bg-surface shadow-sm text-ink font-semibold" 
                  : "text-muted-foreground hover:text-ink"
              }`}
            >
              {status === "" ? "All Agencies" : status.replace("_", " ")}
            </button>
          ))}
        </div>
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search agencies..." 
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
              <TableHead>Brand Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Joined</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!filteredOrgs || filteredOrgs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-24 bg-surface/30">
                  <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                    <div className="h-16 w-16 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-5">
                      <FileText className="w-6 h-6 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-ink mb-1">No agencies found</h3>
                    <p className="text-sm text-muted-foreground">Adjust filters to see results.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredOrgs.map((org) => (
                <TableRow key={org.id} className="table-row-interactive group hover:bg-teal/[0.02]">
                  <TableCell className="font-medium text-ink py-4">{org.brand_name}</TableCell>
                  <TableCell className="py-4">
                    {org.status === "active" && <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Active</Badge>}
                    {org.status === "pending_approval" && <Badge className="text-amber-700 border-amber-200 bg-amber-50">Pending</Badge>}
                    {org.status === "inactive" && <Badge className="bg-coral/10 text-coral border-coral/20">Suspended</Badge>}
                  </TableCell>
                  <TableCell className="py-4 text-muted-foreground">
                    {format(new Date(org.created_at), "MMM d, yyyy")}
                  </TableCell>
                  <TableCell className="py-4 text-right">
                    <div className="flex justify-end gap-2">
                      {org.status === "pending_approval" && (
                        <>
                          <Button 
                            variant="outline" 
                            size="sm"
                            className="text-emerald-600 border-emerald-200 hover:bg-emerald-50 shadow-sm"
                            onClick={() => handleApprove(org.id)}
                            disabled={isApproving || isRejecting}
                          >
                            <Check className="w-4 h-4 mr-1" /> Approve
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            className="text-coral border-coral/30 hover:bg-coral/10 shadow-sm"
                            onClick={() => handleReject(org.id)}
                            disabled={isApproving || isRejecting}
                          >
                            <X className="w-4 h-4 mr-1" /> Reject
                          </Button>
                        </>
                      )}
                      {org.status === "active" && (
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="text-coral hover:bg-coral/10 hover:text-coral-dark opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => handleReject(org.id)}
                          disabled={isApproving || isRejecting}
                        >
                          Suspend
                        </Button>
                      )}
                      {org.status === "inactive" && (
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="text-emerald-600 hover:bg-emerald-50 hover:text-emerald-700 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => handleApprove(org.id)}
                          disabled={isApproving || isRejecting}
                        >
                          Reactivate
                        </Button>
                      )}
                    </div>
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
