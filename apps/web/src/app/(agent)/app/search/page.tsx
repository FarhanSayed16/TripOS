"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plane, Building2, AlertCircle, ShoppingCart } from "lucide-react";
import { useSearchFlightsMutation, useSearchHotelsMutation, NormalizedOffer } from "@/lib/api/inventoryApi";
import { FlightSearchForm } from "./components/FlightSearchForm";
import { HotelSearchForm } from "./components/HotelSearchForm";
import { OfferResults } from "./components/OfferResults";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "@/lib/store";
import { setLastSearchRequestId } from "@/lib/quoteSlice";
import { SelectedFlightRail } from "./components/SelectedFlightRail";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function SearchPage() {
  const dispatch = useDispatch();
  const [searchFlights, { isLoading: isFlightsLoading, error: flightError }] = useSearchFlightsMutation();
  const [searchHotels, { isLoading: isHotelsLoading, error: hotelError }] = useSearchHotelsMutation();
  const selectedOffers = useSelector((state: RootState) => state.quote.selectedOffers);

  const [offers, setOffers] = useState<NormalizedOffer[]>([]);
  const [searchRequestId, setSearchRequestId] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState<any>(null);
  const [cacheHit, setCacheHit] = useState(false);
  const [cacheAgeSeconds, setCacheAgeSeconds] = useState<number | null>(null);
  const [supplierCounts, setSupplierCounts] = useState<Record<string, number> | null>(null);
  const [airlineFacets, setAirlineFacets] = useState<
    { airline: string; count: number }[] | null
  >(null);
  const [aggregation, setAggregation] = useState<{
    before_dedupe?: number;
    after_dedupe?: number;
    deduped_away?: number;
    sort?: string;
  } | null>(null);
  const [fxNote, setFxNote] = useState<string | null>(null);

  const applyResult = (result: {
    offers: NormalizedOffer[];
    search_request_id: string;
    cache_hit?: boolean;
    cache_age_seconds?: number | null;
    supplier_counts?: Record<string, number>;
    airline_facets?: { airline: string; count: number }[];
    aggregation?: {
      before_dedupe?: number;
      after_dedupe?: number;
      deduped_away?: number;
      sort?: string;
    };
    charge_currency?: string;
    display_currency?: string;
    fx_rate?: number | null;
    fx_as_of?: string | null;
  }) => {
    setOffers(result.offers);
    setSearchRequestId(result.search_request_id);
    setCacheHit(Boolean(result.cache_hit));
    setCacheAgeSeconds(
      typeof result.cache_age_seconds === "number" ? result.cache_age_seconds : null
    );
    setSupplierCounts(result.supplier_counts || null);
    setAirlineFacets(result.airline_facets || null);
    setAggregation(result.aggregation || null);
    const charge = (result.charge_currency || "INR").toUpperCase();
    const display = (result.display_currency || charge).toUpperCase();
    if (charge !== display) {
      const when = result.fx_as_of
        ? new Date(result.fx_as_of).toLocaleString()
        : "now";
      setFxNote(
        `Showing ${display} (display only). Charge currency ${charge}. Rate as of ${when}.`
      );
    } else {
      setFxNote(null);
    }
    dispatch(setLastSearchRequestId(result.search_request_id));
  };

  const clearResult = () => {
    setOffers([]);
    setSearchRequestId(null);
    setLastQuery(null);
    setCacheHit(false);
    setCacheAgeSeconds(null);
    setSupplierCounts(null);
    setAirlineFacets(null);
    setAggregation(null);
    setFxNote(null);
  };

  const handleFlightSearch = async (query: any) => {
    try {
      setLastQuery(query);
      const result = await searchFlights(query).unwrap();
      applyResult(result);
    } catch (err) {
      console.error(err);
      clearResult();
    }
  };

  const handleHotelSearch = async (query: any) => {
    try {
      setLastQuery(query);
      const result = await searchHotels(query).unwrap();
      applyResult(result);
    } catch (err) {
      console.error(err);
      clearResult();
    }
  };

  const renderError = (error: any) => {
    if (!error) return null;
    const isRateLimit = error?.status === 429;
    return (
      <div className={`p-4 rounded-xl flex items-start gap-3 my-6 ${isRateLimit ? 'bg-orange-50 text-orange-800 border border-orange-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
        <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-semibold">{isRateLimit ? "Rate Limit Exceeded" : "Search Failed"}</h4>
          <p className="text-sm mt-1">
            {isRateLimit 
              ? "You have exceeded the maximum of 30 searches per minute for your organization. Please wait a moment and try again."
              : (error?.data?.detail || "An unexpected error occurred while searching inventory.")}
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8 pb-20">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="page-title">Search Inventory</h1>
          <p className="page-subtitle">Find and select flights and hotels for your clients.</p>
        </div>
      </div>

      <div id="inventory-search-form" className="w-full mt-6">
        <Tabs defaultValue="flights" className="w-full">
          <div className="flex mb-6">
            <TabsList className="inline-flex h-12 items-center justify-center rounded-full bg-sand p-1 text-muted-foreground">
              <TabsTrigger value="flights" className="inline-flex items-center justify-center whitespace-nowrap rounded-full px-8 py-2.5 text-sm font-semibold transition-all data-[state=active]:bg-paper data-[state=active]:text-ink data-[state=active]:shadow-sm gap-2">
                <Plane className="w-4 h-4" />
                Flights
              </TabsTrigger>
              <TabsTrigger value="hotels" className="inline-flex items-center justify-center whitespace-nowrap rounded-full px-8 py-2.5 text-sm font-semibold transition-all data-[state=active]:bg-paper data-[state=active]:text-ink data-[state=active]:shadow-sm gap-2">
                <Building2 className="w-4 h-4" />
                Hotels
              </TabsTrigger>
            </TabsList>
          </div>
          
          <div className="w-full relative z-10">
            <TabsContent value="flights" className="m-0 focus-visible:outline-none">
              <FlightSearchForm onSearch={handleFlightSearch} isLoading={isFlightsLoading} />
              {renderError(flightError)}
            </TabsContent>
            
            <TabsContent value="hotels" className="m-0 focus-visible:outline-none">
              <HotelSearchForm onSearch={handleHotelSearch} isLoading={isHotelsLoading} />
              {renderError(hotelError)}
            </TabsContent>
          </div>
        </Tabs>
      </div>

      {offers.length > 0 && searchRequestId && (
        <div className="pt-8 border-t border-line">
          <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-8">
            <OfferResults
              offers={offers}
              searchRequestId={searchRequestId}
              lastQuery={lastQuery}
              cacheHit={cacheHit}
              cacheAgeSeconds={cacheAgeSeconds}
              supplierCounts={supplierCounts}
              airlineFacets={airlineFacets}
              aggregation={aggregation}
              fxNote={fxNote}
              onEditSearch={() => {
                setOffers([]);
                setSearchRequestId(null);
                setLastQuery(null);
              }}
            />
            <div className="hidden xl:block">
               <SelectedFlightRail offers={selectedOffers} />
            </div>
            {selectedOffers.length > 0 && (
              <div className="xl:hidden fixed bottom-20 left-0 right-0 z-40 px-4 pb-safe">
                <div className="rounded-xl border border-line bg-paper/95 backdrop-blur shadow-lg p-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-xs text-muted-foreground">Selected</p>
                    <p className="text-sm font-medium text-ink truncate">{selectedOffers[selectedOffers.length - 1]?.title}</p>
                    <p className="font-mono text-sm text-teal">
                      {selectedOffers[selectedOffers.length - 1]?.currency}{" "}
                      {selectedOffers[selectedOffers.length - 1]?.total_amount?.toLocaleString()}
                    </p>
                  </div>
                  <Link href="/app/quotes/new">
                    <Button variant="gradient" size="sm" className="gap-1.5 shrink-0">
                      <ShoppingCart className="w-3.5 h-3.5" />
                      Quote
                    </Button>
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
