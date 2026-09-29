import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SearchQuery } from "@/lib/api/inventoryApi";
import { Building2, Calendar, Users, Loader2 } from "lucide-react";

interface HotelSearchFormProps {
  onSearch: (query: SearchQuery) => void;
  isLoading: boolean;
}

export function HotelSearchForm({ onSearch, isLoading }: HotelSearchFormProps) {
  const [destination, setDestination] = useState("GOI");
  const [checkIn, setCheckIn] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 14);
    return d.toISOString().split("T")[0];
  });
  const [guests, setGuests] = useState(2);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({
      type: "hotel",
      origin: "N/A", // Not used for hotels but required by base schema
      destination,
      departure_date: checkIn,
      passengers: { adults: guests, children: 0, infants: 0 },
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col md:flex-row items-center bg-white rounded-2xl md:rounded-full border border-line p-2 shadow-lg max-w-5xl mx-auto">
      <div className="flex-1 flex flex-col px-6 py-2.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl md:rounded-full transition-colors cursor-pointer group">
        <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <Building2 className="w-3.5 h-3.5" /> Destination
        </label>
        <input 
          value={destination} 
          onChange={(e) => setDestination(e.target.value.toUpperCase())}
          maxLength={3}
          placeholder="GOI"
          required
          className="bg-transparent border-none p-0 focus:ring-0 text-sm font-medium text-ink placeholder:text-muted-foreground uppercase focus-visible:outline-none"
        />
      </div>

      <div className="hidden md:block w-px h-10 bg-line/50 mx-1" />

      <div className="flex-1 flex flex-col px-6 py-2.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl md:rounded-full transition-colors cursor-pointer group">
        <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5" /> Check-In
        </label>
        <input 
          type="date"
          value={checkIn} 
          onChange={(e) => setCheckIn(e.target.value)}
          required
          className="bg-transparent border-none p-0 focus:ring-0 text-sm font-medium text-ink focus-visible:outline-none"
        />
      </div>

      <div className="hidden md:block w-px h-10 bg-line/50 mx-1" />

      <div className="flex-1 flex flex-col px-6 py-2.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl md:rounded-full transition-colors cursor-pointer group">
        <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <Users className="w-3.5 h-3.5" /> Guests
        </label>
        <input 
          type="number"
          min={1}
          max={9}
          value={guests} 
          onChange={(e) => setGuests(parseInt(e.target.value))}
          required
          className="bg-transparent border-none p-0 focus:ring-0 text-sm font-medium text-ink focus-visible:outline-none"
        />
      </div>

      <div className="ml-2 pr-2 md:pr-0 mt-4 md:mt-0 w-full md:w-auto">
        <Button type="submit" disabled={isLoading} className="w-full rounded-full px-8 h-12 bg-teal hover:bg-teal-dark text-white font-medium transition-all shadow-sm hover:shadow-md active:scale-95">
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            "Search Hotels"
          )}
        </Button>
      </div>
    </form>
  );
}
