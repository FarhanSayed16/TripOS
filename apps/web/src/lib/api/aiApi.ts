import { apiSlice } from "../apiSlice";

export interface ParsedIntent {
  type: string;
  origin: string | null;
  destination: string | null;
  departure_date: string | null;
  return_date: string | null;
  passengers: number;
  budget_max: number | null;
  raw_message: string;
}

export interface QuoteDraft {
  selected_offer_ids: string[];
  summary: string;
  suggested_markup_paise: number;
}

export interface SearchAndDraftResponse {
  intent: ParsedIntent;
  search_results: any[];
  draft: QuoteDraft;
}

export const aiApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    parseIntent: builder.mutation<ParsedIntent, string>({
      query: (message) => ({
        url: "/ai/parse-intent",
        method: "POST",
        body: { message },
      }),
    }),
    searchAndDraft: builder.mutation<SearchAndDraftResponse, string>({
      query: (message) => ({
        url: "/ai/search-and-draft",
        method: "POST",
        body: { message },
      }),
    }),
  }),
});

export const {
  useParseIntentMutation,
  useSearchAndDraftMutation,
} = aiApi;
