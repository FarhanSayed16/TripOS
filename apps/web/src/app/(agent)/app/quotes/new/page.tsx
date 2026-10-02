"use client";

import { useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useRouter } from "next/navigation";
import { RootState } from "@/lib/store";
import { clearOffers } from "@/lib/quoteSlice";
import { useCreateQuoteMutation, useUpdatePassengersMutation, useMarkQuoteReadyMutation } from "@/lib/api/quotesApi";
import { useGetCustomersQuery } from "@/lib/api/crmApi";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, CheckCircle2, ArrowRight, Plane, Building2, Trash2, Plus, Link as LinkIcon, Save, ChevronRight, Clock, ShoppingCart } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import Link from "next/link";
import { cn } from "cn";

export default function QuoteBuilder() {
  const router = useRouter();
  const dispatch = useDispatch();
  const offers = useSelector((state: RootState) => state.quote.selectedOffers);
  
  const [step, setStep] = useState(1);
  const [customerId, setCustomerId] = useState("");
  const [markups, setMarkups] = useState<Record<string, number>>({});
  const [passengers, setPassengers] = useState([{ first_name: "", last_name: "" }]);
  const [quoteId, setQuoteId] = useState<string | null>(null);

  const { data: customersData } = useGetCustomersQuery({ limit: 50 });
  const [createQuote, { isLoading: isCreating }] = useCreateQuoteMutation();
  const [updatePassengers, { isLoading: isUpdatingPax }] = useUpdatePassengersMutation();
  const [markReady, { isLoading: isMarkingReady, error: readyError }] = useMarkQuoteReadyMutation();

  const handleCreate = async () => {
    if (!customerId) return alert("Select a customer");
    
    try {
      const items = offers.map((o) => ({
        search_request_id: o.search_request_id,
        offer: o,
        agent_markup: (markups[o.id] || 0) * 100, // Convert INR to paise
      }));

      if (items.some((i) => !i.search_request_id)) {
        alert("Missing search context. Please search again and re-select offers.");
        return;
      }
      const q = await createQuote({ customer_id: customerId, items }).unwrap();
      setQuoteId(q.id);
      setStep(2);
      dispatch(clearOffers());
    } catch (err) {
      console.error(err);
      alert("Failed to create quote.");
    }
  };

  const handleUpdatePax = async () => {
    if (!quoteId) return;
    try {
      await updatePassengers({ id: quoteId, passengers }).unwrap();
      setStep(3);
    } catch (err) {
      console.error(err);
      alert("Failed to update passengers.");
    }
  };

  const handleMarkReady = async () => {
    if (!quoteId) return;
    try {
      await markReady(quoteId).unwrap();
      router.push(`/app/quotes/${quoteId}`);
    } catch (err) {
      console.error(err);
      // Handled by readyError in UI
    }
  };

  // Honest pricing: supplier totals only (no invented base/tax split)
  const offerTotal = offers.reduce((acc, o) => acc + (o.total_amount || 0), 0);
  const totalMarkup = Object.values(markups).reduce((acc, val) => acc + (val || 0), 0);
  const grandTotal = offerTotal + totalMarkup;

  if (offers.length === 0 && step === 1) {
    return (
      <div className="text-center py-20 flex flex-col items-center">
        <div className="h-16 w-16 bg-surface border border-line rounded-full flex items-center justify-center mb-4">
          <ShoppingCart className="w-6 h-6 text-muted-foreground" />
        </div>
        <h2 className="text-2xl font-bold text-ink tracking-tight mb-2">Your cart is empty</h2>
        <p className="text-muted-foreground mb-6">Select flights and hotels from the inventory to build a quote.</p>
        <Button onClick={() => router.push("/app/search")} className="bg-teal hover:bg-teal-dark">
          Go Search Inventory
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-20">
      <div className="flex items-center justify-between border-b border-line pb-4">
        <h1 className="page-title text-2xl tracking-tight">Quote Builder</h1>
        <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium uppercase tracking-wider">
          <span className={step >= 1 ? "text-ink font-bold" : ""}>1. Cart</span>
          <ArrowRight className="w-3 h-3" />
          <span className={step >= 2 ? "text-ink font-bold" : ""}>2. Passengers</span>
          <ArrowRight className="w-3 h-3" />
          <span className={step >= 3 ? "text-ink font-bold" : ""}>3. Review</span>
        </div>
      </div>

      {step === 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          {/* Left Column: Itinerary */}
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-ink">Selected Itinerary</h2>
            
            <div className="space-y-4">
              {offers.map(o => (
                <Card key={o.id} className="relative overflow-hidden border-line shadow-sm bg-paper group">
                  <div className="absolute top-0 left-0 w-1 h-full bg-teal" />
                  <CardContent className="p-5 pl-6">
                    <div className="flex justify-between items-start mb-4">
                      <h4 className="font-semibold text-ink text-sm flex items-center gap-2">
                        {o.type === 'flight' ? <Plane className="w-4 h-4 text-teal"/> : <Building2 className="w-4 h-4 text-teal"/>}
                        {o.title}
                      </h4>
                      <button 
                        onClick={() => {
                          // Note: Need a removeOffer action in quoteSlice if we want this fully functional
                          alert("Remove functionality to be implemented in Redux");
                        }} 
                        className="text-xs text-muted-foreground hover:text-coral flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Trash2 className="w-3.5 h-3.5" /> Remove
                      </button>
                    </div>

                    {/* Flight Segments matching Phase 4 */}
                    {o.segments && o.segments.length > 0 ? (
                      <div className="relative pl-4 border-l-2 border-line/60 space-y-4 ml-1">
                        {o.segments.map((seg, i) => (
                          <div key={i} className="relative">
                            <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-surface border-2 border-teal" />
                            <div className="text-sm font-medium text-ink">
                              {seg.origin} <ChevronRight className="inline w-3 h-3 text-muted-foreground" /> {seg.destination}
                            </div>
                            <div className="text-xs text-muted-foreground mt-0.5">
                              {seg.flight_number} &middot; {seg.marketing_carrier} {seg.operating_carrier !== seg.marketing_carrier ? `(Op ${seg.operating_carrier})` : ""}
                            </div>
                            {seg.departure_at && (
                              <div className="text-xs text-ink/70 mt-0.5 flex items-center gap-1">
                                <Clock className="w-3 h-3" /> {new Date(seg.departure_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </div>
                            )}
                          </div>
                        ))}
                        <div className="absolute -left-[21px] -bottom-1 w-2.5 h-2.5 rounded-full bg-surface border-2 border-teal" />
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground">{o.description}</div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Add More Actions */}
            <div className="flex gap-3 pt-4">
              <Link
                href="/app/search"
                className={cn(
                  buttonVariants({ variant: "outline" }),
                  "border-dashed border-2 text-teal hover:text-teal-dark hover:bg-teal/5 bg-transparent h-12 px-6"
                )}
              >
                <Plus className="w-4 h-4 mr-2" /> Add Flight
              </Link>
              <Link
                href="/app/search"
                className={cn(
                  buttonVariants({ variant: "outline" }),
                  "border-dashed border-2 text-teal hover:text-teal-dark hover:bg-teal/5 bg-transparent h-12 px-6"
                )}
              >
                <Plus className="w-4 h-4 mr-2" /> Add Hotel
              </Link>
            </div>
          </div>

          {/* Right Column: Customer + Pricing */}
          <div className="space-y-6">
            
            {/* Customer Block Floating Card */}
            <Card className="border-line shadow-sm bg-surface">
              <CardHeader className="pb-3 border-b border-line bg-paper/50">
                <CardTitle className="text-sm font-semibold text-ink flex items-center justify-between">
                  Customer Details
                  <span className="text-[10px] font-normal text-coral bg-coral/10 px-2 py-0.5 rounded-full border border-coral/20">Required</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-4">
                <div>
                  <Select value={customerId} onValueChange={(val) => setCustomerId(val as string)}>
                    <SelectTrigger className="w-full bg-paper">
                      <SelectValue placeholder="Search or select customer..." />
                    </SelectTrigger>
                    <SelectContent>
                      {customersData?.items.map((c: any) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.first_name} {c.last_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {customerId && customersData && (
                  <div className="text-xs text-muted-foreground bg-paper p-3 rounded-md border border-line flex flex-col gap-1.5 shadow-sm animate-in fade-in">
                    {(() => {
                      const c = customersData.items.find((x: any) => x.id === customerId);
                      return (
                        <>
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-ink">{c?.first_name} {c?.last_name}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Phone</span>
                            <span className="font-mono text-ink">{c?.phone_e164}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Email</span>
                            <span className="text-ink">{c?.email || 'N/A'}</span>
                          </div>
                        </>
                      );
                    })()}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Price Builder */}
            <Card className="border-line shadow-sm bg-surface">
              <CardHeader className="pb-3 border-b border-line bg-paper/50">
                <CardTitle className="text-sm font-semibold text-ink">Price Builder</CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Offer total</span>
                  <span className="font-mono text-ink">₹{offerTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <p className="text-[11px] text-muted-foreground -mt-2">
                  Supplier fare as returned — tax breakdown not available separately.
                </p>
                
                <div className="pt-4 border-t border-line space-y-3">
                  <p className="text-xs font-semibold text-ink uppercase tracking-wider mb-2">Agent Markup</p>
                  {offers.map(o => (
                     <div key={o.id} className="flex items-center justify-between">
                       <span className="text-xs text-muted-foreground truncate max-w-[120px]">{o.title}</span>
                       <div className="flex items-center gap-2">
                         <span className="text-xs font-mono text-muted-foreground">₹</span>
                         <Input 
                            type="number" 
                            value={markups[o.id] || 0}
                            onChange={(e) => setMarkups({...markups, [o.id]: Number(e.target.value)})}
                            className="w-24 h-8 text-xs text-right font-mono bg-paper border-teal/30 focus-visible:ring-teal"
                         />
                       </div>
                     </div>
                  ))}
                </div>
                
                <div className="pt-4 border-t border-line flex justify-between items-end mt-2">
                  <span className="font-semibold text-ink text-sm">Grand Total</span>
                  <span className="text-2xl font-bold text-teal font-mono tracking-tight">₹{grandTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex flex-col gap-3 pt-2">
              <Button onClick={handleCreate} disabled={isCreating || !customerId} className="w-full h-12 bg-teal hover:bg-teal-dark shadow-md" size="lg">
                {isCreating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <LinkIcon className="w-4 h-4 mr-2" />}
                Generate Payment Link
              </Button>
              <Button variant="outline" onClick={handleCreate} disabled={isCreating || !customerId} className="w-full h-11 bg-paper hover:bg-sand">
                <Save className="w-4 h-4 mr-2 text-muted-foreground" /> Save Quote
              </Button>
            </div>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-6 max-w-2xl mx-auto animate-in slide-in-from-right-8 duration-300">
          <Card className="border-line shadow-sm">
            <CardHeader className="border-b border-line bg-surface/50">
              <CardTitle className="text-lg font-semibold flex items-center justify-between">
                Passenger Details 
                <span className="text-xs bg-coral/10 text-coral border border-coral/20 px-2 py-0.5 rounded-full font-medium">Required for Booking</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              <p className="text-sm text-muted-foreground mb-4">Please provide full names exactly as they appear on the government ID to clear the Pax Gate.</p>
              
              <div className="space-y-6">
                {passengers.map((p, i) => (
                  <div key={i} className="grid grid-cols-2 gap-4 bg-sand/30 p-4 rounded-lg border border-line">
                    <div className="col-span-2">
                      <h4 className="text-xs font-semibold text-ink uppercase tracking-wider mb-3">Passenger {i + 1}</h4>
                    </div>
                    <div>
                      <label className="text-xs font-medium mb-1.5 block text-muted-foreground">First Name</label>
                      <Input 
                        value={p.first_name}
                        onChange={(e) => {
                          const newP = [...passengers];
                          newP[i].first_name = e.target.value;
                          setPassengers(newP);
                        }}
                        required
                        className="bg-paper"
                        placeholder="e.g. John"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium mb-1.5 block text-muted-foreground">Last Name</label>
                      <Input 
                        value={p.last_name}
                        onChange={(e) => {
                          const newP = [...passengers];
                          newP[i].last_name = e.target.value;
                          setPassengers(newP);
                        }}
                        required
                        className="bg-paper"
                        placeholder="e.g. Doe"
                      />
                    </div>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full border-dashed" onClick={() => setPassengers([...passengers, { first_name: "", last_name: "" }])}>
                <Plus className="w-4 h-4 mr-2" /> Add Passenger
              </Button>
            </CardContent>
          </Card>
          
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={() => setStep(1)}>Back to Cart</Button>
            <Button onClick={handleUpdatePax} disabled={isUpdatingPax} className="px-8 bg-teal hover:bg-teal-dark">
              {isUpdatingPax ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save Passengers"}
            </Button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-6 text-center py-16 animate-in zoom-in-95 duration-300">
          <div className="inline-flex h-20 w-20 items-center justify-center rounded-full bg-mint/10 mb-6 border border-mint/20">
            <CheckCircle2 className="w-10 h-10 text-mint" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-ink">Quote Assembled</h2>
          <p className="text-muted-foreground max-w-md mx-auto mt-2">
            The quote has been created and passenger details have been recorded. 
            Marking it as "Ready" will finalize the quote and generate a payment link.
          </p>

          {readyError && (
            <div className="bg-coral/10 text-coral p-4 rounded-xl max-w-md mx-auto mt-6 border border-coral/20 text-left flex items-start gap-3">
              <div className="mt-0.5">
                <CheckCircle2 className="w-5 h-5 opacity-0" /> {/* Placeholder for alignment */}
              </div>
              <div>
                <p className="font-semibold text-sm mb-1">Validation Failed</p>
                <p className="text-sm opacity-90">{(readyError as any)?.data?.detail || "The Pax Gate blocked this quote from becoming ready."}</p>
              </div>
            </div>
          )}

          <div className="mt-10 flex justify-center gap-4">
            <Button variant="outline" size="lg" onClick={() => setStep(2)}>Back to Pax</Button>
            <Button size="lg" onClick={handleMarkReady} disabled={isMarkingReady} className="px-8 bg-teal hover:bg-teal-dark shadow-md">
              {isMarkingReady ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : "Mark Quote Ready"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
