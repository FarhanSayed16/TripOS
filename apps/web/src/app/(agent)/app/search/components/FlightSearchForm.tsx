import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SearchQuery } from "@/lib/api/inventoryApi";
import { Plane, Calendar, Users, Loader2 } from "lucide-react";

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

  return (
    <form onSubmit={handleSubmit} className="flex flex-col md:flex-row items-center bg-paper rounded-2xl md:rounded-full border border-line p-2 shadow-lg max-w-5xl mx-auto">
      <div className="flex-1 flex flex-col px-6 py-2.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl md:rounded-full transition-colors cursor-pointer group">
        <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <Plane className="w-3.5 h-3.5" /> Origin
        </label>
        <input 
          value={origin} 
          onChange={(e) => setOrigin(e.target.value.toUpperCase())}
          maxLength={3}
          placeholder="DEL"
          required
          className="bg-transparent border-none p-0 focus:ring-0 text-sm font-medium text-ink placeholder:text-muted-foreground uppercase focus-visible:outline-none"
        />
      </div>
      
      <div className="hidden md:block w-px h-10 bg-line/50 mx-1" />
      
      <div className="flex-1 flex flex-col px-6 py-2.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl md:rounded-full transition-colors cursor-pointer group">
        <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <Plane className="w-3.5 h-3.5" /> Destination
        </label>
        <input 
          value={destination} 
          onChange={(e) => setDestination(e.target.value.toUpperCase())}
          maxLength={3}
          placeholder="BOM"
          required
          className="bg-transparent border-none p-0 focus:ring-0 text-sm font-medium text-ink placeholder:text-muted-foreground uppercase focus-visible:outline-none"
        />
      </div>

      <div className="hidden md:block w-px h-10 bg-line/50 mx-1" />

      <div className="flex-1 flex flex-col px-6 py-2.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl md:rounded-full transition-colors cursor-pointer group">
        <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5" /> Departure
        </label>
        <input 
          type="date"
          value={departureDate} 
          onChange={(e) => setDepartureDate(e.target.value)}
          required
          className="bg-transparent border-none p-0 focus:ring-0 text-sm font-medium text-ink focus-visible:outline-none"
        />
      </div>

      <div className="hidden md:block w-px h-10 bg-line/50 mx-1" />

      <div className="flex-1 flex flex-col px-6 py-2.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl md:rounded-full transition-colors cursor-pointer group">
        <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <Users className="w-3.5 h-3.5" /> Passengers
        </label>
        <input 
          type="number"
          min={1}
          max={9}
          value={adults} 
          onChange={(e) => setAdults(parseInt(e.target.value))}
          required
          className="bg-transparent border-none p-0 focus:ring-0 text-sm font-medium text-ink focus-visible:outline-none"
        />
      </div>

      <div className="hidden md:block w-px h-10 bg-line/50 mx-1" />

      <div className="flex-1 flex flex-col px-6 py-2.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl md:rounded-full transition-colors cursor-pointer group">
        <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
          Deal code
        </label>
        <input
          value={dealCode}
          onChange={(e) => setDealCode(e.target.value.toUpperCase())}
          placeholder="XYZ123"
          maxLength={32}
          className="bg-transparent border-none p-0 focus:ring-0 text-sm font-medium text-ink placeholder:text-muted-foreground uppercase focus-visible:outline-none"
        />
      </div>

      <div className="ml-2 pr-2 md:pr-0 mt-4 md:mt-0 w-full md:w-auto">
        <Button type="submit" disabled={isLoading} className="w-full rounded-full px-8 h-12 bg-teal hover:bg-teal-dark text-white font-medium transition-all shadow-sm hover:shadow-md active:scale-95">
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            "Search Flights"
          )}
        </Button>
      </div>
    </form>
  );
}
