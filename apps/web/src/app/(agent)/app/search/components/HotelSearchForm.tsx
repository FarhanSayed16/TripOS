import { useState } from "react";
import { Button } from "@/components/ui/button";
import { SearchQuery } from "@/lib/api/inventoryApi";
import { Building2, Calendar, Users, Loader2, Search } from "lucide-react";

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
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Row 1: Destination / Check-In / Guests */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Destination */}
        <div className="group rounded-xl border border-line bg-surface/60 hover:border-teal/40 transition-colors p-4 focus-within:border-teal focus-within:ring-2 focus-within:ring-teal/10">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2 flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5 text-teal" /> Destination
          </label>
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value.toUpperCase())}
            maxLength={3}
            placeholder="GOI"
            required
            className="w-full bg-transparent border-none p-0 focus:ring-0 text-2xl font-bold text-ink placeholder:text-muted-foreground/30 uppercase focus-visible:outline-none tracking-wider"
          />
          <span className="text-xs text-muted-foreground mt-1 block">City or airport code</span>
        </div>

        {/* Check-In */}
        <div className="group rounded-xl border border-line bg-surface/60 hover:border-teal/40 transition-colors p-4 focus-within:border-teal focus-within:ring-2 focus-within:ring-teal/10">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-teal" /> Check-In
          </label>
          <input
            type="date"
            value={checkIn}
            onChange={(e) => setCheckIn(e.target.value)}
            required
            className="w-full bg-transparent border-none p-0 focus:ring-0 text-base font-semibold text-ink focus-visible:outline-none"
          />
        </div>

        {/* Guests */}
        <div className="group rounded-xl border border-line bg-surface/60 hover:border-teal/40 transition-colors p-4 focus-within:border-teal focus-within:ring-2 focus-within:ring-teal/10">
          <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-teal" /> Guests
          </label>
          <input
            type="number"
            min={1}
            max={9}
            value={guests}
            onChange={(e) => setGuests(parseInt(e.target.value))}
            required
            className="w-full bg-transparent border-none p-0 focus:ring-0 text-base font-semibold text-ink focus-visible:outline-none"
          />
        </div>
      </div>

      {/* Row 2: Submit */}
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
            Search Hotels
          </>
        )}
      </Button>
    </form>
  );
}
