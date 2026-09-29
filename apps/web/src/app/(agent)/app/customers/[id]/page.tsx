"use client";

import { use } from "react";
import Link from "next/link";
import { useGetCustomerQuery, useGetCustomerTimelineQuery } from "@/lib/api/crmApi";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Mail, Phone, Calendar, Clock, Loader2, StickyNote, MessageCircle, ArrowRight, ExternalLink } from "lucide-react";
import { format } from "date-fns";
import { Badge } from "@/components/ui/badge";

function waMeUrl(phoneE164: string): string {
  const digits = phoneE164.replace(/\D/g, "");
  return `https://wa.me/${digits}`;
}

export default function CustomerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;

  const { data: customer, isLoading: isLoadingCustomer } = useGetCustomerQuery(id);
  const { data: timeline, isLoading: isLoadingTimeline } = useGetCustomerTimelineQuery(id);

  if (isLoadingCustomer) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-teal" />
      </div>
    );
  }

  if (!customer) {
    return (
      <div className="text-center py-24 bg-surface/30 rounded-xl border border-line">
        <h2 className="text-xl font-semibold text-ink mb-2">Customer Not Found</h2>
        <Link href="/app/customers" className="text-teal hover:underline inline-flex items-center">
          <ArrowLeft className="w-4 h-4 mr-2" /> Return to Customers
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/app/customers">
          <Button variant="outline" size="icon" className="w-9 h-9 rounded-full bg-paper shadow-sm">
            <ArrowLeft className="w-4 h-4 text-muted-foreground" />
          </Button>
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-ink">
              {customer.first_name} {customer.last_name}
            </h1>
            <Badge variant="outline" className="bg-sand/30 font-medium border-line text-muted-foreground">Active</Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">Customer Profile & History</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 space-y-6">
          <Card className="bg-paper border-line shadow-sm">
            <CardHeader className="bg-surface/50 border-b border-line pb-4">
              <CardTitle className="text-lg">Contact Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5 pt-6">
              <div className="flex items-center gap-4 text-sm group">
                <div className="w-10 h-10 rounded-full bg-teal/10 flex items-center justify-center flex-shrink-0 group-hover:bg-teal group-hover:text-white transition-colors text-teal">
                  <Phone className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-muted-foreground text-xs font-medium uppercase tracking-wider mb-0.5">Phone</p>
                  <p className="font-semibold text-ink font-mono tracking-tight">{customer.phone_e164}</p>
                </div>
              </div>

              <div className="flex items-center gap-4 text-sm group">
                <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-500 group-hover:text-white transition-colors text-blue-500">
                  <Mail className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-muted-foreground text-xs font-medium uppercase tracking-wider mb-0.5">Email</p>
                  <p className="font-medium text-ink">{customer.email || "Not provided"}</p>
                </div>
              </div>

              <div className="flex items-center gap-4 text-sm group">
                <div className="w-10 h-10 rounded-full bg-sand flex items-center justify-center flex-shrink-0 text-muted-foreground group-hover:bg-line transition-colors">
                  <Calendar className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-muted-foreground text-xs font-medium uppercase tracking-wider mb-0.5">Added On</p>
                  <p className="font-medium text-ink">
                    {format(new Date(customer.created_at), "MMM d, yyyy")}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <a
            href={waMeUrl(customer.phone_e164)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex w-full items-center justify-center gap-2 rounded-lg h-11 px-4 text-sm font-medium bg-[#25D366] hover:bg-[#1DA851] text-white shadow-sm transition-colors"
          >
            <MessageCircle className="w-5 h-5" />
            Message on WhatsApp
          </a>
        </div>

        <div className="md:col-span-2 space-y-6">
          <Card className="bg-paper border-line shadow-sm min-h-[500px]">
            <CardHeader className="border-b border-line pb-4 bg-surface/50">
              <CardTitle className="text-lg">Activity Timeline</CardTitle>
              <CardDescription>History of quotes, bookings, and interactions.</CardDescription>
            </CardHeader>
            <CardContent className="pt-8 px-8">
              {isLoadingTimeline ? (
                <div className="flex justify-center p-12">
                  <Loader2 className="w-6 h-6 animate-spin text-teal" />
                </div>
              ) : timeline && timeline.length > 0 ? (
                <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-line">
                  {timeline.map(
                    (item: {
                      id: string;
                      type: string;
                      title: string;
                      description?: string | null;
                      created_at: string;
                      reference_id?: string;
                    }) => (
                      <div
                        key={item.id}
                        className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active"
                      >
                        <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-paper shadow-sm shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10
                          ${item.type === 'booking' ? 'bg-emerald-500 text-white' : 
                            item.type === 'quote' ? 'bg-blue-500 text-white' : 
                            'bg-surface border-line text-muted-foreground'}`
                        }>
                          {item.type === "note" && <StickyNote className="w-4 h-4" />}
                          {item.type === "quote" && <Clock className="w-4 h-4" />}
                          {item.type === "booking" && <Calendar className="w-4 h-4" />}
                        </div>
                        <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-line/60 bg-surface shadow-sm hover:shadow-md transition-shadow">
                          <div className="flex items-center justify-between space-x-2 mb-2">
                            <div className="font-semibold text-ink flex items-center gap-2">
                              {item.title}
                              {item.type === 'booking' && <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Confirmed</Badge>}
                              {item.type === 'quote' && <Badge className="bg-blue-50 text-blue-700 border-blue-200">Sent</Badge>}
                            </div>
                            <time className="text-xs font-medium text-muted-foreground">
                              {format(new Date(item.created_at), "MMM d, h:mm a")}
                            </time>
                          </div>
                          {item.description && (
                            <div className="text-sm text-muted-foreground mb-3">{item.description}</div>
                          )}
                          
                          {(item.type === "quote" || item.type === "booking") && item.reference_id && (
                            <div className="pt-3 border-t border-line mt-2">
                              <Link href={`/app/quotes/${item.reference_id}`} className="inline-flex items-center text-xs font-medium text-teal hover:text-teal-dark hover:underline">
                                View Details <ArrowRight className="w-3 h-3 ml-1" />
                              </Link>
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  )}
                </div>
              ) : (
                <div className="text-center py-20 bg-surface/30 rounded-xl border border-line border-dashed">
                  <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                    <div className="h-12 w-12 rounded-full bg-paper border border-line flex items-center justify-center shadow-sm mb-4">
                      <Clock className="w-5 h-5 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-ink mb-1">No activity yet</h3>
                    <p className="text-sm text-muted-foreground">Quotes, bookings, and notes will appear here on this timeline.</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
