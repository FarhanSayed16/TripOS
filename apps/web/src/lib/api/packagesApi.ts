import { apiSlice } from "../apiSlice";

export interface PackageItem {
  id: string;
  type: string;
  title: string;
  description: string | null;
  estimated_cost_paise: number;
  supplier_code: string | null;
  sort_order: number;
}

export interface Package {
  id: string;
  organization_id: string;
  title: string;
  description: string | null;
  destination: string;
  duration_days: number;
  base_price_paise: number;
  cover_image_url: string | null;
  status: "draft" | "published" | "archived";
  created_at: string;
  items: PackageItem[];
}

export interface PackageItemCreate {
  type: string;
  title: string;
  description?: string | null;
  estimated_cost_paise: number;
  supplier_code?: string | null;
  search_params?: Record<string, any> | null;
  sort_order?: number;
}

export interface PackageCreate {
  title: string;
  description?: string | null;
  destination: string;
  duration_days: number;
  base_price_paise: number;
  cover_image_url?: string | null;
  items?: PackageItemCreate[];
}

export interface PackageUpdate {
  title?: string;
  description?: string | null;
  destination?: string;
  duration_days?: number;
  base_price_paise?: number;
  cover_image_url?: string | null;
  status?: string;
}

interface PaginatedPackages {
  items: Package[];
  total: number;
  limit: number;
  offset: number;
}

export const packagesApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getPackages: builder.query<PaginatedPackages, { status?: string; limit?: number; offset?: number } | void>({
      query: (params) => ({
        url: "/packages",
        params: params || {},
      }),
      providesTags: ["Package"],
    }),
    getPackage: builder.query<Package, string>({
      query: (id) => `/packages/${id}`,
      providesTags: (result, error, id) => [{ type: "Package", id }],
    }),
    createPackage: builder.mutation<Package, PackageCreate>({
      query: (body) => ({
        url: "/packages",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Package"],
    }),
    updatePackage: builder.mutation<Package, { id: string; data: PackageUpdate }>({
      query: ({ id, data }) => ({
        url: `/packages/${id}`,
        method: "PATCH",
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: "Package", id }],
    }),
    deletePackage: builder.mutation<void, string>({
      query: (id) => ({
        url: `/packages/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Package"],
    }),
    publishPackage: builder.mutation<Package, string>({
      query: (id) => ({
        url: `/packages/${id}/publish`,
        method: "POST",
      }),
      invalidatesTags: (result, error, id) => [{ type: "Package", id }],
    }),
    packageToQuote: builder.mutation<any, { package_id: string; customer_id: string }>({
      query: ({ package_id, customer_id }) => ({
        url: `/packages/${package_id}/to-quote`,
        method: "POST",
        body: { customer_id },
      }),
      invalidatesTags: ["Quote"],
    }),
    addPackageItem: builder.mutation<Package, { package_id: string; data: PackageItemCreate }>({
      query: ({ package_id, data }) => ({
        url: `/packages/${package_id}/items`,
        method: "POST",
        body: data,
      }),
      invalidatesTags: (result, error, { package_id }) => [{ type: "Package", id: package_id }],
    }),
    removePackageItem: builder.mutation<Package, { package_id: string; item_id: string }>({
      query: ({ package_id, item_id }) => ({
        url: `/packages/${package_id}/items/${item_id}`,
        method: "DELETE",
      }),
      invalidatesTags: (result, error, { package_id }) => [{ type: "Package", id: package_id }],
    }),
  }),
});

export const {
  useGetPackagesQuery,
  useGetPackageQuery,
  useCreatePackageMutation,
  useUpdatePackageMutation,
  useDeletePackageMutation,
  usePublishPackageMutation,
  usePackageToQuoteMutation,
  useAddPackageItemMutation,
  useRemovePackageItemMutation,
} = packagesApi;
