import { useDispatch, useSelector } from "react-redux";
import { addOffer } from "@/lib/quoteSlice";
import { RootState } from "@/lib/store";
import { NormalizedOffer } from "@/lib/api/inventoryApi";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plane, Building2, CheckCircle2 } from "lucide-react";
import { useI18nOptional } from "@/lib/i18n";

function sourceLabel(offer: NormalizedOffer): string {
  const mode = offer.inventory_mode || offer.raw_data?.inventory_mode;
  const code = offer.supplier_code || "supplier";
  const src = offer.source_type ? ` · ${offer.source_type}` : "";
  if (mode === "live") return `${code}${src} · live`;
  if (mode === "simulated") return `${code}${src} · simulated`;
  if (mode === "mock") return `${code}${src} · mock`;
  return `${code}${src}`;
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
  const mode = offer.inventory_mode || offer.raw_data?.inventory_mode;
  const isIndicativeSim = mode === "simulated";
  const { t } = useI18nOptional();

  const handleSelect = () => {
    if (!isSelected) {
      dispatch(addOffer({ ...offer, search_request_id: searchRequestId }));
    }
  };

  return (
    <Card className={`transition-all duration-300 ${isSelected ? "border-teal ring-1 ring-teal bg-teal/5" : "hover:border-focus bg-surface"}`}>
      <CardContent className="p-4 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-full bg-sand flex items-center justify-center flex-shrink-0">
            {offer.type === "flight" ? (
              <Plane className="w-6 h-6 text-focus" />
            ) : (
              <Building2 className="w-6 h-6 text-focus" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-ink">{offer.title}</h3>
              {offer.fare_family && (
                <span className="text-[10px] font-medium uppercase tracking-wide px-2 py-0.5 rounded border bg-sand text-ink border-line">
                  {offer.fare_family}
                </span>
              )}
              <span
                className={`text-[10px] font-medium uppercase tracking-wide px-2 py-0.5 rounded border ${
                  mode === "live"
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                    : isIndicativeSim
                      ? "bg-amber-50 text-amber-800 border-amber-200"
                      : "bg-surface text-muted-foreground border-line"
                }`}
              >
                {sourceLabel(offer)}
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{offer.description}</p>
            {offer.baggage && (
              <p className="text-xs text-muted-foreground mt-1">
                Baggage
                {offer.baggage.cabin_kg != null ? ` · cabin ${offer.baggage.cabin_kg}kg` : ""}
                {offer.baggage.checked_kg != null
                  ? ` · checked ${offer.baggage.checked_kg}kg`
                  : " · no checked"}
              </p>
            )}
            {(offer.duration_minutes != null || offer.stops != null) && (
              <p className="text-xs text-muted-foreground mt-1">
                {offer.stops != null
                  ? offer.stops === 0
                    ? "Non-stop"
                    : `${offer.stops} stop${offer.stops === 1 ? "" : "s"}`
                  : null}
                {offer.stops != null && offer.duration_minutes != null ? " · " : null}
                {offer.duration_minutes != null
                  ? `${Math.floor(offer.duration_minutes / 60)}h ${offer.duration_minutes % 60}m`
                  : null}
                {offer.depart_time ? ` · Departs ${offer.depart_time}` : null}
              </p>
            )}
            {offer.segments && offer.segments.length > 0 && (
              <div className="text-xs text-muted-foreground mt-1 space-y-0.5">
                {offer.segments.map((seg, i) => {
                  const mkt = seg.marketing_carrier || "?";
                  const op = seg.operating_carrier || mkt;
                  const codeshare = op !== mkt ? ` (op ${op})` : "";
                  return (
                    <p key={`${seg.flight_number}-${i}`}>
                      {seg.origin}→{seg.destination}
                      {seg.flight_number ? ` · ${seg.flight_number}` : ""}
                      {` · mkt ${mkt}${codeshare}`}
                      {seg.departure_at ? ` · ${seg.departure_at}` : ""}
                    </p>
                  );
                })}
              </div>
            )}
            {offer.deal_code && (
              <span className="inline-block mt-2 text-[10px] font-semibold bg-teal-100 text-teal-800 px-2 py-0.5 rounded border border-teal-200 uppercase tracking-wide">
                Deal: {offer.deal_code}
              </span>
            )}
            <p className="text-xs text-muted-foreground/60 mt-2 font-mono">Ref: {offer.supplier_reference}</p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <div className="text-right">
            <div className="text-xl font-bold text-ink font-mono tracking-tight">
              {offer.money
                ? `${offer.money.display_currency} ${offer.money.display_amount.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
                : `${offer.currency} ${offer.total_amount.toLocaleString()}`}
            </div>
            {offer.money &&
              offer.money.display_currency !== offer.money.currency && (
                <div className="text-[11px] text-muted-foreground mt-0.5 flex items-center justify-end gap-1">
                  <span>Charge:</span>
                  <span className="font-mono">
                    {offer.money.currency} {offer.money.amount.toLocaleString()}
                  </span>
                </div>
              )}
          </div>
          <Button
            onClick={handleSelect}
            variant={isSelected ? "secondary" : "default"}
            disabled={isSelected}
            className="w-full sm:w-auto transition-all"
          >
            {isSelected ? (
              <>
                <CheckCircle2 className="w-4 h-4 mr-2" /> {t("search.selected")}
              </>
            ) : (
              t("search.addToQuote")
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
