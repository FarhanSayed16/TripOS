import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { BaseQueryFn, FetchArgs, FetchBaseQueryError } from '@reduxjs/toolkit/query';
import { getApiLocale } from '@/lib/localeStore';

let accessToken: string | null = null;
let refreshPromise: Promise<boolean> | null = null;

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

export const getAccessToken = () => accessToken;

const rawBaseQuery = fetchBaseQuery({
  baseUrl: '/api/v1',
  credentials: 'include',
  prepareHeaders: (headers) => {
    if (accessToken) {
      headers.set('authorization', `Bearer ${accessToken}`);
    }
    headers.set('Accept-Language', getApiLocale());
    return headers;
  },
});

async function tryRefresh(): Promise<boolean> {
  try {
    const res = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) {
      accessToken = null;
      return false;
    }
    const data = await res.json();
    accessToken = data.access_token ?? null;
    return !!accessToken;
  } catch {
    accessToken = null;
    return false;
  }
}

const baseQueryWithReauth: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (
  args,
  api,
  extraOptions
) => {
  let result = await rawBaseQuery(args, api, extraOptions);

  if (result.error && result.error.status === 401) {
    const url = typeof args === 'string' ? args : args.url;
    // Avoid refresh loops on auth endpoints
    if (url.includes('/auth/refresh') || url.includes('/auth/login') || url.includes('/auth/logout')) {
      return result;
    }

    if (!refreshPromise) {
      refreshPromise = tryRefresh().finally(() => {
        refreshPromise = null;
      });
    }
    const ok = await refreshPromise;
    if (ok) {
      result = await rawBaseQuery(args, api, extraOptions);
    }
  }

  return result;
};

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Customer', 'CustomerTimeline', 'Payment', 'Quote', 'QuoteAudit', 'Booking', 'Organization', 'DeadLetter', 'Package', 'Wallet', 'Commission', 'Document', 'FollowUp', 'Analytics', 'Network', 'Domains', 'Suppliers', 'FxRates', 'Partners'],
  endpoints: () => ({}),
});
