"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import en from "@/messages/en.json";
import hi from "@/messages/hi.json";
import {
  getApiLocale,
  normalizeApiLocale,
  setApiLocale,
  type ApiLocale,
} from "@/lib/localeStore";

export type Locale = ApiLocale;

const catalogs: Record<Locale, Record<string, unknown>> = {
  en: en as Record<string, unknown>,
  hi: hi as Record<string, unknown>,
};

type I18nContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  dateLocale: string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

function lookup(obj: Record<string, unknown>, path: string): string | undefined {
  const parts = path.split(".");
  let cur: unknown = obj;
  for (const p of parts) {
    if (cur == null || typeof cur !== "object") return undefined;
    cur = (cur as Record<string, unknown>)[p];
  }
  return typeof cur === "string" ? cur : undefined;
}

function interpolate(template: string, vars?: Record<string, string | number>) {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, k: string) =>
    vars[k] != null ? String(vars[k]) : `{${k}}`
  );
}

export const normalizeLocale = normalizeApiLocale;

export { getApiLocale, setApiLocale };

export function I18nProvider({
  children,
  initialLocale = "en",
}: {
  children: ReactNode;
  initialLocale?: Locale;
}) {
  const [locale, setLocaleState] = useState<Locale>(normalizeLocale(initialLocale));

  const setLocale = useCallback((next: Locale) => {
    const loc = normalizeLocale(next);
    setLocaleState(loc);
    setApiLocale(loc);
  }, []);

  useEffect(() => {
    setApiLocale(locale);
  }, [locale]);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      const catalog = catalogs[locale] || catalogs.en;
      const raw = lookup(catalog, key) ?? lookup(catalogs.en, key) ?? key;
      return interpolate(raw, vars);
    },
    [locale]
  );

  const value = useMemo(
    () => ({
      locale,
      setLocale,
      t,
      dateLocale: locale === "hi" ? "hi-IN" : "en-IN",
    }),
    [locale, setLocale, t]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return ctx;
}

export function useI18nOptional(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (ctx) return ctx;
  return {
    locale: "en",
    setLocale: () => undefined,
    t: (key, vars) => interpolate(lookup(catalogs.en, key) ?? key, vars),
    dateLocale: "en-IN",
  };
}
