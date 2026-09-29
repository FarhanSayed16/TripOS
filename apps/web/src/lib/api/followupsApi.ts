import { apiSlice } from "../apiSlice";

export interface FollowUp {
  id: string;
  quote_id: string;
  organization_id: string;
  type: string;
  status: string;
  message: string | null;
  snoozed_until: string | null;
  created_at: string;
  
  quote_public_token: string | null;
  customer_name: string | null;
  amount_paise: number | null;
  hours_overdue: number | null;
}

export const followupsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getFollowUps: builder.query<FollowUp[], void>({
      query: () => "/followups",
      providesTags: ["FollowUp"],
    }),
    snoozeFollowUp: builder.mutation<FollowUp, { id: string; hours: number }>({
      query: ({ id, hours }) => ({
        url: `/followups/${id}/snooze`,
        method: "POST",
        body: { hours },
      }),
      invalidatesTags: ["FollowUp"],
    }),
    dismissFollowUp: builder.mutation<FollowUp, string>({
      query: (id) => ({
        url: `/followups/${id}/dismiss`,
        method: "POST",
      }),
      invalidatesTags: ["FollowUp"],
    }),
    sendReminder: builder.mutation<{ status: string; wa_link: string }, string>({
      query: (id) => ({
        url: `/followups/${id}/send-reminder`,
        method: "POST",
      }),
      invalidatesTags: ["FollowUp"],
    }),
  }),
});

export const {
  useGetFollowUpsQuery,
  useSnoozeFollowUpMutation,
  useDismissFollowUpMutation,
  useSendReminderMutation,
} = followupsApi;
