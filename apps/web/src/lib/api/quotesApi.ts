import { apiSlice } from "../apiSlice";
import { NormalizedOffer } from "./inventoryApi";

export interface QuotePassenger {
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  passport_number?: string;
}

export interface QuoteItem {
  id: string;
  offer_snapshot_id: string;
  supplier_cost: number;
  agent_markup: number;
  platform_fee: number;
  customer_total: number;
  extras?: {
    type: string;
    code: string;
    label: string;
    amount_paise: number;
    passenger_index?: number | null;
    meta?: Record<string, unknown>;
  }[];
  extras_total?: number;
  money?: {
    currency: string;
    amount: number;
    display_currency: string;
    display_amount: number;
    fx_rate?: number;
    fx_as_of?: string | null;
    fx_source?: string | null;
  } | null;
  offer?: NormalizedOffer;
}

export interface Quote {
  id: string;
  customer_id: string;
  public_token: string;
  status: "draft" | "ready" | "sent" | "paid" | "expired" | "cancelled";
  valid_until: string;
  created_at: string;
  payment_link_url?: string;
  booking?: {
    id: string;
    status: 'pending' | 'confirmed' | 'failed' | 'cancelled';
    supplier_pnr?: string;
    failure_reason?: string;
  };
  items: QuoteItem[];
  passengers: QuotePassenger[];
  charge_currency?: string;
  display_currency?: string;
  fx_rate?: number | null;
  fx_as_of?: string | null;
  fx_source?: string | null;
}

export interface QuoteCreatePayload {
  customer_id: string;
  items: {
    search_request_id: string;
    offer: NormalizedOffer;
    agent_markup: number; // in paise
  }[];
}

export const quotesApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getQuotes: builder.query<{ items: Quote[]; total: number }, { status?: string; page?: number }>({
      query: (params) => ({
        url: "/quotes", // NOTE: The backend doesn't have a GET /quotes list yet, we'll need to create it or mock it.
        params,
      }),
      providesTags: ["Quote"],
    }),
    getQuote: builder.query<Quote, string>({
      query: (id) => `/quotes/${id}`,
      providesTags: (result, error, id) => [{ type: "Quote", id }],
    }),
    createQuote: builder.mutation<Quote, QuoteCreatePayload>({
      query: (body) => ({
        url: "/quotes",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Quote"],
    }),
    updatePassengers: builder.mutation<Quote, { id: string; passengers: QuotePassenger[] }>({
      query: ({ id, passengers }) => ({
        url: `/quotes/${id}/passengers`,
        method: "PUT",
        body: passengers,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: "Quote", id }],
    }),
    markQuoteReady: builder.mutation<Quote, string>({
      query: (id) => ({
        url: `/quotes/${id}/ready`,
        method: "POST",
      }),
      invalidatesTags: (result, error, id) => [{ type: "Quote", id }],
    }),
    generatePaymentLink: builder.mutation<
      { id: string; gateway_order_id?: string; status: string; payment_link_url?: string },
      string
    >({
      query: (id) => ({
        url: `/quotes/${id}/payment`,
        method: "POST",
      }),
      invalidatesTags: (result, error, id) => [{ type: "Quote", id }, "Payment"],
    }),
    getWhatsappPreview: builder.query<
      { phone_e164: string; message_template: string; wa_me_url?: string },
      string
    >({
      query: (id) => `/quotes/${id}/whatsapp-preview`,
    }),
    sendQuote: builder.mutation<Quote, { id: string, content: string, channel?: string }>({
      query: ({ id, content, channel = "whatsapp" }) => ({
        url: `/quotes/${id}/send`,
        method: "POST",
        body: { content, channel },
      }),
      invalidatesTags: (result, error, { id }) => [{ type: "Quote", id }],
    }),
    cancelQuote: builder.mutation<Quote, string>({
      query: (id) => ({
        url: `/quotes/${id}/cancel`,
        method: "POST",
      }),
      invalidatesTags: (result, error, id) => [{ type: "Quote", id }, "Booking"],
    }),
    refreshQuote: builder.mutation<Quote, string>({
      query: (id) => ({
        url: `/quotes/${id}/refresh`,
        method: "POST",
      }),
      invalidatesTags: ["Quote"],
    }),
    getQuoteAuditEvents: builder.query<
      { id: string; action: string; created_at: string; metadata?: any }[],
      string
    >({
      query: (id) => `/quotes/${id}/audit`,
      providesTags: (result, error, id) => [{ type: "QuoteAudit", id }],
    }),
    getQuoteFareRules: builder.query<
      {
        supplier_code: string;
        supplier_reference: string;
        is_refundable?: boolean | null;
        change_allowed?: boolean | null;
        cancel_penalty_summary?: string | null;
        change_penalty_summary?: string | null;
        baggage_summary?: string | null;
        raw_text?: string | null;
        source: string;
      },
      string
    >({
      query: (id) => `/quotes/${id}/fare-rules`,
    }),
    getQuoteRefunds: builder.query<
      {
        id: string;
        amount: number;
        status: string;
        reason?: string | null;
        notes?: string | null;
        gateway_refund_id?: string | null;
        created_at: string;
      }[],
      string
    >({
      query: (id) => `/quotes/${id}/refunds`,
      providesTags: (result, error, id) => [{ type: "Quote", id }],
    }),
    updateQuoteItemExtras: builder.mutation<
      Quote,
      {
        quoteId: string;
        itemId: string;
        extras: {
          type: string;
          code: string;
          label: string;
          amount_paise: number;
          passenger_index?: number | null;
          meta?: Record<string, unknown>;
        }[];
      }
    >({
      query: ({ quoteId, itemId, extras }) => ({
        url: `/quotes/${quoteId}/items/${itemId}/extras`,
        method: "PUT",
        body: { extras },
      }),
      invalidatesTags: (result, error, { quoteId }) => [{ type: "Quote", id: quoteId }],
    }),
  }),
});

export const {
  useGetQuotesQuery,
  useGetQuoteQuery,
  useCreateQuoteMutation,
  useUpdatePassengersMutation,
  useMarkQuoteReadyMutation,
  useGeneratePaymentLinkMutation,
  useGetWhatsappPreviewQuery,
  useSendQuoteMutation,
  useCancelQuoteMutation,
  useRefreshQuoteMutation,
  useGetQuoteAuditEventsQuery,
  useGetQuoteFareRulesQuery,
  useGetQuoteRefundsQuery,
  useUpdateQuoteItemExtrasMutation,
} = quotesApi;
