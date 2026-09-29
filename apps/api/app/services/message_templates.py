"""Locale-aware message templates (WhatsApp / email) — FC Phase 5."""
from __future__ import annotations

from typing import Optional

from app.services.i18n import normalize_locale


def whatsapp_quote_template(
    *,
    locale: str,
    first_name: str,
    amount_line: str,
    public_url: str,
    valid_until: str,
) -> str:
    loc = normalize_locale(locale)
    if loc == "hi":
        return (
            f"नमस्ते {first_name},\n\n"
            f"{amount_line}"
            f"अपना कोट सुरक्षित रूप से यहाँ देखें: {public_url}\n\n"
            f"कृपया ध्यान दें कि यह कोट {valid_until} तक मान्य है। "
            f"कोई प्रश्न हो तो बताएँ!\n\n"
            f"धन्यवाद।"
        )
    return (
        f"Hi {first_name},\n\n"
        f"{amount_line}"
        f"View your quote securely here: {public_url}\n\n"
        f"Please note this quote is valid until {valid_until}. "
        f"Let me know if you have any questions!\n\n"
        f"Thanks."
    )


def amount_line_for_locale(
    *,
    locale: str,
    display_cur: str,
    display_amt: float,
    charge: str,
    total_charge: float,
    fx_as_of_str: Optional[str],
) -> str:
    loc = normalize_locale(locale)
    if display_cur.upper() != charge.upper():
        fx_bit = fx_as_of_str or ("कोट निर्माण" if loc == "hi" else "quote creation")
        if loc == "hi":
            return (
                f"आपका यात्रा कोट लगभग {display_cur} {display_amt:,.2f} है "
                f"(भुगतान {charge} {total_charge:,.2f} में)।\n\n"
                f"FX दर दिनांक: {fx_bit}।\n\n"
            )
        return (
            f"Here is your travel quote for {display_cur} {display_amt:,.2f} "
            f"(approx; payment in {charge} {total_charge:,.2f}).\n\n"
            f"FX rate as of {fx_bit}.\n\n"
        )
    if loc == "hi":
        return f"आपका यात्रा कोट {charge} {total_charge:,.2f} का है।\n\n"
    return f"Here is your travel quote for {charge} {total_charge:,.2f}.\n\n"
