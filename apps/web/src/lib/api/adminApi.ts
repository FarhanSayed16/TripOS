import { apiSlice } from "../apiSlice";

export interface AdminOrganization {
  id: string;
  brand_name: string;
  status: "active" | "inactive" | "pending_approval";
  created_at: string;
}

export interface AdminBooking {
  id: string;
  quote_id: string;
  quote_public_token: string | null;
  organization_name: string;
  status: string;
  failure_reason: string | null;
  supplier_pnr: string | null;
  created_at: string;
}

export interface AdminPayment {
  id: string;
  quote_id: string;
  organization_name: string;
  amount: number;
  status: string;
  gateway_order_id: string | null;
  gateway_payment_id: string | null;
  created_at: string;
}

export interface AdminDeadLetter {
  id: string;
  type: string;
  payload: Record<string, unknown> | null;
  error_details: string | null;
  attempts: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface AdminAnalytics {
  active_orgs: number;
  total_quotes: number;
  total_bookings: number;
  confirmed_bookings: number;
  failed_bookings: number;
  booking_failure_rate: number;
  total_gmv_paise: number;
  monthly_active_transacting_agents: number;
  avg_gmv_per_agent_paise: number;
  dead_letter_jobs: number;
  payment_captured_booking_failed_7d?: number;
  l2b_7d?: {
    l2b_ratio: number;
    status: string;
    looks: number;
    confirmed_bookings: number;
  };
  l2b_survival?: {
    enabled: boolean;
    active: boolean;
    status: string;
    l2b_ratio: number;
    ttl_multiplier: number;
    ttl_cap_seconds: number;
    pause_warm_refresh: boolean;
  };
}

export interface AdminL2bSurvival {
  enabled: boolean;
  active: boolean;
  status: string;
  l2b_ratio: number;
  looks: number;
  confirmed_bookings: number;
  ttl_multiplier: number;
  ttl_cap_seconds: number;
  pause_warm_refresh: boolean;
  warn_ratio: number;
  critical_ratio: number;
}

export interface AdminRefund {
  id: string;
  payment_id: string;
  quote_id?: string;
  amount: number;
  status: string;
  reason?: string | null;
  notes?: string | null;
  gateway_refund_id?: string | null;
  created_at: string;
}

export interface AdminL2bOrg {
  organization_id: string;
  organization_name?: string;
  searches: number;
  revalidates: number;
  books: number;
  confirmed_bookings: number;
  looks: number;
  l2b_ratio: number;
  status: string;
}

export interface AdminL2bOrgsResponse {
  window_days: number;
  warn_ratio: number;
  critical_ratio: number;
  orgs: AdminL2bOrg[];
}

export interface AdminCommissionSummary {
  organization_id: string;
  organization_name: string;
  pending_paise: number;
  available_paise: number;
  settled_paise: number;
}

export const adminApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getAdminOrganizations: builder.query<AdminOrganization[], void>({
      query: () => "/admin/organizations",
      providesTags: ["Organization"],
    }),
    approveOrganization: builder.mutation<AdminOrganization, string>({
      query: (id) => ({
        url: `/admin/organizations/${id}/approve`,
        method: "POST",
      }),
      invalidatesTags: ["Organization"],
    }),
    rejectOrganization: builder.mutation<AdminOrganization, string>({
      query: (id) => ({
        url: `/admin/organizations/${id}/reject`,
        method: "POST",
      }),
      invalidatesTags: ["Organization"],
    }),
    getAdminBookings: builder.query<AdminBooking[], void>({
      query: () => "/admin/bookings",
      providesTags: ["Booking"],
    }),
    getAdminPayments: builder.query<AdminPayment[], void>({
      query: () => "/admin/payments",
    }),
    getAdminDeadLetters: builder.query<AdminDeadLetter[], void>({
      query: () => "/admin/dead-letters",
      providesTags: ["DeadLetter"],
    }),
    getAdminAnalytics: builder.query<AdminAnalytics, number | void>({
      query: (days) => ({
        url: "/admin/analytics",
        params: { days: days || 30 },
      }),
      providesTags: ["Analytics"],
    }),
    getAdminL2bOrgs: builder.query<AdminL2bOrgsResponse, { days?: number; limit?: number } | void>({
      query: (params) => ({
        url: "/admin/l2b/orgs",
        params: { days: params?.days || 7, limit: params?.limit || 20 },
      }),
    }),
    getAdminL2bSurvival: builder.query<AdminL2bSurvival, void>({
      query: () => "/admin/l2b/survival",
    }),
    getAdminRefunds: builder.query<
      { items: AdminRefund[]; count: number },
      { status?: string; limit?: number } | void
    >({
      query: (params) => ({
        url: "/admin/refunds",
        params: {
          status: params?.status,
          limit: params?.limit || 50,
        },
      }),
      providesTags: ["Analytics"],
    }),
    updateAdminRefundStatus: builder.mutation<
      AdminRefund,
      { id: string; status: string; notes?: string; gateway_refund_id?: string }
    >({
      query: ({ id, ...body }) => ({
        url: `/admin/refunds/${id}/status`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["Analytics"],
    }),
    getAdminSuppliersHealth: builder.query<
      {
        window_seconds: number;
        l2b_7d?: { l2b_ratio: number; status: string };
        suppliers: {
          supplier_code: string;
          sample_count: number;
          error_rate: number;
          latency_p95_ms?: number | null;
          circuit_state: string;
          circuit_open: boolean;
        }[];
      },
      void
    >({
      query: () => "/admin/suppliers/health",
    }),
    getAdminCommissions: builder.query<AdminCommissionSummary[], void>({
      query: () => "/admin/commissions",
      providesTags: ["Commission"],
    }),
    settleCommissions: builder.mutation<{ status: string; settled_amount_paise: number }, string>({
      query: (org_id) => ({
        url: `/admin/commissions/${org_id}/settle`,
        method: "POST",
      }),
      invalidatesTags: ["Commission"],
    }),
    getFxRates: builder.query<
      {
        charge_currency: string;
        fx_provider_enabled: boolean;
        items: {
          id: string;
          base_currency: string;
          quote_currency: string;
          rate: number;
          as_of: string | null;
          source: string;
          is_active: boolean;
        }[];
      },
      void
    >({
      query: () => "/admin/fx-rates",
      providesTags: ["FxRates"],
    }),
    upsertFxRate: builder.mutation<
      any,
      {
        base_currency?: string;
        quote_currency: string;
        rate: number;
        source?: string;
        is_active?: boolean;
      }
    >({
      query: (body) => ({
        url: "/admin/fx-rates",
        method: "POST",
        body,
      }),
      invalidatesTags: ["FxRates"],
    }),
    seedFxRates: builder.mutation<{ seeded: number; pairs: string[] }, void>({
      query: () => ({
        url: "/admin/fx-rates/seed",
        method: "POST",
      }),
      invalidatesTags: ["FxRates"],
    }),
    getPartnerApps: builder.query<
      {
        id: string;
        organization_id: string;
        name: string;
        key_prefix: string;
        env: string;
        webhook_url?: string | null;
        scopes: string[];
        rate_limit_per_minute: number;
        is_active: boolean;
        last_used_at?: string | null;
        created_at: string;
        api_key?: string | null;
        webhook_secret?: string | null;
      }[],
      void
    >({
      query: () => "/admin/partners",
      providesTags: ["Partners"],
    }),
    createPartnerApp: builder.mutation<
      {
        id: string;
        organization_id: string;
        name: string;
        key_prefix: string;
        api_key?: string | null;
        webhook_secret?: string | null;
      },
      {
        organization_id: string;
        name: string;
        env?: string;
        webhook_url?: string;
        rate_limit_per_minute?: number;
      }
    >({
      query: (body) => ({
        url: "/admin/partners",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Partners"],
    }),
    rotatePartnerKey: builder.mutation<
      { id: string; api_key?: string | null; webhook_secret?: string | null; key_prefix: string },
      string
    >({
      query: (id) => ({
        url: `/admin/partners/${id}/rotate-key`,
        method: "POST",
      }),
      invalidatesTags: ["Partners"],
    }),
    getPartnerUsage: builder.query<
      {
        partner_app_id: string;
        organization_id: string;
        name: string;
        rate_limit_per_minute: number;
        l2b: Record<string, unknown>;
      },
      string
    >({
      query: (id) => `/admin/partners/${id}/usage`,
    }),
  }),
});

export const {
  useGetAdminOrganizationsQuery,
  useApproveOrganizationMutation,
  useRejectOrganizationMutation,
  useGetAdminBookingsQuery,
  useGetAdminPaymentsQuery,
  useGetAdminDeadLettersQuery,
  useGetAdminAnalyticsQuery,
  useGetAdminL2bOrgsQuery,
  useGetAdminL2bSurvivalQuery,
  useGetAdminRefundsQuery,
  useUpdateAdminRefundStatusMutation,
  useGetAdminSuppliersHealthQuery,
  useGetAdminCommissionsQuery,
  useSettleCommissionsMutation,
  useGetFxRatesQuery,
  useUpsertFxRateMutation,
  useSeedFxRatesMutation,
  useGetPartnerAppsQuery,
  useCreatePartnerAppMutation,
  useRotatePartnerKeyMutation,
  useGetPartnerUsageQuery,
} = adminApi;
