"use client";

import { use, useState } from "react";
import { format } from "date-fns";
import { Copy, ExternalLink, CheckCircle2, Clock, Check, CreditCard, XCircle, FileText, MessageCircle, AlertCircle, Plane, ChevronRight, Phone, Mail, FileCheck, Building2, User } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useGetQuoteQuery, useGeneratePaymentLinkMutation, useCancelQuoteMutation, useGetQuoteAuditEventsQuery, useRefreshQuoteMutation, useGetQuoteFareRulesQuery, useGetQuoteRefundsQuery } from "@/lib/api/quotesApi";
import { useGetCustomersQuery } from "@/lib/api/crmApi";
import { useGetBookingDocumentsQuery, useUploadDocumentMutation, useDeleteDocumentMutation } from "@/lib/api/documentsApi";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { needsManualSupportCopy, formatFailureReason } from "@/lib/failureLabels";
import { formatMoney, formatPaiseAsMoney, fxFootnote } from "@/lib/money";
import { QuoteExtrasPanel } from "../components/QuoteExtrasPanel";
import { NormalizedOffer } from "@/lib/api/inventoryApi";

type FareChangeInfo = {
  message: string;
  previous_total_paise?: number;
  new_total_paise?: number;
};

function formatPaise(paise: number) {
  return formatPaiseAsMoney(paise, { currency: "INR" });
}

export default function QuoteDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const router = useRouter();
  const { data: quote, isLoading, error } = useGetQuoteQuery(resolvedParams.id);
  const { data: auditEvents } = useGetQuoteAuditEventsQuery(resolvedParams.id);
  const { data: fareRules } = useGetQuoteFareRulesQuery(resolvedParams.id);
  const { data: refunds } = useGetQuoteRefundsQuery(resolvedParams.id);
  const { data: customersData } = useGetCustomersQuery({ limit: 50 });
  const [copied, setCopied] = useState(false);
  const [fareChange, setFareChange] = useState<FareChangeInfo | null>(null);

  const [generatePaymentLink, { isLoading: isGeneratingPayment }] = useGeneratePaymentLinkMutation();
  const [refreshQuote, { isLoading: isRefreshing }] = useRefreshQuoteMutation();
  const [cancelQuote, { isLoading: isCanceling }] = useCancelQuoteMutation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal"></div>
      </div>
    );
  }

  if (error || !quote) {
    return <div className="p-8 text-center text-red-500">Failed to load quote details.</div>;
  }

  const publicLink = `${window.location.origin}/q/${quote.public_token}`; // We'll assume a /q/ router for public

  const handleCopyLink = () => {
    navigator.clipboard.writeText(publicLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleGeneratePayment = async () => {
    try {
      await generatePaymentLink(quote.id).unwrap();
      alert("Payment link generated! The public page will now route customers to checkout.");
    } catch (err: any) {
      const msg =
        err?.data?.message ||
        err?.data?.detail ||
        (typeof err?.data === "string" ? err.data : null) ||
        "Unknown error";
      const code = err?.data?.error_code;
      if (code === "FARE_CHANGED") {
        setFareChange({
          message: msg,
          previous_total_paise:
            typeof err?.data?.previous_total_paise === "number"
              ? err.data.previous_total_paise
              : undefined,
          new_total_paise:
            typeof err?.data?.new_total_paise === "number"
              ? err.data.new_total_paise
              : undefined,
        });
      } else if (code === "SOLD_OUT") {
        alert(`Sold out — pay link blocked.\n${msg}`);
      } else {
        alert("Failed to generate payment: " + msg);
      }
    }
  };

  const handleAcceptNewFare = async () => {
    try {
      const refreshed = await refreshQuote(quote.id).unwrap();
      setFareChange(null);
      router.push(`/app/quotes/${refreshed.id}`);
    } catch (err: any) {
      alert(err?.data?.message || err?.data?.detail || "Could not refresh quote");
    }
  };

  const handleCancelQuote = async () => {
    if (!confirm("Are you sure you want to cancel this quote? If it has a booking, this will attempt to cancel the supplier booking.")) return;
    try {
      await cancelQuote(quote.id).unwrap();
      alert("Quote cancelled successfully.");
    } catch (err: any) {
      alert("Failed to cancel: " + (err?.data?.detail || "Unknown error"));
    }
  };

  const total = quote.items.reduce((sum, item) => sum + item.customer_total, 0);
  const customer = customersData?.items?.find((c: any) => c.id === quote.customer_id);

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-20 animate-in fade-in duration-500">
      
      {/* Fare Change Dialog */}
      <Dialog open={!!fareChange} onOpenChange={(open) => !open && setFareChange(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Fare changed</DialogTitle>
            <DialogDescription>
              {fareChange?.message ||
                "The supplier price changed before payment. Accept the new fare to refresh this quote, or stay on the current quote."}
            </DialogDescription>
          </DialogHeader>
          {(fareChange?.previous_total_paise != null || fareChange?.new_total_paise != null) && (
            <div className="grid grid-cols-2 gap-3 text-sm py-2">
              <div className="rounded-lg border border-line bg-sand/30 p-3">
                <p className="text-xs text-muted-foreground mb-1">Previous fare</p>
                <p className="font-semibold text-ink">
                  {fareChange.previous_total_paise != null
                    ? formatPaise(fareChange.previous_total_paise)
                    : "—"}
                </p>
              </div>
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                <p className="text-xs text-amber-800 mb-1">New fare</p>
                <p className="font-semibold text-amber-900">
                  {fareChange.new_total_paise != null
                    ? formatPaise(fareChange.new_total_paise)
                    : "—"}
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setFareChange(null)} disabled={isRefreshing}>
              Stay on quote
            </Button>
            <Button onClick={handleAcceptNewFare} disabled={isRefreshing} className="bg-teal hover:bg-teal-dark">
              {isRefreshing ? "Refreshing…" : "Accept new fare"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Booking Alert Banners */}
      {quote.booking?.status === 'failed' && (
        <div className="bg-coral/10 border-l-4 border-coral p-4 rounded-r-md flex items-start space-x-3 mb-6">
          <AlertCircle className="w-5 h-5 text-coral mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-coral-dark">Booking Failed (Action Required)</h3>
            <p className="text-sm text-coral-dark/90 mt-1">
              {needsManualSupportCopy(quote.booking.failure_reason)}
            </p>
            {quote.booking.failure_reason && (
              <p className="text-xs text-coral mt-2 font-mono bg-white/50 inline-block px-2 py-0.5 rounded">
                code: {quote.booking.failure_reason} — {formatFailureReason(quote.booking.failure_reason)}
              </p>
            )}
          </div>
        </div>
      )}

      {/* 1. Page Shell - Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-line pb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-4xl font-mono font-bold tracking-tight text-ink">
              {quote.booking?.supplier_pnr || `#Q-${quote.id.substring(0,8).toUpperCase()}`}
            </h1>
            <Badge variant={quote.status === 'paid' || quote.status === 'ready' ? 'default' : 'outline'} className={`capitalize text-sm ${quote.status === 'paid' ? 'bg-mint text-mint-foreground' : ''}`}>
              {quote.status}
            </Badge>
            {quote.booking?.status === 'confirmed' && (
              <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Confirmed Booking</Badge>
            )}
            {quote.booking?.status === 'cancelled' && (
              <Badge className="bg-surface text-ink border-line">Cancelled Booking</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground flex items-center gap-2">
            <Clock className="w-4 h-4" /> Created {format(new Date(quote.created_at), "MMM d, yyyy")} &bull; Valid until {format(new Date(quote.valid_until), "MMM d, h:mm a")}
          </p>
        </div>
        
        <div className="flex gap-3 mt-6 md:mt-0">
          {(quote.status === "ready" || quote.status === "sent") && (
            <Button onClick={handleGeneratePayment} disabled={isGeneratingPayment} className="gap-2 bg-teal hover:bg-teal-dark shadow-sm h-11 px-6">
              <CreditCard className="w-4 h-4" />
              Generate Pay Link
            </Button>
          )}

          {quote.status === "paid" && quote.booking?.id && (
            <Link
              href={`/app/bookings`}
              className={cn(buttonVariants({ variant: "default" }), "gap-2 bg-mint hover:bg-mint/90 text-white shadow-sm h-11 px-6")}
            >
              <FileCheck className="w-4 h-4" />
              View booking
            </Link>
          )}

          {quote.status === "ready" && (
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleCopyLink} className="gap-2 h-11 bg-paper border-line">
                {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                {copied ? "Copied" : "Copy Link"}
              </Button>
              <Link
                href={`/app/quotes/${quote.id}/send`}
                className={cn(
                  buttonVariants(),
                  "bg-[#25D366] hover:bg-[#128C7E] text-white gap-2 h-11"
                )}
              >
                <MessageCircle className="w-4 h-4" />
                WhatsApp
              </Link>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-8">
        {/* 2. Main Details Block (Left) */}
        <div className="space-y-8">
          
          {/* Passenger List */}
          <Card className="border-line shadow-sm overflow-hidden bg-surface">
            <div className="bg-paper/50 px-5 py-3 border-b border-line flex items-center gap-2">
              <User className="w-4 h-4 text-muted-foreground" />
              <h3 className="font-semibold text-ink text-sm uppercase tracking-wide">Passengers</h3>
            </div>
            <div className="p-0">
              <table className="w-full text-sm">
                <thead className="bg-sand/30 text-muted-foreground text-xs uppercase tracking-wider text-left">
                  <tr>
                    <th className="px-5 py-3 font-medium">Name</th>
                    <th className="px-5 py-3 font-medium">DOB</th>
                    <th className="px-5 py-3 font-medium">Passport</th>
                    <th className="px-5 py-3 font-medium text-right">Ticket No.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line/60">
                  {quote.passengers.map((p, i) => (
                    <tr key={i} className="hover:bg-sand/10 transition-colors">
                      <td className="px-5 py-3 font-medium text-ink flex items-center gap-2">
                        {p.first_name} {p.last_name}
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">{p.date_of_birth || '—'}</td>
                      <td className="px-5 py-3 text-muted-foreground">{p.passport_number || '—'}</td>
                      <td className="px-5 py-3 text-right font-mono text-xs text-muted-foreground">
                        {quote.booking?.supplier_pnr || (quote.booking?.status === "confirmed" ? "—" : "Pending")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Flight Itinerary */}
          <div className="space-y-4">
            <h3 className="font-semibold text-ink text-lg">Itinerary</h3>
            {quote.items.map((item) => {
              const offer = item.offer as NormalizedOffer;
              return (
                <Card key={item.id} className="relative overflow-hidden border-line shadow-sm bg-paper group">
                  <div className={`absolute top-0 left-0 w-1 h-full ${quote.booking?.status === 'confirmed' ? 'bg-mint' : 'bg-teal'}`} />
                  <CardContent className="p-5 pl-6">
                    <div className="flex justify-between items-start mb-5">
                      <div>
                        <h4 className="font-semibold text-ink text-sm flex items-center gap-2">
                          {offer.type === 'flight' ? <Plane className="w-4 h-4 text-teal"/> : <Building2 className="w-4 h-4 text-teal"/>}
                          {offer.title}
                        </h4>
                        <p className="text-xs text-muted-foreground mt-1 font-mono">Item ID: {item.offer_snapshot_id.substring(0,8)}</p>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline" className={`font-mono text-xs ${quote.booking?.status === 'confirmed' ? 'border-mint text-mint' : 'border-amber-500 text-amber-600'}`}>
                          {quote.booking?.status === 'confirmed' ? 'HK (Confirmed)' : 'Unconfirmed'}
                        </Badge>
                      </div>
                    </div>

                    {/* Rich Segments */}
                    {offer.segments && offer.segments.length > 0 ? (
                      <div className="relative pl-4 border-l-2 border-line/60 space-y-5 ml-1">
                        {offer.segments.map((seg, i) => (
                          <div key={i} className="relative">
                            <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-surface border-2 border-teal" />
                            <div className="text-sm font-semibold text-ink flex items-center gap-2">
                              {seg.origin} <ChevronRight className="w-3 h-3 text-muted-foreground" /> {seg.destination}
                            </div>
                            <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                              <span className="font-mono bg-sand/50 px-1.5 py-0.5 rounded border border-line/50">{seg.flight_number}</span>
                              <span>&middot;</span>
                              <span>{seg.marketing_carrier} {seg.operating_carrier !== seg.marketing_carrier ? `(Op ${seg.operating_carrier})` : ""}</span>
                            </div>
                            {seg.departure_at && (
                              <div className="text-xs text-ink mt-1.5 flex items-center gap-1.5 bg-paper border border-line/40 inline-flex px-2 py-1 rounded">
                                <Clock className="w-3.5 h-3.5 text-teal" /> 
                                <span className="font-medium">{format(new Date(seg.departure_at), "MMM d, yyyy h:mm a")}</span>
                              </div>
                            )}
                          </div>
                        ))}
                        <div className="absolute -left-[21px] -bottom-1 w-2.5 h-2.5 rounded-full bg-surface border-2 border-teal" />
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground">{offer.description}</div>
                    )}
                    
                    <div className="mt-6 border-t border-line/60 pt-4">
                      <QuoteExtrasPanel
                        quoteId={quote.id}
                        item={item}
                        offer={offer || null}
                        editable={quote.status === "draft" || quote.status === "ready"}
                      />
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Fare Rules */}
          {fareRules && (
            <Card className="border-line shadow-sm bg-surface">
              <CardHeader className="bg-paper/50 border-b border-line pb-3">
                <CardTitle className="text-sm flex items-center gap-2 text-ink uppercase tracking-wide">
                  <FileText className="w-4 h-4 text-muted-foreground" />
                  Fare Rules & Conditions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 pt-4 text-sm">
                <div className="flex flex-wrap gap-2 mb-2">
                  <Badge className="bg-paper text-ink border-line shadow-sm">
                    Refundable:{" "}
                    <span className="font-semibold ml-1">
                      {fareRules.is_refundable === true ? "Yes" : fareRules.is_refundable === false ? "No" : "Unknown"}
                    </span>
                  </Badge>
                  <Badge className="bg-paper text-ink border-line shadow-sm">
                    Changes:{" "}
                    <span className="font-semibold ml-1">
                      {fareRules.change_allowed === true ? "May be allowed" : fareRules.change_allowed === false ? "Restricted" : "Unknown"}
                    </span>
                  </Badge>
                  <Badge variant="secondary" className="bg-sand/50 text-muted-foreground">{fareRules.source}</Badge>
                </div>
                {fareRules.cancel_penalty_summary && (
                  <p className="text-ink bg-paper p-3 rounded border border-line text-xs">
                    <span className="font-semibold text-coral block mb-1">Cancel Policy</span>
                    {fareRules.cancel_penalty_summary}
                  </p>
                )}
                {fareRules.change_penalty_summary && (
                  <p className="text-ink bg-paper p-3 rounded border border-line text-xs">
                    <span className="font-semibold text-amber-600 block mb-1">Change Policy</span>
                    {fareRules.change_penalty_summary}
                  </p>
                )}
                {fareRules.baggage_summary && (
                  <p className="text-ink bg-paper p-3 rounded border border-line text-xs">
                    <span className="font-semibold text-teal block mb-1">Baggage Allowance</span>
                    {fareRules.baggage_summary}
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Booking Documents Section (Phase 34) */}
          {quote.booking && (
            <BookingDocuments bookingId={quote.booking.id} />
          )}
        </div>

        {/* 3. Right Summary Block */}
        <div className="space-y-6 lg:sticky lg:top-24 lg:self-start">
          
          {/* Contact Details Card */}
          <Card className="border-line shadow-sm bg-surface">
            <CardHeader className="pb-3 border-b border-line bg-paper/50">
              <CardTitle className="text-sm font-semibold text-ink">Contact Details</CardTitle>
            </CardHeader>
            <CardContent className="p-5">
              {customer ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-teal/10 flex items-center justify-center text-teal font-bold uppercase">
                      {customer.first_name[0]}{customer.last_name[0]}
                    </div>
                    <div>
                      <p className="font-semibold text-ink">{customer.first_name} {customer.last_name}</p>
                      <p className="text-xs text-muted-foreground">Customer</p>
                    </div>
                  </div>
                  <div className="pt-3 space-y-2 text-sm border-t border-line/60">
                    <div className="flex items-center gap-2 text-ink">
                      <Phone className="w-4 h-4 text-muted-foreground" />
                      <span className="font-mono">{customer.phone_e164}</span>
                    </div>
                    {customer.email && (
                      <div className="flex items-center gap-2 text-ink">
                        <Mail className="w-4 h-4 text-muted-foreground" />
                        <span>{customer.email}</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Loading customer details...</p>
              )}
            </CardContent>
          </Card>

          {/* Payment & Invoice Card */}
          <Card className="border-line shadow-sm bg-surface overflow-hidden">
            <div className={`px-5 py-3 ${quote.status === 'paid' ? 'bg-mint text-mint-foreground' : 'bg-surface text-ink/80'} border-b border-line`}>
              <h3 className="font-semibold text-sm">Payment Status: {quote.status === 'paid' ? 'Paid' : 'Pending'}</h3>
            </div>
            <CardContent className="p-5 space-y-4">
              {/* Markup Ladder (§6.5) */}
              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-muted-foreground">
                  <span>Supplier Cost</span>
                  <span className="font-mono">
                    {(() => {
                      const supplier = quote.items.reduce((s, i) => s + (i.supplier_cost ?? 0), 0);
                      return supplier > 0
                        ? formatPaiseAsMoney(supplier, { currency: quote.charge_currency || "INR" })
                        : "—";
                    })()}
                  </span>
                </div>
                <div className="flex justify-between text-muted-foreground">
                  <span>Platform Fee</span>
                  <span className="font-mono">
                    {formatPaiseAsMoney(
                      quote.items.reduce((s, i) => s + (i.platform_fee ?? 0), 0),
                      { currency: quote.charge_currency || "INR" }
                    )}
                  </span>
                </div>
                <div className="flex justify-between text-ink font-medium">
                  <span>Agent Markup</span>
                  <span className="font-mono text-teal">
                    {formatPaiseAsMoney(
                      quote.items.reduce((s, i) => s + (i.agent_markup ?? 0), 0),
                      { currency: quote.charge_currency || "INR" }
                    )}
                  </span>
                </div>
                {quote.items.some(i => (i.extras_total ?? 0) > 0) && (
                  <div className="flex justify-between text-muted-foreground">
                    <span>Extras (Ancillaries)</span>
                    <span className="font-mono">
                      {formatPaiseAsMoney(
                        quote.items.reduce((s, i) => s + (i.extras_total ?? 0), 0),
                        { currency: quote.charge_currency || "INR" }
                      )}
                    </span>
                  </div>
                )}
              </div>
              <div className="flex justify-between items-end border-t border-line pt-4">
                <span className="font-semibold text-ink">Customer Total</span>
                <span className="text-2xl font-bold font-mono tracking-tight text-ink">
                  {quote.items[0]?.money
                    ? formatMoney({
                        ...quote.items[0].money,
                        display_amount: quote.items.reduce(
                          (s, i) => s + (i.money?.display_amount ?? i.customer_total / 100),
                          0
                        ),
                      })
                    : formatPaiseAsMoney(total, { currency: quote.charge_currency || "INR" })}
                </span>
              </div>
              
              <div className="pt-2">
                <Button
                  variant="outline"
                  disabled
                  title="Invoice PDF is not available yet"
                  className="w-full gap-2 border-dashed border-2"
                >
                  <ExternalLink className="w-4 h-4 text-muted-foreground" />
                  Invoice PDF (coming soon)
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Meta Card (§6.6) */}
          <Card className="border-line shadow-sm bg-surface">
            <CardHeader className="pb-3 border-b border-line bg-paper/50">
              <CardTitle className="text-sm font-semibold text-ink">Quote Details</CardTitle>
            </CardHeader>
            <CardContent className="p-5">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="stat-label">Inventory Mode</span>
                  <p className="font-medium text-ink mt-0.5 capitalize">
                    {quote.items[0]?.offer?.inventory_mode || "—"}
                  </p>
                </div>
                <div>
                  <span className="stat-label">Fare Family</span>
                  <p className="font-medium text-ink mt-0.5">
                    {quote.items[0]?.offer?.fare_family || "—"}
                  </p>
                </div>
                <div>
                  <span className="stat-label">Deal Code</span>
                  <p className="font-medium font-mono text-ink mt-0.5">
                    {quote.items[0]?.offer?.deal_code || "None"}
                  </p>
                </div>
                <div>
                  <span className="stat-label">Valid Until</span>
                  <p className="font-medium text-ink mt-0.5">
                    {format(new Date(quote.valid_until), "MMM d, h:mm a")}
                  </p>
                </div>
                <div className="col-span-2">
                  <span className="stat-label">Created</span>
                  <p className="font-medium text-ink mt-0.5">
                    {format(new Date(quote.created_at), "MMM d, yyyy h:mm a")}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quote Activity Timeline */}
          <Card className="border-line shadow-sm bg-surface">
            <CardHeader className="pb-3 border-b border-line bg-paper/50">
              <CardTitle className="text-sm font-semibold text-ink">Activity Log</CardTitle>
            </CardHeader>
            <CardContent className="p-5">
              <div className="relative pl-6 border-l-2 border-line/60 space-y-5">
                <div className="relative">
                  <span className="absolute -left-[29px] top-1.5 h-3 w-3 rounded-full border-2 border-white bg-teal shadow-sm"></span>
                  <p className="text-sm font-medium text-ink">Quote Created</p>
                  <p className="text-xs text-muted-foreground">{format(new Date(quote.created_at), "MMM d, h:mm a")}</p>
                </div>
                {auditEvents?.map((event) => {
                  let color = "bg-muted-foreground";
                  let title = event.action;
                  if (title.startsWith("booking.failed") || title === "cancel.requested" || title === "payment_captured_quote_expired") color = "bg-coral";
                  if (title === "booking.confirmed") color = "bg-mint";
                  if (title === "payment.captured") color = "bg-mint";
                  if (title === "quote.sent") color = "bg-amber";

                  return (
                    <div key={event.id} className="relative animate-in fade-in">
                      <span className={`absolute -left-[29px] top-1.5 h-3 w-3 rounded-full border-2 border-white shadow-sm ${color}`}></span>
                      <p className="text-sm font-medium capitalize text-ink">{event.action.replace(/_/g, " ").replace(/\./g, " ")}</p>
                      <p className="text-xs text-muted-foreground">{format(new Date(event.created_at), "MMM d, h:mm a")}</p>
                      {event.metadata?.reason && (
                        <p className="text-xs text-coral mt-1 bg-coral/5 p-1.5 rounded">Reason: {event.metadata.reason}</p>
                      )}
                      {event.metadata?.supplier_pnr && (
                        <p className="text-xs text-emerald-700 mt-1 font-mono bg-emerald-50 inline-block px-1.5 py-0.5 rounded border border-emerald-100">
                          PNR: {event.metadata.supplier_pnr}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* 4. Admin Controls */}
          {quote.status !== "cancelled" && (
            <div className="pt-4 flex flex-col gap-2">
              <Button variant="ghost" onClick={handleCancelQuote} disabled={isCanceling} className="w-full text-coral hover:text-coral hover:bg-coral/10 justify-start">
                <XCircle className="w-4 h-4 mr-2" /> Cancel Quote / Booking
              </Button>
            </div>
          )}

          {refunds && refunds.length > 0 && (
            <Card className="border-line shadow-sm border-coral/30 bg-coral/5">
              <CardHeader className="pb-3 border-b border-coral/20">
                <CardTitle className="text-sm font-semibold text-coral-dark">Refunds</CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-3">
                {refunds.map((r) => (
                  <div key={r.id} className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-sm capitalize text-ink">{r.status}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {r.reason || "—"} &middot; {format(new Date(r.created_at), "MMM d, h:mm a")}
                      </p>
                    </div>
                    <p className="font-mono font-semibold text-ink">₹{(r.amount / 100).toLocaleString()}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* 5. Mobile Sticky Bottom Action Bar */}
      <div className="lg:hidden fixed bottom-16 left-0 right-0 p-4 bg-paper/90 backdrop-blur-md border-t border-line/60 flex justify-between items-center z-40 shadow-[0_-4px_12px_rgba(0,0,0,0.05)] pb-safe">
        <div>
          <p className="text-xs text-muted-foreground font-medium">Total</p>
          <p className="text-lg font-bold font-mono text-ink leading-tight">
            {quote.items[0]?.money
              ? formatMoney({
                  ...quote.items[0].money,
                  display_amount: quote.items.reduce(
                    (s, i) => s + (i.money?.display_amount ?? i.customer_total / 100),
                    0
                  ),
                })
              : formatPaiseAsMoney(total, { currency: quote.charge_currency || "INR" })}
          </p>
        </div>
        <div className="flex gap-2">
          {(quote.status === "ready" || quote.status === "sent") && (
            <Button onClick={handleGeneratePayment} disabled={isGeneratingPayment} className="gap-2 bg-teal hover:bg-teal-dark shadow-sm">
              <CreditCard className="w-4 h-4" />
              Pay Link
            </Button>
          )}
          {quote.status === "paid" && (
            <Link
              href="/app/bookings"
              className={cn(buttonVariants({ variant: "default" }), "gap-2 bg-mint hover:bg-mint/90 text-white shadow-sm")}
            >
              <FileCheck className="w-4 h-4" />
              Booking
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

function BookingDocuments({ bookingId }: { bookingId: string }) {
  const { data: documents, isLoading } = useGetBookingDocumentsQuery(bookingId);
  const [uploadDocument, { isLoading: isUploading }] = useUploadDocumentMutation();
  const [deleteDocument] = useDeleteDocumentMutation();
  
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("type", "ticket");
    
    try {
      await uploadDocument({ booking_id: bookingId, data: formData }).unwrap();
      alert("Document uploaded successfully.");
    } catch (err) {
      alert("Failed to upload document.");
    }
  };
  
  const handleDelete = async (id: string) => {
    if (confirm("Delete this document?")) {
      try {
        await deleteDocument(id).unwrap();
      } catch (err) {
        alert("Failed to delete document.");
      }
    }
  };
  
  return (
    <Card className="mt-8 border-line shadow-sm bg-surface">
      <CardHeader className="flex flex-row items-center justify-between bg-paper/50 border-b border-line pb-4">
        <CardTitle className="text-sm font-semibold uppercase tracking-wide flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-muted-foreground" /> Booking Documents
        </CardTitle>
        <div className="relative">
          <input 
            type="file" 
            id="doc-upload" 
            className="hidden" 
            onChange={handleUpload} 
            disabled={isUploading}
          />
          <label 
            htmlFor="doc-upload"
            className={`px-4 py-2 bg-paper border border-line text-ink rounded-md text-sm font-medium cursor-pointer shadow-sm hover:bg-sand transition-colors ${isUploading ? 'opacity-50' : ''}`}
          >
            {isUploading ? 'Uploading...' : 'Upload Document'}
          </label>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        {isLoading ? (
          <div className="text-muted-foreground text-sm">Loading documents...</div>
        ) : !documents || documents.length === 0 ? (
          <div className="text-muted-foreground text-sm text-center py-8 bg-sand/30 rounded border border-dashed border-line">
            No documents uploaded yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {documents.map(doc => (
              <div key={doc.id} className="border border-line bg-paper p-4 rounded-md flex items-start justify-between shadow-sm">
                <div className="flex gap-3">
                  <div className="p-2 bg-teal/10 text-teal rounded">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-medium text-sm text-ink truncate w-36" title={doc.filename}>{doc.filename}</p>
                    <Badge variant="outline" className="mt-1 text-[10px] uppercase tracking-wider">{doc.type}</Badge>
                  </div>
                </div>
                <div className="flex gap-1">
                  <a 
                    href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${doc.storage_url}`} 
                    target="_blank" 
                    rel="noreferrer"
                    className="text-muted-foreground hover:text-teal p-1"
                    title="Download"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                  <button onClick={() => handleDelete(doc.id)} className="text-muted-foreground hover:text-coral p-1">
                    <XCircle className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
