import { apiSlice } from "../apiSlice";

export interface OrgSettings {
  id: string;
  brand_name: string;
  slug: string;
  logo_url?: string | null;
  primary_color?: string | null;
  status: string;
  preferred_currency: string;
  default_locale?: string;
}

export const orgApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getMyOrganization: builder.query<OrgSettings, void>({
      query: () => "/organizations/me",
      providesTags: ["Organization"],
    }),
    updateMyOrganization: builder.mutation<
      OrgSettings,
      {
        brand_name?: string;
        logo_url?: string;
        primary_color?: string;
        preferred_currency?: string;
        default_locale?: string;
      }
    >({
      query: (body) => ({
        url: "/organizations/me",
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["Organization"],
    }),
  }),
});

export const {
  useGetMyOrganizationQuery,
  useUpdateMyOrganizationMutation,
} = orgApi;
