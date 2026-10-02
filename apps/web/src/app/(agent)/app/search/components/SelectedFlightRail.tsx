import { NormalizedOffer } from "@/lib/api/inventoryApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { Plane, ShoppingCart, Clock, Briefcase, Info, ChevronRight, Check } from "lucide-react";
import Link from "next/link";
import { cn } from "cn";

export function SelectedFlightRail({ offers }: { offers: NormalizedOffer[] }) {
  if (!offers || offers.length === 0) {
    return (
      <Card className="bg-paper border-line sticky top-24">
        <CardContent className="p-6 text-center text-muted-foreground flex flex-col items-center justify-center min-h-[300px]">
          <Plane className="w-10 h-10 mb-4 opacity-20" />
          <p className="text-sm">Select a flight or hotel to build your quote.</p>
        </CardContent>
      </Card>
    );
  }

  const selected = offers[offers.length - 1];

  return (
    <div className="sticky top-24 space-y-4 animate-in fade-in slide-in-from-right-8 duration-300">
      <Card className="border-line shadow-sm overflow-hidden bg-paper">
        <div className="bg-gradient-to-r from-teal to-teal-dark px-4 py-3 text-white flex items-center justify-between">
          <span className="font-semibold text-sm">Selected Option</span>
          <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full backdrop-blur-md">
            {offers.length} item{offers.length > 1 ? "s" : ""}
          </span>
        </div>
        
        <CardContent className="p-5">
          {/* Timeline Itinerary */}
          <div className="mb-6">
            <h4 className="font-semibold text-ink text-sm mb-3 flex items-center gap-2">
              <Plane className="w-4 h-4 text-teal" />
              {selected.title}
            </h4>
            
            {selected.segments && selected.segments.length > 0 ? (
              <div className="relative pl-4 border-l-2 border-line/60 space-y-4 ml-1">
                {selected.segments.map((seg, i) => (
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
              <div className="text-sm text-muted-foreground">{selected.description}</div>
            )}
          </div>

          {/* Fare — honest total only (no invented base/tax split) */}
          <div className="bg-sand/40 rounded-lg p-3 mb-5 border border-line/50">
            <div className="flex justify-between items-center font-semibold">
              <span className="text-ink">Offer total</span>
              <span className="text-lg font-mono text-ink">
                {selected.currency} {selected.total_amount.toLocaleString()}
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground mt-2">
              Includes taxes as returned by supplier. Separate base/tax lines appear when available.
            </p>
          </div>

          {/* Baggage */}
          <div className="space-y-2 mb-6">
            <div className="flex items-start gap-2 text-xs text-muted-foreground">
              <Briefcase className="w-3.5 h-3.5 text-teal shrink-0 mt-0.5" />
              <span>
                {selected.baggage?.checked_kg ? `${selected.baggage.checked_kg}kg Checked` : "No checked bags"} &middot;{" "}
                {selected.baggage?.cabin_kg ? `${selected.baggage.cabin_kg}kg Cabin` : "No cabin bag"}
              </span>
            </div>
            {selected.fare_family ? (
              <div className="flex items-start gap-2 text-xs text-muted-foreground">
                <Check className="w-3.5 h-3.5 text-teal shrink-0 mt-0.5" />
                <span>Fare family: {selected.fare_family}</span>
              </div>
            ) : null}
            {selected.inventory_mode ? (
              <div className="flex items-start gap-2 text-xs text-muted-foreground">
                <Info className="w-3.5 h-3.5 text-teal shrink-0 mt-0.5" />
                <span className="capitalize">Inventory: {selected.inventory_mode}</span>
              </div>
            ) : null}
          </div>

          <Link
            href="/app/quotes/new"
            className={cn(
              buttonVariants({ variant: "gradient", size: "lg" }),
              "w-full justify-between group h-12 shadow-md"
            )}
          >
            <span className="flex items-center gap-2">
              <ShoppingCart className="w-4 h-4" />
              Continue to quote
            </span>
            <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
