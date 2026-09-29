import { Metadata, ResolvingMetadata } from "next";
import PublicQuoteClient from "./PublicQuoteClient";

type Props = {
  params: Promise<{ token: string }>;
};

function apiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  return `${raw.replace(/\/$/, "")}/api/v1`;
}

export async function generateMetadata(
  { params }: Props,
  _parent: ResolvingMetadata
): Promise<Metadata> {
  const resolvedParams = await params;

  try {
    const res = await fetch(`${apiBase()}/public/quotes/${resolvedParams.token}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) throw new Error("Not found");
    const quote = await res.json();

    const total =
      quote.items.reduce((sum: number, item: { customer_total: number }) => sum + item.customer_total, 0) /
      100;
    const agency = quote.agency_name || "TripOS";
    const firstTitle = quote.items?.[0]?.sanitized_offer_data?.title;
    const description = firstTitle
      ? `${firstTitle} · ₹${total.toLocaleString()}`
      : `Travel quote total ₹${total.toLocaleString()}. Valid until ${new Date(quote.valid_until).toLocaleDateString()}.`;

    return {
      title: `Travel Quote from ${agency}`,
      description,
      openGraph: {
        title: `Travel Quote from ${agency}`,
        description,
      },
    };
  } catch {
    return {
      title: "Quote Unavailable | TripOS",
      description: "This quote is no longer available or has expired.",
    };
  }
}

export default async function PublicQuotePage({ params }: Props) {
  const resolvedParams = await params;
  return <PublicQuoteClient token={resolvedParams.token} />;
}
