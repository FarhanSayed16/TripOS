"use client";

import { use } from "react";
import Link from "next/link";
import { useGetPublicQuoteQuery } from "@/lib/api/publicApi";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, Clock, AlertCircle, CreditCard, Loader2 } from "lucide-react";

export default function QuoteStatusPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = use(params);
  const { data: quote, isLoading, error, refetch, isFetching } = useGetPublicQuoteQuery(token);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-sand">
        <Loader2 className="w-8 h-8 animate-spin text-focus" />
      </div>
    );
  }

  if (error || !quote) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-sand p-4">
        <Card className="max-w-md w-full text-center p-8">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h1 className="text-xl font-bold mb-2">Status unavailable</h1>
          <p className="text-muted-foreground mb-4">We could not find this quote.</p>
          <Link href={`/q/${token}`}>
            <Button variant="outline">Back to quote</Button>
          </Link>
        </Card>
      </div>
    );
  }

  const agency = quote.agency_name || "your travel agent";
  const paymentStatus = quote.payment_status;
  const bookingStatus = quote.booking_status;

  let icon = <Clock className="w-12 h-12 text-focus" />;
  let title = "Payment pending";
  let body = `Your quote with ${agency} is waiting for payment. If you already paid, refresh in a moment.`;

  if (quote.status === "paid" || paymentStatus === "captured") {
    if (bookingStatus === "confirmed") {
      icon = <CheckCircle2 className="w-12 h-12 text-green-500" />;
      title = "Booking confirmed";
      body = `Payment received and booking confirmed. ${agency} will share your travel details shortly.`;
    } else if (bookingStatus === "failed") {
      icon = <AlertCircle className="w-12 h-12 text-amber-500" />;
      title = "Payment received — booking needs attention";
      body = `We received your payment. ${agency} is resolving the booking with the supplier. You do not need to pay again.`;
    } else {
      icon = <CreditCard className="w-12 h-12 text-green-500" />;
      title = "Payment received";
      body = `Thanks — payment is confirmed. ${agency} is confirming your booking with the supplier.`;
    }
  } else if (quote.status === "expired" || quote.status === "cancelled") {
    icon = <AlertCircle className="w-12 h-12 text-red-400" />;
    title = "Quote no longer active";
    body = `This quote is ${quote.status}. Please contact ${agency} for a new quote.`;
  } else if (paymentStatus === "failed") {
    icon = <AlertCircle className="w-12 h-12 text-red-400" />;
    title = "Payment failed";
    body = `The payment did not complete. You can return to the quote and try again, or contact ${agency}.`;
  }

  return (
    <div className="min-h-screen bg-sand flex flex-col items-center justify-center p-4">
      <Card className="max-w-md w-full border border-line shadow-sm">
        <CardContent className="pt-10 pb-8 px-6 flex flex-col items-center text-center">
          <div className="mb-6">{icon}</div>
          <h1 className="text-2xl font-bold text-ink mb-2">{title}</h1>
          <p className="text-muted-foreground mb-8 leading-relaxed">{body}</p>
          <div className="flex flex-col sm:flex-row gap-2 w-full">
            <Button
              variant="outline"
              className="w-full"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              {isFetching ? <Loader2 className="w-4 h-4 animate-spin" /> : "Refresh status"}
            </Button>
            <Link href={`/q/${token}`} className="w-full">
              <Button className="w-full bg-focus hover:bg-focus/90">View quote</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
