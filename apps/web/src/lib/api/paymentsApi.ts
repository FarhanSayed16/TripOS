import { apiSlice } from "../apiSlice";

export interface Payment {
  id: string;
  quote_id: string;
  status: "pending" | "captured" | "failed" | "refunded";
  amount: number;
  gateway_order_id: string;
  gateway_payment_id?: string;
  created_at: string;
}

export const paymentsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getPayments: builder.query<{ items: Payment[]; total: number }, { status?: string }>({
      query: (params) => ({
        url: "/payments",
        params,
      }),
      providesTags: ["Payment"],
    }),
  }),
});

export const {
  useGetPaymentsQuery,
} = paymentsApi;
