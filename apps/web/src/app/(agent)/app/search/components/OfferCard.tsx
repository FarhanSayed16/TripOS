import { useDispatch, useSelector } from "react-redux";
import { addOffer } from "@/lib/quoteSlice";
import { RootState } from "@/lib/store";
import { NormalizedOffer } from "@/lib/api/inventoryApi";
import { Button } from "@/components/ui/button";
import { Plane, Building2, CheckCircle2, Clock, Luggage, ArrowRight } from "lucide-react";
import { useI18nOptional } from "@/lib/i18n";

function formatDuration(mins: number): string {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function stopsLabel(stops: number | null | undefined): string {
  if (stops == null) return "";
  if (stops === 0) return "Non-stop";
  return `${stops} stop${stops > 1 ? "s" : ""}`;
}

export function OfferCard({
  offer,
  searchRequestId,
}: {
  offer: NormalizedOffer;
  searchRequestId: string;
}) {
  const dispatch = useDispatch();
  const selectedOffers = useSelector((state: RootState) => state.quote.selectedOffers);
  const isSelected = selectedOffers.some((o) => o.id === offer.id);
  const { t } = useI18nOptional();

  const handleSelect = () => {
    if (!isSelected) {
      dispatch(addOffer({ ...offer, search_request_id: searchRequestId }));
    }
  };

  const airlineName = offer.airline_name || offer.airline_code || "";
  const departTime = offer.depart_time
    ? offer.depart_time
    : offer.segments?.[0]?.departure_at
      ? new Date(offer.segments[0].departure_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : null;

  const priceDisplay = offer.money
    ? `${offer.money.display_currency} ${offer.money.display_amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
    : `${offer.currency} ${offer.total_amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

  return (
    <div
      className={`group rounded-xl border bg-surface transition-all duration-200 hover:shadow-md ${
        isSelected
          ? "border-teal ring-2 ring-teal/15 shadow-sm"
          : "border-line hover:border-teal/30"
      }`}
    >
      <div className="p-5 flex flex-col sm:flex-row gap-5">
        {/* Left: Flight Info */}
        <div className="flex-1 min-w-0">
          {/* Row 1: Airline + Route */}
          <div className="flex items-center gap-3 mb-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
              offer.type === "flight"
                ? "bg-teal/10 text-teal"
                : "bg-amber-100 text-amber-700"
            }`}>
              {offer.type === "flight" ? (
                <Plane className="w-5 h-5" />
              ) : (
                <Building2 className="w-5 h-5" />
              )}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-ink text-[15px]">{airlineName || offer.title}</span>
                {offer.fare_family && (
                  <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-teal/10 text-teal border border-teal/20">
                    {offer.fare_family}
                  </span>
                )}
              </div>
              {airlineName && offer.title !== airlineName && (
                <p className="text-xs text-muted-foreground truncate">{offer.title}</p>
              )}
            </div>
          </div>

          {/* Row 2: Route Timeline */}
          {offer.type === "flight" && (
            <div className="flex items-center gap-4 mb-3 pl-1">
              {/* Depart */}
              <div className="text-center">
                <div className="text-lg font-bold text-ink leading-tight">
                  {departTime || "—"}
                </div>
                <div className="text-[11px] text-muted-foreground font-medium uppercase">
                  {offer.segments?.[0]?.origin || ""}
                </div>
              </div>

              {/* Duration line */}
              <div className="flex-1 flex flex-col items-center gap-0.5 px-2">
                <span className="text-[11px] text-muted-foreground font-medium">
                  {offer.duration_minutes != null ? formatDuration(offer.duration_minutes) : ""}
                </span>
                <div className="w-full relative h-[2px]">
                  <div className="absolute inset-0 bg-line rounded-full" />
                  {offer.stops != null && offer.stops > 0 && (
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-amber-400 border-2 border-surface" />
                  )}
                </div>
                <span className="text-[10px] text-muted-foreground">
                  {stopsLabel(offer.stops)}
                </span>
              </div>

              {/* Arrive */}
              <div className="text-center">
                <div className="text-lg font-bold text-ink leading-tight">
                  {offer.segments && offer.segments.length > 0
                    ? offer.segments[offer.segments.length - 1]?.arrival_at
                      ? new Date(offer.segments[offer.segments.length - 1].arrival_at!).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                      : "—"
                    : "—"}
                </div>
                <div className="text-[11px] text-muted-foreground font-medium uppercase">
                  {offer.segments && offer.segments.length > 0
                    ? offer.segments[offer.segments.length - 1]?.destination || ""
                    : ""}
                </div>
              </div>
            </div>
          )}

          {/* Row 3: Tags */}
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            {offer.baggage && (
              <span className="inline-flex items-center gap-1 bg-paper border border-line rounded-md px-2 py-0.5">
                <Luggage className="w-3 h-3" />
                {offer.baggage.checked_kg != null
                  ? `${offer.baggage.checked_kg}kg`
                  : "No bag"}
              </span>
            )}
            {offer.deal_code && (
              <span className="inline-flex items-center gap-1 bg-teal/10 text-teal border border-teal/20 rounded-md px-2 py-0.5 font-semibold uppercase">
                Deal: {offer.deal_code}
              </span>
            )}
            {offer.description && !airlineName && (
              <span className="text-muted-foreground">{offer.description}</span>
            )}
          </div>
        </div>

        {/* Right: Price + Action */}
        <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-3 shrink-0 sm:min-w-[140px] sm:pl-5 sm:border-l sm:border-line">
          <div className="text-right">
            <div className="text-2xl font-bold text-ink font-mono tracking-tight leading-tight">
              {priceDisplay}
            </div>
            {offer.money &&
              offer.money.display_currency !== offer.money.currency && (
                <div className="text-[11px] text-muted-foreground mt-0.5 font-mono">
                  Charge: {offer.money.currency} {offer.money.amount.toLocaleString()}
                </div>
              )}
            <div className="text-[10px] text-muted-foreground/50 mt-0.5">per person</div>
          </div>
          <Button
            onClick={handleSelect}
            variant={isSelected ? "secondary" : "gradient"}
            disabled={isSelected}
            size="sm"
            className={`transition-all w-full sm:w-auto ${isSelected ? "" : "shadow-sm"}`}
          >
            {isSelected ? (
              <>
                <CheckCircle2 className="w-4 h-4 mr-1.5" /> {t("search.selected")}
              </>
            ) : (
              <>
                {t("search.addToQuote")} <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
