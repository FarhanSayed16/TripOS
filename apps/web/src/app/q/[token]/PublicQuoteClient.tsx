"use client";

import { useGetPublicQuoteQuery, useGetThemeQuery } from "@/lib/api/publicApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { format } from "date-fns";
import { hi as hiLocale, enIN } from "date-fns/locale";
import { Plane, Hotel, CheckCircle2, AlertCircle } from "lucide-react";
import { useState, useEffect } from "react";
import { formatMoney, formatPaiseAsMoney, fxFootnote } from "@/lib/money";
import { I18nProvider, normalizeLocale, useI18n } from "@/lib/i18n";

function PublicQuoteInner({ token }: { token: string }) {
  const { t, locale, dateLocale, setLocale } = useI18n();
  const { data: quote, isLoading, error } = useGetPublicQuoteQuery(token);
  const [domain, setDomain] = useState<string>("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      setDomain(window.location.hostname);
    }
  }, []);

  useEffect(() => {
    if (quote?.locale) {
      setLocale(normalizeLocale(quote.locale));
    }
  }, [quote?.locale, setLocale]);

  const isCustomDomain =
    domain &&
    domain !== "localhost" &&
    domain !== "127.0.0.1" &&
    !domain.includes("tripos.com");

  const { data: theme } = useGetThemeQuery(domain, {
    skip: !isCustomDomain,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-sand">
        {t("publicQuote.loading")}
      </div>
    );
  }

  if (error || !quote) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-sand p-4">
        <Card className="max-w-md w-full text-center p-8">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-ink mb-2">
            {t("publicQuote.unavailableTitle")}
          </h1>
          <p className="text-muted-foreground">{t("publicQuote.unavailableBody")}</p>
        </Card>
      </div>
    );
  }

  const isExpired =
    new Date() > new Date(quote.valid_until) ||
    quote.status === "expired" ||
    quote.status === "cancelled";
  const totalPaise = quote.items.reduce((sum, item) => sum + item.customer_total, 0);
  const totalDisplay = quote.items.reduce(
    (sum, item) => sum + (item.money?.display_amount ?? item.customer_total / 100),
    0
  );
  const displayCurrency =
    quote.display_currency || quote.items[0]?.money?.display_currency || "INR";
  const totalLabel = formatMoney(
    {
      currency: quote.charge_currency || "INR",
      amount: totalPaise / 100,
      display_currency: displayCurrency,
      display_amount: totalDisplay,
    },
    "INR",
    dateLocale
  );
  const note =
    quote.charge_note ||
    fxFootnote({
      charge_currency: quote.charge_currency,
      display_currency: quote.display_currency,
      fx_rate: quote.fx_rate,
      fx_as_of: quote.fx_as_of,
    });

  const agency = theme?.brand_name || quote.agency_name || "TripOS";
  const logoUrl = theme?.logo_url || quote.agency_logo_url;
  const primaryColor = theme?.primary_color || "#3A86FF";
  const buttonStyle = theme?.primary_color ? { backgroundColor: theme.primary_color } : {};
  const dfLocale = locale === "hi" ? hiLocale : enIN;
  const guaranteedDate = format(new Date(quote.valid_until), "MMM d, h:mm a", {
    locale: dfLocale,
  });

  return (
    <div
      className="min-h-screen bg-sand pb-24 md:pb-12"
      style={{ "--tw-ring-color": primaryColor } as React.CSSProperties}
    >
      <header className="bg-paper border-b border-line p-4 sticky top-0 z-10 shadow-sm">
        <div className="max-w-3xl mx-auto flex justify-between items-center gap-3">
          <div className="flex items-center gap-3 min-w-0">
            {logoUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={logoUrl} alt={agency} className="h-8 w-8 rounded object-cover" />
            ) : null}
            <div className="font-display text-xl tracking-tight text-ink truncate">{agency}</div>
          </div>
          <div className="text-sm font-medium bg-sand px-3 py-1 rounded-full shrink-0">
            {t("publicQuote.quoteLabel")} #{quote.id.split("-")[0].toUpperCase()}
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto p-4 mt-6 space-y-6">
        {isExpired && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg flex gap-3 items-start">
            <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
            <div>
              <p className="font-bold">{t("publicQuote.expiredTitle")}</p>
              <p className="text-sm mt-1">{t("publicQuote.expiredBody")}</p>
            </div>
          </div>
        )}

        {!isExpired && (
          <div className="bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded-lg flex gap-3 items-center">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <p className="text-sm font-medium">
              {t("publicQuote.guaranteedUntil", { date: guaranteedDate })}
            </p>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>{t("publicQuote.itinerary")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {quote.items.map((item) => {
              const data = item.sanitized_offer_data;
              return (
                <div
                  key={item.id}
                  className="p-4 rounded-lg border border-line bg-paper flex gap-4"
                >
                  <div className="bg-sand p-3 rounded-full h-fit">
                    {data.type === "flight" ? (
                      <Plane className="w-6 h-6 text-focus" />
                    ) : (
                      <Hotel className="w-6 h-6 text-focus" />
                    )}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-lg text-ink">
                      {data.title || t("publicQuote.travelService")}
                    </h3>
                    {data.description && (
                      <p className="text-sm text-muted-foreground mt-1">{data.description}</p>
                    )}
                    <div className="mt-4 pt-4 border-t border-line text-right">
                      <p className="font-bold text-xl text-ink">
                        {formatPaiseAsMoney(item.customer_total, {
                          currency: quote.charge_currency || "INR",
                          money: item.money,
                          locale: dateLocale,
                        })}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        <Card className="border-2 border-focus/20 shadow-md">
          <CardContent className="p-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-lg font-medium">{t("publicQuote.totalAmount")}</span>
              <span className="text-3xl font-bold text-focus">{totalLabel}</span>
            </div>
            {note && <p className="text-xs text-muted-foreground mb-6">{note}</p>}

            <div className="hidden md:block">
              {quote.payment_link_url ? (
                <a href={quote.payment_link_url} target="_blank" rel="noopener noreferrer">
                  <Button
                    className="w-full h-14 text-lg text-white transition-opacity hover:opacity-90"
                    style={buttonStyle}
                    disabled={isExpired}
                  >
                    {t("publicQuote.proceedPayment")}
                  </Button>
                </a>
              ) : (
                <Button className="w-full h-14 text-lg text-white" style={buttonStyle} disabled>
                  {t("publicQuote.paymentNotAvailable")}
                </Button>
              )}
              <p className="text-center text-xs text-muted-foreground/60 mt-3">
                {t("publicQuote.secureNote")}
              </p>
            </div>
          </CardContent>
        </Card>
      </main>

      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-paper border-t border-line p-4 shadow-[0_-4px_10px_rgba(0,0,0,0.05)] z-20">
        <div className="flex justify-between items-center mb-3">
          <span className="text-sm font-medium text-muted-foreground">{t("publicQuote.total")}</span>
          <span className="text-xl font-bold text-ink">{totalLabel}</span>
        </div>
        {quote.payment_link_url ? (
          <a href={quote.payment_link_url} target="_blank" rel="noopener noreferrer">
            <Button
              className="w-full h-12 text-base text-white transition-opacity hover:opacity-90"
              style={buttonStyle}
              disabled={isExpired}
            >
              {t("publicQuote.proceedPayment")}
            </Button>
          </a>
        ) : (
          <Button className="w-full h-12 text-base text-white" style={buttonStyle} disabled>
            {t("publicQuote.paymentNotAvailableShort")}
          </Button>
        )}
      </div>
    </div>
  );
}

export default function PublicQuoteClient({ token }: { token: string }) {
  // Nested provider so quote.locale can remount catalogs without affecting agent shell
  return (
    <I18nProvider initialLocale="en">
      <PublicQuoteInner token={token} />
    </I18nProvider>
  );
}
