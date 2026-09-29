import { apiSlice } from "../apiSlice";

export interface WalletSummary {
  pending_paise: number;
  available_paise: number;
  total_earned_paise: number;
  total_settled_paise: number;
}

export interface WalletLedgerEntry {
  id: string;
  organization_id: string;
  booking_id: string | null;
  type: string;
  amount_paise: number;
  status: string;
  description: string | null;
  settled_at: string | null;
  created_at: string;
}

interface PaginatedLedger {
  items: WalletLedgerEntry[];
  total: number;
  limit: number;
  offset: number;
}

export const walletApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getWalletSummary: builder.query<WalletSummary, void>({
      query: () => "/wallet/summary",
      providesTags: ["Wallet"],
    }),
    getWalletLedger: builder.query<PaginatedLedger, { limit?: number; offset?: number } | void>({
      query: (params) => ({
        url: "/wallet/ledger",
        params: params || {},
      }),
      providesTags: ["Wallet"],
    }),
  }),
});

export const {
  useGetWalletSummaryQuery,
  useGetWalletLedgerQuery,
} = walletApi;
