"use client";

import { useMemo, useState } from "react";
import { NormalizedOffer } from "@/lib/api/inventoryApi";
import { OfferCard } from "./OfferCard";
import { Button } from "@/components/ui/button";
import { useI18nOptional } from "@/lib/i18n";

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
}

type SortKey = "recommended" | "price" | "duration" | "stops";

function formatCacheAge(seconds: number): string {
  if (seconds < 60) return `updated ${seconds}s ago`;
  return `updated ${Math.max(1, Math.round(seconds / 60))}m ago`;
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

  return (
    <div className="space-y-6">
      
      {lastQuery && (
        <div className="flex items-center justify-between bg-paper p-4 rounded-xl border border-line shadow-sm">
          <div className="flex items-center gap-2 text-ink">
            <span className="font-semibold">{lastQuery.origin} &rarr; {lastQuery.destination}</span>
            <span className="text-muted-foreground">&middot;</span>
            <span className="text-sm">{new Date(lastQuery.departure_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
            <span className="text-muted-foreground">&middot;</span>
            <span className="text-sm">{lastQuery.passengers?.adults || 1} pax</span>
          </div>
          <Button variant="outline" size="sm" className="h-8">
            Edit search
          </Button>
        </div>
      )}

      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="text-xl font-bold text-ink">{t("search.results")}</h2>
          {cacheHit && (
            <span
              className="text-xs font-medium text-amber-800 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-md"
              title="Browse prices from shopping cache — revalidated before payment"
            >
              {t("search.indicative")}
              {typeof cacheAgeSeconds === "number"
                ? ` · ${formatCacheAge(cacheAgeSeconds)}`
                : ""}
            </span>
          )}
          {aggregation?.deduped_away ? (
            <span className="text-xs text-gray-500">
              Deduped {aggregation.deduped_away} duplicate
              {aggregation.deduped_away === 1 ? "" : "s"}
            </span>
          ) : null}
        </div>
        <p className="text-sm text-gray-500">
          Showing {visibleOffers.length} of {filteredSorted.length}
          {filteredSorted.length !== offers.length
            ? ` (filtered from ${offers.length})`
            : ""}
        </p>
      </div>

      {fxNote && (
        <p className="text-xs text-gray-500 border border-line rounded-md bg-white px-3 py-2">
          {fxNote}
        </p>
      )}

      {supplierCounts && Object.keys(supplierCounts).length > 0 && (
        <div className="flex flex-wrap gap-2 text-xs">
          {Object.entries(supplierCounts).map(([code, count]) => (
            <span
              key={code}
              className="px-2 py-1 rounded border border-line bg-white text-gray-600 font-mono"
            >
              {code}: {count}
            </span>
          ))}
        </div>
      )}

      {/* Client-side sort/filter — no re-search */}
      <div className="flex flex-wrap gap-3 items-end p-3 rounded-lg border border-line bg-sand/20">
        <label className="text-xs text-gray-600 flex flex-col gap-1">
          Sort
          <select
            className="border border-line rounded-md px-2 py-1.5 text-sm bg-white"
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
          >
            <option value="recommended">Recommended</option>
            <option value="price">Price</option>
            <option value="duration">Duration</option>
            <option value="stops">Stops</option>
          </select>
        </label>
        <label className="text-xs text-gray-600 flex flex-col gap-1">
          Stops
          <select
            className="border border-line rounded-md px-2 py-1.5 text-sm bg-white"
            value={maxStops}
            onChange={(e) => setMaxStops(e.target.value)}
          >
            <option value="any">Any</option>
            <option value="0">Non-stop</option>
            <option value="1">≤ 1 stop</option>
            <option value="2">≤ 2 stops</option>
          </select>
        </label>
        <label className="text-xs text-gray-600 flex flex-col gap-1">
          Airline
          <select
            className="border border-line rounded-md px-2 py-1.5 text-sm bg-white min-w-[120px]"
            value={airline}
            onChange={(e) => setAirline(e.target.value)}
          >
            <option value="any">Any</option>
            {airlines.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-gray-600 flex flex-col gap-1">
          Max price
          <input
            type="number"
            placeholder="e.g. 8000"
            className="border border-line rounded-md px-2 py-1.5 text-sm bg-white w-28"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
          />
        </label>
        {(maxStops !== "any" || airline !== "any" || maxPrice) && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setMaxStops("any");
              setAirline("any");
              setMaxPrice("");
              setSort("recommended");
            }}
          >
            Reset
          </Button>
        )}
      </div>

      <div className="space-y-4">
        {visibleOffers.map((offer, i) => (
          <div
            key={offer.id}
            className="animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-both space-y-2"
            style={{ animationDelay: `${Math.min(i * 50, 500)}ms` }}
          >
            {offer.family_group_id &&
              offer.fare_family &&
              visibleOffers.find((o) => o.family_group_id === offer.family_group_id)
                ?.id === offer.id &&
              visibleOffers.filter((o) => o.family_group_id === offer.family_group_id)
                .length > 1 && (
                <div className="flex flex-wrap gap-2 text-xs px-1">
                  <span className="text-gray-500 self-center">Compare fares:</span>
                  {visibleOffers
                    .filter((o) => o.family_group_id === offer.family_group_id)
                    .sort((a, b) => a.total_amount - b.total_amount)
                    .map((o) => (
                      <span
                        key={o.id}
                        className="px-2 py-1 rounded border border-line bg-white font-medium"
                      >
                        {o.fare_family} · {o.currency}{" "}
                        {o.total_amount.toLocaleString()}
                      </span>
                    ))}
                </div>
              )}
            <OfferCard offer={offer} searchRequestId={searchRequestId} />
          </div>
        ))}
        {visibleOffers.length === 0 && (
          <p className="text-sm text-gray-500 py-6 text-center">
            No offers match these filters. Reset filters to see all results.
          </p>
        )}
      </div>

      {hasMore && (
        <div className="flex justify-center pt-4">
          <Button
            variant="outline"
            onClick={() => setVisibleCount((prev) => prev + 20)}
            className="w-full md:w-auto"
          >
            Load More Results
          </Button>
        </div>
      )}
    </div>
  );
}
