import { apiSlice } from "../apiSlice";

export interface PublicQuoteItem {
  id: string;
  customer_total: number;
  sanitized_offer_data: {
    title: string;
    description: string;
    type: string;
    currency: string;
  };
  money?: {
    currency: string;
    amount: number;
    display_currency: string;
    display_amount: number;
    fx_rate?: number;
    fx_as_of?: string | null;
    fx_source?: string | null;
  } | null;
}

export interface PublicQuote {
  id: string;
  status: "draft" | "ready" | "sent" | "paid" | "expired" | "cancelled";
  valid_until: string;
  items: PublicQuoteItem[];
  payment_link_url?: string | null;
  agency_name?: string;
  agency_logo_url?: string | null;
  payment_status?: string | null;
  booking_status?: string | null;
  charge_currency?: string;
  display_currency?: string;
  fx_rate?: number | null;
  fx_as_of?: string | null;
  fx_source?: string | null;
  charge_note?: string | null;
  locale?: string;
}

export const publicApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getPublicQuote: builder.query<PublicQuote, string>({
      query: (token) => `/public/quotes/${token}`,
    }),
    getTheme: builder.query<{brand_name: string, primary_color: string | null, logo_url: string | null}, string>({
      query: (domain) => `/public/theme/${domain}`,
    }),
  }),
});

export const { useGetPublicQuoteQuery, useGetThemeQuery } = publicApi;
