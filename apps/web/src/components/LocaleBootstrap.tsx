"use client";

import { useEffect } from "react";
import { I18nProvider, normalizeLocale, setApiLocale } from "@/lib/i18n";
import { useAuth } from "@/contexts/AuthContext";
import { useGetMeQuery } from "@/lib/api/authApi";
import { useGetMyOrganizationQuery } from "@/lib/api/orgApi";

/**
 * Resolves user.locale → org.default_locale → en and feeds I18nProvider.
 * Public/unauth pages stay on default en until quote locale is applied locally.
 */
export function LocaleBootstrap({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const { data: me } = useGetMeQuery(undefined, { skip: !isAuthenticated });
  const { data: org } = useGetMyOrganizationQuery(undefined, {
    skip: !isAuthenticated || !me?.active_organization_id,
  });

  const locale = normalizeLocale(
    isAuthenticated ? me?.locale || org?.default_locale || "en" : "en"
  );

  useEffect(() => {
    setApiLocale(locale);
  }, [locale]);

  return (
    <I18nProvider initialLocale={locale} key={locale}>
      {children}
    </I18nProvider>
  );
}
