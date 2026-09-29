"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  useGetAncillariesMutation,
  useGetSeatMapMutation,
  NormalizedOffer,
  AncillaryOption,
  SeatCell,
} from "@/lib/api/inventoryApi";
import { useUpdateQuoteItemExtrasMutation, QuoteItem } from "@/lib/api/quotesApi";
import { formatPaiseAsMoney } from "@/lib/money";

type ExtraLine = {
  type: string;
  code: string;
  label: string;
  amount_paise: number;
  passenger_index?: number | null;
  meta?: Record<string, unknown>;
};

export function QuoteExtrasPanel({
  quoteId,
  item,
  offer,
  editable,
}: {
  quoteId: string;
  item: QuoteItem;
  offer: NormalizedOffer | null;
  editable: boolean;
}) {
  const [getAncillaries, { data: catalog, isLoading: loadingAnc }] =
    useGetAncillariesMutation();
  const [getSeatMap, { data: seatMap, isLoading: loadingSeats }] =
    useGetSeatMapMutation();
  const [updateExtras, { isLoading: saving }] = useUpdateQuoteItemExtrasMutation();
  const [selected, setSelected] = useState<ExtraLine[]>(
    (item.extras || []).map((e) => ({ ...e }))
  );
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    setSelected((item.extras || []).map((e) => ({ ...e })));
  }, [item.id, item.extras]);

  useEffect(() => {
    if (!offer || !editable) return;
    if (offer.supports_ancillaries !== false) {
      getAncillaries({ offer }).catch(() => undefined);
    }
    if (offer.supports_seat_map) {
      getSeatMap({ offer }).catch(() => undefined);
    }
  }, [offer?.id, editable]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleAncillary = (opt: AncillaryOption) => {
    setSelected((prev) => {
      const exists = prev.find((p) => p.code === opt.code && p.type === opt.type);
      if (exists) return prev.filter((p) => !(p.code === opt.code && p.type === opt.type));
      return [
        ...prev.filter((p) => !(p.type === opt.type && opt.type === "meal")), // one meal
        {
          type: opt.type,
          code: opt.code,
          label: opt.label,
          amount_paise: Math.round(opt.amount * 100),
          meta: opt.meta || {},
        },
      ];
    });
  };

  const pickSeat = (cell: SeatCell) => {
    if (!cell.available) return;
    setSelected((prev) => {
      const withoutSeats = prev.filter((p) => p.type !== "seat");
      return [
        ...withoutSeats,
        {
          type: "seat",
          code: cell.seat,
          label: `Seat ${cell.seat}`,
          amount_paise: Math.round(cell.amount * 100),
          meta: { characteristics: cell.characteristics },
        },
      ];
    });
  };

  const save = async () => {
    try {
      await updateExtras({
        quoteId,
        itemId: item.id,
        extras: selected,
      }).unwrap();
      setMsg("Extras saved — total updated.");
    } catch {
      setMsg("Could not save extras.");
    }
  };

  const extrasSum = selected.reduce((s, e) => s + e.amount_paise, 0);

  if (!offer && (!item.extras || item.extras.length === 0)) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Fare extras & seats</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {offer?.fare_family && (
          <p className="text-sm text-gray-600">
            Fare family: <Badge variant="outline">{offer.fare_family}</Badge>
            {offer.cabin ? ` · ${offer.cabin}` : ""}
            {offer.baggage?.checked_kg != null
              ? ` · ${offer.baggage.checked_kg}kg checked`
              : ""}
          </p>
        )}

        {selected.length > 0 && (
          <ul className="text-sm space-y-1 border border-line rounded-md p-3 bg-sand/20">
            {selected.map((e) => (
              <li key={`${e.type}-${e.code}`} className="flex justify-between">
                <span>
                  {e.label}
                  <span className="text-xs text-gray-400 ml-2">{e.type}</span>
                </span>
                <span className="font-mono">
                  {formatPaiseAsMoney(e.amount_paise)}
                </span>
              </li>
            ))}
            <li className="flex justify-between font-semibold pt-2 border-t border-line">
              <span>Extras subtotal</span>
              <span>{formatPaiseAsMoney(extrasSum)}</span>
            </li>
          </ul>
        )}

        {editable && catalog?.supported && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Baggage / meals / SSR
            </p>
            {loadingAnc && <p className="text-xs text-gray-400">Loading options…</p>}
            <div className="grid gap-2 sm:grid-cols-2">
              {(catalog.items || []).map((opt) => {
                const on = selected.some(
                  (s) => s.code === opt.code && s.type === opt.type
                );
                return (
                  <button
                    key={opt.code}
                    type="button"
                    onClick={() => toggleAncillary(opt)}
                    className={`text-left text-sm border rounded-md px-3 py-2 transition-colors ${
                      on
                        ? "border-focus bg-focus/5"
                        : "border-line hover:border-focus/40"
                    }`}
                  >
                    <div className="font-medium">{opt.label}</div>
                    <div className="text-xs text-gray-500">
                      {opt.currency} {opt.amount.toLocaleString()}
                      {opt.description ? ` · ${opt.description}` : ""}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {editable && seatMap?.supported && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Seat map
            </p>
            {loadingSeats && <p className="text-xs text-gray-400">Loading seats…</p>}
            <div className="overflow-x-auto">
              <div className="inline-flex flex-col gap-1 font-mono text-xs">
                {(seatMap.rows || []).map((row) => (
                  <div key={row.row} className="flex gap-1 items-center">
                    <span className="w-6 text-gray-400">{row.row}</span>
                    {row.seats.map((cell) => {
                      const picked = selected.some(
                        (s) => s.type === "seat" && s.code === cell.seat
                      );
                      return (
                        <button
                          key={cell.seat}
                          type="button"
                          disabled={!cell.available}
                          onClick={() => pickSeat(cell)}
                          title={`${cell.seat} · ${cell.amount}`}
                          className={`w-8 h-8 rounded border text-[10px] ${
                            !cell.available
                              ? "bg-gray-100 text-gray-300 border-gray-100"
                              : picked
                                ? "bg-focus text-white border-focus"
                                : "bg-white border-line hover:border-focus"
                          }`}
                        >
                          {cell.seat.slice(-1)}
                        </button>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {!editable && (!item.extras || item.extras.length === 0) && (
          <p className="text-sm text-gray-500">No extras on this item.</p>
        )}

        {editable && (
          <Button onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save extras"}
          </Button>
        )}
        {msg && <p className="text-xs text-focus">{msg}</p>}
      </CardContent>
    </Card>
  );
}
