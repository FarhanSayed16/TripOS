/** FC Phase 4 — display money helpers (display ≠ charge). */

export type MoneyDisplay = {
  currency: string;
  amount: number;
  display_currency: string;
  display_amount: number;
  fx_rate?: number;
  fx_as_of?: string | null;
  fx_source?: string | null;
};

export function formatMajor(
  amount: number,
  currency: string,
  locale = "en-IN"
): string {
  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: currency || "INR",
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toLocaleString(locale, { maximumFractionDigits: 2 })}`;
  }
}

export function formatMoney(
  money?: MoneyDisplay | null,
  fallbackCurrency = "INR",
  locale = "en-IN"
): string {
  if (!money) return formatMajor(0, fallbackCurrency, locale);
  return formatMajor(
    money.display_amount,
    money.display_currency || fallbackCurrency,
    locale
  );
}

export function formatPaiseAsMoney(
  paise: number,
  opts?: { currency?: string; money?: MoneyDisplay | null; locale?: string }
): string {
  const locale = opts?.locale || "en-IN";
  if (opts?.money) return formatMoney(opts.money, opts.currency || "INR", locale);
  return formatMajor(paise / 100, opts?.currency || "INR", locale);
}

export function fxFootnote(opts: {
  charge_currency?: string | null;
  display_currency?: string | null;
  fx_rate?: number | null;
  fx_as_of?: string | null;
}): string | null {
  const charge = (opts.charge_currency || "INR").toUpperCase();
  const display = (opts.display_currency || charge).toUpperCase();
  if (charge === display) return null;
  const when = opts.fx_as_of
    ? new Date(opts.fx_as_of).toLocaleString()
    : "quote creation";
  const rate =
    opts.fx_rate != null ? `1 ${charge} ≈ ${opts.fx_rate} ${display}. ` : "";
  return `${rate}Display only — payment is collected in ${charge}. Rate as of ${when}.`;
}
