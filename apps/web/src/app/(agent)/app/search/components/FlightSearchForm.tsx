import { useState } from "react";
import { Button } from "@/components/ui/button";
import { SearchQuery } from "@/lib/api/inventoryApi";
import { Plane, ArrowLeftRight, Calendar, Users, Tag, Loader2, Search } from "lucide-react";

interface FlightSearchFormProps {
  onSearch: (query: SearchQuery) => void;
  isLoading: boolean;
}

export function FlightSearchForm({ onSearch, isLoading }: FlightSearchFormProps) {
  const [origin, setOrigin] = useState("DEL");
  const [destination, setDestination] = useState("BOM");
  const [departureDate, setDepartureDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    return d.toISOString().split("T")[0];
  });
  const [adults, setAdults] = useState(1);
  const [dealCode, setDealCode] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({
      type: "flight",
      origin,
      destination,
      departure_date: departureDate,
      passengers: { adults, children: 0, infants: 0 },
      ...(dealCode.trim() ? { deal_code: dealCode.trim().toUpperCase() } : {}),
    });
  };

  const swapCities = () => {
    setOrigin(destination);
    setDestination(origin);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Row 1: Origin / Destination */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative">
        {/* Origin */}
        <div className="group rounded-xl border border-line bg-surface/60 hover:border-teal/40 transition-colors p-4 focus-within:border-teal focus-within:ring-2 focus-within:ring-teal/10">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2 flex items-center gap-1.5">
            <Plane className="w-3.5 h-3.5 text-teal" /> From
          </label>
          <input
            value={origin}
            onChange={(e) => setOrigin(e.target.value.toUpperCase())}
            maxLength={3}
            placeholder="DEL"
            required
            className="w-full bg-transparent border-none p-0 focus:ring-0 text-2xl font-bold text-ink placeholder:text-muted-foreground/30 uppercase focus-visible:outline-none tracking-wider"
          />
          <span className="text-xs text-muted-foreground mt-1 block">Airport code</span>
        </div>

        {/* Swap button */}
        <button
          type="button"
          onClick={swapCities}
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10 hidden md:flex h-10 w-10 rounded-full bg-paper border-2 border-line items-center justify-center hover:border-teal hover:bg-teal/5 transition-all shadow-sm"
          aria-label="Swap origin and destination"
        >
          <ArrowLeftRight className="w-4 h-4 text-ink/60" />
        </button>

        {/* Destination */}
        <div className="group rounded-xl border border-line bg-surface/60 hover:border-teal/40 transition-colors p-4 focus-within:border-teal focus-within:ring-2 focus-within:ring-teal/10">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2 flex items-center gap-1.5">
            <Plane className="w-3.5 h-3.5 text-teal" /> To
          </label>
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value.toUpperCase())}
            maxLength={3}
            placeholder="BOM"
            required
            className="w-full bg-transparent border-none p-0 focus:ring-0 text-2xl font-bold text-ink placeholder:text-muted-foreground/30 uppercase focus-visible:outline-none tracking-wider"
          />
          <span className="text-xs text-muted-foreground mt-1 block">Airport code</span>
        </div>
      </div>

      {/* Row 2: Date / Passengers / Deal Code */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Departure */}
        <div className="group rounded-xl border border-line bg-surface/60 hover:border-teal/40 transition-colors p-4 focus-within:border-teal focus-within:ring-2 focus-within:ring-teal/10">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-teal" /> Departure
          </label>
          <input
            type="date"
            value={departureDate}
            onChange={(e) => setDepartureDate(e.target.value)}
            required
            className="w-full bg-transparent border-none p-0 focus:ring-0 text-base font-semibold text-ink focus-visible:outline-none"
          />
        </div>

        {/* Passengers */}
        <div className="group rounded-xl border border-line bg-surface/60 hover:border-teal/40 transition-colors p-4 focus-within:border-teal focus-within:ring-2 focus-within:ring-teal/10">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-teal" /> Passengers
          </label>
          <input
            type="number"
            min={1}
            max={9}
            value={adults}
            onChange={(e) => setAdults(parseInt(e.target.value))}
            required
            className="w-full bg-transparent border-none p-0 focus:ring-0 text-base font-semibold text-ink focus-visible:outline-none"
          />
        </div>

        {/* Deal Code */}
        <div className="group rounded-xl border border-line bg-surface/60 hover:border-teal/40 transition-colors p-4 focus-within:border-teal focus-within:ring-2 focus-within:ring-teal/10">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2 flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-teal" /> Deal Code
          </label>
          <input
            value={dealCode}
            onChange={(e) => setDealCode(e.target.value.toUpperCase())}
            placeholder="Optional"
            maxLength={32}
            className="w-full bg-transparent border-none p-0 focus:ring-0 text-base font-semibold text-ink placeholder:text-muted-foreground/30 uppercase focus-visible:outline-none"
          />
        </div>
      </div>

      {/* Row 3: Submit */}
      <Button
        type="submit"
        disabled={isLoading}
        className="w-full h-13 rounded-xl bg-gradient-to-r from-teal to-teal-dark hover:from-teal-dark hover:to-teal text-white font-semibold text-[15px] transition-all shadow-md hover:shadow-lg hover:-translate-y-[1px] active:scale-[0.99] gap-2.5"
      >
        {isLoading ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <>
            <Search className="w-4.5 h-4.5" />
            Search Flights
          </>
        )}
      </Button>
    </form>
  );
}
