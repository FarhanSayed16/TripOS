import { apiSlice } from '../apiSlice';

export const crmApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getCustomers: builder.query<any, { page?: number; limit?: number; search?: string }>({
      query: (params) => {
        let qs = `?offset=${((params.page || 1) - 1) * (params.limit || 10)}&limit=${params.limit || 10}`;
        if (params.search) {
          qs += `&search=${encodeURIComponent(params.search)}`;
        }
        return `/customers${qs}`;
      },
      providesTags: ['Customer'],
    }),
    getCustomer: builder.query<any, string>({
      query: (id) => `/customers/${id}`,
      providesTags: (result, error, id) => [{ type: 'Customer', id }],
    }),
    createCustomer: builder.mutation<any, any>({
      query: (data) => ({
        url: '/customers',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Customer'],
    }),
    updateCustomer: builder.mutation<any, { id: string; data: any }>({
      query: ({ id, data }) => ({
        url: `/customers/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Customer', id }, 'Customer'],
    }),
    getCustomerTimeline: builder.query<any, string>({
      query: (id) => `/customers/${id}/timeline`,
      providesTags: (result, error, id) => [{ type: 'CustomerTimeline', id }],
    }),
  }),
});

export const {
  useGetCustomersQuery,
  useGetCustomerQuery,
  useCreateCustomerMutation,
  useUpdateCustomerMutation,
  useGetCustomerTimelineQuery,
} = crmApi;
