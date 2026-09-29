import { apiSlice } from "../apiSlice";

export interface PassengerQuery {
  adults: number;
  children: number;
  infants: number;
}

export interface SearchQuery {
  type: "flight" | "hotel";
  origin: string;
  destination: string;
  departure_date: string;
  return_date?: string;
  passengers: PassengerQuery;
  /** FC Phase 7 — promo / corp deal code */
  deal_code?: string;
}

export interface FlightSegment {
  origin: string;
  destination: string;
  departure_at?: string | null;
  arrival_at?: string | null;
  marketing_carrier?: string | null;
  operating_carrier?: string | null;
  flight_number?: string | null;
  duration_minutes?: number | null;
  cabin?: string | null;
}

export interface NormalizedOffer {
  id: string;
  supplier_code: string;
  supplier_reference: string;
  type: "flight" | "hotel";
  currency: string;
  total_amount: number;
  base_amount: number;
  tax_amount: number;
  /** FC Phase 4 — display conversion (does not replace total_amount) */
  money?: {
    currency: string;
    amount: number;
    display_currency: string;
    display_amount: number;
    fx_rate?: number;
    fx_as_of?: string | null;
    fx_source?: string | null;
  } | null;
  title: string;
  description?: string;
  raw_data: Record<string, any>;
  is_revalidated: boolean;
  valid_until?: string;
  /** FC Phase 1 — live | simulated | mock */
  inventory_mode?: string | null;
  /** FC Phase 3 */
  source_type?: string | null;
  duration_minutes?: number | null;
  stops?: number | null;
  airline_code?: string | null;
  airline_name?: string | null;
  depart_time?: string | null;
  /** FC Phase 6 */
  fare_family?: string | null;
  fare_family_code?: string | null;
  cabin?: string | null;
  baggage?: {
    cabin_kg?: number | null;
    checked_kg?: number | null;
    pieces?: number | null;
    notes?: string | null;
  } | null;
  family_group_id?: string | null;
  supports_ancillaries?: boolean | null;
  supports_seat_map?: boolean | null;
  /** FC Phase 7 */
  segments?: FlightSegment[] | null;
  deal_code?: string | null;
}

export interface SearchResponse {
  search_request_id: string;
  results_count: number;
  offers: NormalizedOffer[];
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
  fx_source?: string | null;
  ancillaries_enabled?: boolean;
  seat_map_enabled?: boolean;
}

export interface AncillaryOption {
  code: string;
  type: "baggage" | "meal" | "seat" | "ssr" | "other";
  label: string;
  description?: string;
  amount: number;
  currency: string;
  per_passenger?: boolean;
  meta?: Record<string, unknown>;
}

export interface AncillaryCatalog {
  supported: boolean;
  currency: string;
  items: AncillaryOption[];
  message?: string | null;
}

export interface SeatCell {
  seat: string;
  available: boolean;
  amount: number;
  currency: string;
  characteristics: string[];
}

export interface SeatMapResponse {
  supported: boolean;
  currency: string;
  cabin?: string | null;
  rows: { row: number; seats: SeatCell[] }[];
  message?: string | null;
}

export const inventoryApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    searchFlights: builder.mutation<SearchResponse, SearchQuery>({
      query: (body) => ({
        url: "/inventory/search/flights",
        method: "POST",
        body,
      }),
    }),
    searchHotels: builder.mutation<SearchResponse, SearchQuery>({
      query: (body) => ({
        url: "/inventory/search/hotels",
        method: "POST",
        body,
      }),
    }),
    revalidateOffer: builder.mutation<NormalizedOffer, { offer: NormalizedOffer }>({
      query: (body) => ({
        url: "/inventory/revalidate",
        method: "POST",
        body,
      }),
    }),
    getAncillaries: builder.mutation<AncillaryCatalog, { offer: NormalizedOffer }>({
      query: (body) => ({
        url: "/inventory/ancillaries",
        method: "POST",
        body,
      }),
    }),
    getSeatMap: builder.mutation<SeatMapResponse, { offer: NormalizedOffer }>({
      query: (body) => ({
        url: "/inventory/seat-map",
        method: "POST",
        body,
      }),
    }),
  }),
});

export const {
  useSearchFlightsMutation,
  useSearchHotelsMutation,
  useRevalidateOfferMutation,
  useGetAncillariesMutation,
  useGetSeatMapMutation,
} = inventoryApi;
