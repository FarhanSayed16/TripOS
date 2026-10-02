"use client";

import { useMemo, useState } from "react";
import { NormalizedOffer } from "@/lib/api/inventoryApi";
import { OfferCard } from "./OfferCard";
import { Button } from "@/components/ui/button";
import { useI18nOptional } from "@/lib/i18n";
import { ArrowUpDown, Filter, RotateCcw, Plane, ChevronDown } from "lucide-react";

interface OfferResultsProps {
  offers: NormalizedOffer[];
  searchRequestId: string;
  cacheHit?: boolean;
  cacheAgeSeconds?: number | null;
  supplierCounts?: Record<string, number> | null;
  airlineFacets?: { airline: string; count: number }[] | null;
  aggregation?: {
    before_dedupe?: number;
    after_dedupe?: number;
    deduped_away?: number;
    sort?: string;
  } | null;
  fxNote?: string | null;
  lastQuery?: any;
  onEditSearch?: () => void;
}

type SortKey = "recommended" | "price" | "duration" | "stops";

function formatCacheAge(seconds: number): string {
  if (seconds < 60) return `${seconds}s ago`;
  return `${Math.max(1, Math.round(seconds / 60))}m ago`;
}

function sortOffers(list: NormalizedOffer[], sort: SortKey): NormalizedOffer[] {
  const copy = [...list];
  if (sort === "price") {
    return copy.sort((a, b) => a.total_amount - b.total_amount);
  }
  if (sort === "duration") {
    return copy.sort(
      (a, b) =>
        (a.duration_minutes ?? 99999) - (b.duration_minutes ?? 99999) ||
        a.total_amount - b.total_amount
    );
  }
  if (sort === "stops") {
    return copy.sort(
      (a, b) =>
        (a.stops ?? 99) - (b.stops ?? 99) || a.total_amount - b.total_amount
    );
  }
  // recommended heuristic (mirrors API)
  return copy.sort((a, b) => {
    const score = (o: NormalizedOffer) =>
      o.total_amount + (o.duration_minutes ?? 9999) * 2 + (o.stops ?? 9) * 500;
    return score(a) - score(b);
  });
}

export function OfferResults({
  offers,
  searchRequestId,
  cacheHit = false,
  cacheAgeSeconds = null,
  supplierCounts = null,
  airlineFacets = null,
  aggregation = null,
  fxNote = null,
  lastQuery = null,
  onEditSearch,
}: OfferResultsProps) {
  const { t } = useI18nOptional();
  const [visibleCount, setVisibleCount] = useState(20);
  const [sort, setSort] = useState<SortKey>("recommended");
  const [maxStops, setMaxStops] = useState<string>("any");
  const [airline, setAirline] = useState<string>("any");
  const [maxPrice, setMaxPrice] = useState<string>("");

  const filteredSorted = useMemo(() => {
    let list = [...offers];
    if (maxStops !== "any") {
      const n = Number(maxStops);
      list = list.filter((o) => (o.stops ?? 0) <= n);
    }
    if (airline !== "any") {
      const a = airline.toUpperCase();
      list = list.filter(
        (o) =>
          (o.airline_code || "").toUpperCase() === a ||
          (o.airline_name || "").toUpperCase().includes(a)
      );
    }
    if (maxPrice.trim()) {
      const p = Number(maxPrice);
      if (!Number.isNaN(p)) {
        list = list.filter((o) => o.total_amount <= p);
      }
    }
    return sortOffers(list, sort);
  }, [offers, sort, maxStops, airline, maxPrice]);

  if (!offers || offers.length === 0) {
    return null;
  }

  const visibleOffers = filteredSorted.slice(0, visibleCount);
  const hasMore = visibleCount < filteredSorted.length;
  const airlines =
    airlineFacets?.map((f) => f.airline) ||
    Array.from(
      new Set(
        offers
          .map((o) => o.airline_code || o.airline_name)
          .filter(Boolean) as string[]
      )
    );

  const hasActiveFilters = maxStops !== "any" || airline !== "any" || maxPrice.trim() !== "";

  return (
    <div className="space-y-5">
      
      {/* Search Summary Bar */}
      {lastQuery && (
        <div className="flex items-center justify-between bg-surface rounded-xl border border-line p-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-teal/10 flex items-center justify-center">
              <Plane className="w-4.5 h-4.5 text-teal" />
            </div>
            <div>
              <div className="flex items-center gap-1.5 text-ink font-semibold text-[15px]">
                <span>{lastQuery.origin}</span>
                <span className="text-muted-foreground">→</span>
                <span>{lastQuery.destination}</span>
              </div>
              <div className="text-xs text-muted-foreground">
                {new Date(lastQuery.departure_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
                {" · "}
                {lastQuery.passengers?.adults || 1} passenger{(lastQuery.passengers?.adults || 1) > 1 ? "s" : ""}
              </div>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1.5"
            type="button"
            onClick={() => {
              onEditSearch?.();
              document.getElementById("inventory-search-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
          >
            Edit search
          </Button>
        </div>
      )}

      {/* Results Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold text-ink">{filteredSorted.length} {t("search.results")}</h2>
          {cacheHit && (
            <span
              className="text-[11px] font-medium text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full"
              title="Browse prices from shopping cache — revalidated before payment"
            >
              Cached{typeof cacheAgeSeconds === "number" ? ` · ${formatCacheAge(cacheAgeSeconds)}` : ""}
            </span>
          )}
        </div>
        <span className="text-xs text-muted-foreground">
          {filteredSorted.length !== offers.length
            ? `${filteredSorted.length} of ${offers.length}`
            : `${offers.length} results`}
        </span>
      </div>

      {fxNote && (
        <p className="text-xs text-muted-foreground border border-line rounded-lg bg-paper px-3 py-2">
          {fxNote}
        </p>
      )}

      {/* Sort & Filter Bar */}
      <div className="flex flex-wrap gap-3 items-center p-3 rounded-xl border border-line bg-paper">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground mr-1">
          <Filter className="w-3.5 h-3.5" />
          Filters
        </div>
        
        <div className="relative">
          <select
            className="appearance-none border border-line rounded-lg px-3 pr-7 py-1.5 text-sm bg-surface text-ink font-medium focus:border-teal focus:ring-1 focus:ring-teal/20 focus-visible:outline-none cursor-pointer"
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
          >
            <option value="recommended">Recommended</option>
            <option value="price">Cheapest</option>
            <option value="duration">Fastest</option>
            <option value="stops">Fewest stops</option>
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
        </div>

        <div className="relative">
          <select
            className="appearance-none border border-line rounded-lg px-3 pr-7 py-1.5 text-sm bg-surface text-ink font-medium focus:border-teal focus:ring-1 focus:ring-teal/20 focus-visible:outline-none cursor-pointer"
            value={maxStops}
            onChange={(e) => setMaxStops(e.target.value)}
          >
            <option value="any">Any stops</option>
            <option value="0">Non-stop only</option>
            <option value="1">≤ 1 stop</option>
            <option value="2">≤ 2 stops</option>
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
        </div>

        {airlines.length > 0 && (
          <div className="relative">
            <select
              className="appearance-none border border-line rounded-lg px-3 pr-7 py-1.5 text-sm bg-surface text-ink font-medium min-w-[110px] focus:border-teal focus:ring-1 focus:ring-teal/20 focus-visible:outline-none cursor-pointer"
              value={airline}
              onChange={(e) => setAirline(e.target.value)}
            >
              <option value="any">All airlines</option>
              {airlines.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
          </div>
        )}

        <input
          type="number"
          placeholder="Max price"
          className="border border-line rounded-lg px-3 py-1.5 text-sm bg-surface text-ink font-medium w-28 placeholder:text-muted-foreground/40 focus:border-teal focus:ring-1 focus:ring-teal/20 focus-visible:outline-none"
          value={maxPrice}
          onChange={(e) => setMaxPrice(e.target.value)}
        />

        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            className="text-xs gap-1 text-coral hover:text-coral h-7"
            onClick={() => {
              setMaxStops("any");
              setAirline("any");
              setMaxPrice("");
              setSort("recommended");
            }}
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </Button>
        )}
      </div>

      {/* Fare Family Comparison Rows + Offer Cards */}
      <div className="space-y-3">
        {visibleOffers.map((offer, i) => (
          <div
            key={offer.id}
            className="animate-in fade-in slide-in-from-bottom-3 duration-400 fill-mode-both"
            style={{ animationDelay: `${Math.min(i * 40, 400)}ms` }}
          >
            {/* Fare family comparison */}
            {offer.family_group_id &&
              offer.fare_family &&
              visibleOffers.find((o) => o.family_group_id === offer.family_group_id)
                ?.id === offer.id &&
              visibleOffers.filter((o) => o.family_group_id === offer.family_group_id)
                .length > 1 && (
                <div className="flex flex-wrap gap-2 text-xs px-1 mb-2">
                  <span className="text-muted-foreground self-center font-medium">Compare fares:</span>
                  {visibleOffers
                    .filter((o) => o.family_group_id === offer.family_group_id)
                    .sort((a, b) => a.total_amount - b.total_amount)
                    .map((o) => (
                      <span
                        key={o.id}
                        className="px-2.5 py-1 rounded-lg border border-line bg-paper font-semibold text-ink"
                      >
                        {o.fare_family} · <span className="font-mono">{o.currency} {o.total_amount.toLocaleString()}</span>
                      </span>
                    ))}
                </div>
              )}
            <OfferCard offer={offer} searchRequestId={searchRequestId} />
          </div>
        ))}
        {visibleOffers.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <Filter className="w-8 h-8 mx-auto mb-3 opacity-30" />
            <p className="text-sm font-medium">No offers match your filters</p>
            <p className="text-xs mt-1">Try adjusting your criteria or reset all filters.</p>
          </div>
        )}
      </div>

      {hasMore && (
        <div className="flex justify-center pt-2">
          <Button
            variant="outline"
            onClick={() => setVisibleCount((prev) => prev + 20)}
            className="w-full md:w-auto gap-2"
          >
            Load more results
            <span className="text-xs text-muted-foreground">
              ({filteredSorted.length - visibleCount} remaining)
            </span>
          </Button>
        </div>
      )}
    </div>
  );
}
