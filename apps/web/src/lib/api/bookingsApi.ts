import { apiSlice } from "../apiSlice";

export interface Booking {
  id: string;
  quote_id: string;
  status: "pending" | "confirmed" | "failed" | "cancelled";
  supplier_pnr?: string;
  failure_reason?: string;
  failure_label?: string;
  needs_manual_support?: boolean;
  created_at: string;
  updated_at?: string;
  quote?: {
    id: string;
    customer_name: string;
    total_price?: number;
    currency?: string;
    status?: string;
  };
}

export interface BookingChange {
  id: string;
  booking_id: string;
  organization_id: string;
  change_type: string;
  status: string;
  request_payload: Record<string, unknown>;
  supplier_diff_paise?: number | null;
  new_total_paise?: number | null;
  currency: string;
  notes?: string | null;
  manual_sop: boolean;
  created_at: string;
  updated_at: string;
  sop_hint?: string | null;
}

export const bookingsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getBookings: builder.query<Booking[], { status?: string } | void>({
      query: (params) => ({
        url: "/bookings",
        params: params || {},
      }),
      providesTags: ["Booking"],
    }),
    getBooking: builder.query<Booking, string>({
      query: (id) => `/bookings/${id}`,
      providesTags: (_r, _e, id) => [{ type: "Booking", id }],
    }),
    quoteBookingChange: builder.mutation<
      BookingChange,
      { bookingId: string; change_type: string; request_payload?: Record<string, unknown>; notes?: string }
    >({
      query: ({ bookingId, ...body }) => ({
        url: `/bookings/${bookingId}/changes/quote`,
        method: "POST",
        body,
      }),
    }),
    confirmBookingChange: builder.mutation<
      BookingChange,
      { changeId: string; payment_collected?: boolean; force_manual_sop?: boolean }
    >({
      query: ({ changeId, ...body }) => ({
        url: `/bookings/changes/${changeId}/confirm`,
        method: "POST",
        body,
      }),
    }),
    listBookingChanges: builder.query<BookingChange[], string>({
      query: (bookingId) => `/bookings/${bookingId}/changes`,
    }),
  }),
});

export const {
  useGetBookingsQuery,
  useGetBookingQuery,
  useQuoteBookingChangeMutation,
  useConfirmBookingChangeMutation,
  useListBookingChangesQuery,
} = bookingsApi;
