import { apiSlice } from "../apiSlice";

export interface BookingDocument {
  id: string;
  booking_id: string;
  organization_id: string;
  type: string;
  filename: string;
  storage_url: string;
  mime_type: string;
  uploaded_by_user_id: string;
  created_at: string;
}

export const documentsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getBookingDocuments: builder.query<BookingDocument[], string>({
      query: (booking_id) => `/bookings/${booking_id}/documents`,
      providesTags: (result, error, booking_id) => [{ type: "Document", id: booking_id }],
    }),
    uploadDocument: builder.mutation<BookingDocument, { booking_id: string; data: FormData }>({
      query: ({ booking_id, data }) => ({
        url: `/bookings/${booking_id}/documents`,
        method: "POST",
        body: data,
      }),
      invalidatesTags: (result, error, { booking_id }) => [{ type: "Document", id: booking_id }],
    }),
    deleteDocument: builder.mutation<void, string>({
      query: (doc_id) => ({
        url: `/documents/${doc_id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Document"],
    }),
  }),
});

export const {
  useGetBookingDocumentsQuery,
  useUploadDocumentMutation,
  useDeleteDocumentMutation,
} = documentsApi;
