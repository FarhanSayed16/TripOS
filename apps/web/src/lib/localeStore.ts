/** Tiny store so apiSlice can set Accept-Language without importing React i18n. */

export type ApiLocale = "en" | "hi";

let apiLocale: ApiLocale = "en";

export function getApiLocale(): ApiLocale {
  return apiLocale;
}

export function setApiLocale(locale: ApiLocale) {
  apiLocale = locale === "hi" ? "hi" : "en";
  if (typeof document !== "undefined") {
    document.documentElement.lang = apiLocale;
  }
}

export function normalizeApiLocale(value?: string | null): ApiLocale {
  const v = (value || "").toLowerCase().split("-")[0];
  return v === "hi" ? "hi" : "en";
}
