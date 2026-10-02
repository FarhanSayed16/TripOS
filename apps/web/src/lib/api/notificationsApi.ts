import { apiSlice } from "../apiSlice";

export interface Notification {
  id: string;
  organization_id: string;
  user_id: string | null;
  type: string;
  title: string;
  body: string | null;
  icon: string;
  severity: "info" | "warning" | "error" | "success";
  link: string | null;
  is_read: boolean;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface UnreadCount {
  count: number;
}

export const notificationsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getNotifications: builder.query<Notification[], { limit?: number; unread_only?: boolean }>({
      query: ({ limit = 30, unread_only = false } = {}) =>
        `/notifications?limit=${limit}&unread_only=${unread_only}`,
      providesTags: ["Notification"],
    }),
    getUnreadCount: builder.query<UnreadCount, void>({
      query: () => "/notifications/unread-count",
      providesTags: ["Notification"],
    }),
    markRead: builder.mutation<{ ok: boolean }, string>({
      query: (id) => ({
        url: `/notifications/${id}/read`,
        method: "PATCH",
      }),
      invalidatesTags: ["Notification"],
    }),
    markAllRead: builder.mutation<{ ok: boolean; count: number }, void>({
      query: () => ({
        url: "/notifications/read-all",
        method: "POST",
      }),
      invalidatesTags: ["Notification"],
    }),
  }),
});

export const {
  useGetNotificationsQuery,
  useGetUnreadCountQuery,
  useMarkReadMutation,
  useMarkAllReadMutation,
} = notificationsApi;
