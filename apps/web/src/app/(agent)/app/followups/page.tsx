"use client";

import { useState } from "react";
import { 
  useGetFollowUpsQuery, 
  useSnoozeFollowUpMutation, 
  useDismissFollowUpMutation,
  useSendReminderMutation 
} from "@/lib/api/followupsApi";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MessageCircle, Clock, X, Bell } from "lucide-react";
import Link from "next/link";

export default function FollowUpsPage() {
  const { data: followups, isLoading } = useGetFollowUpsQuery();
  const [snooze] = useSnoozeFollowUpMutation();
  const [dismiss] = useDismissFollowUpMutation();
  const [sendReminder] = useSendReminderMutation();

  const handleSnooze = async (id: string, hours: number) => {
    await snooze({ id, hours });
  };

  const handleDismiss = async (id: string) => {
    if (confirm("Dismiss this follow-up?")) {
      await dismiss(id);
    }
  };

  const handleSendReminder = async (id: string) => {
    try {
      const res = await sendReminder(id).unwrap();
      window.open(res.wa_link, "_blank");
    } catch (err: any) {
      alert("Failed to send reminder.");
    }
  };

  const formatCurrency = (paise: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(paise / 100);
  };

  if (isLoading) return (
    <div className="flex items-center justify-center p-12">
      <div className="h-8 w-8 rounded-full border-2 border-teal border-t-transparent animate-spin" />
    </div>
  );

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="page-title flex items-center gap-3">
          <Bell className="w-6 h-6 text-teal" />
          Follow-ups
        </h1>
        <p className="page-subtitle">Unpaid quotes that need your attention.</p>
      </div>

      <div className="space-y-4">
        {(!followups || followups.length === 0) && (
          <div className="p-20 text-center bg-paper/50 rounded-xl">
            <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
              <div className="h-12 w-12 rounded-full bg-paper border border-line/50 flex items-center justify-center shadow-sm mb-4">
                <Bell className="w-5 h-5 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold text-ink mb-1">All caught up!</h3>
              <p className="text-sm text-muted-foreground">No pending follow-ups at the moment.</p>
            </div>
          </div>
        )}

        {followups?.map((f) => (
          <Card key={f.id} className="hover:shadow-sm transition-shadow">
            <CardContent className="p-4 flex items-center justify-between">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-lg text-ink">{f.customer_name}</span>
                  <Badge variant={f.type === "auto_48h" ? "destructive" : "secondary"}>
                    {f.hours_overdue}h Overdue
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>{formatCurrency(f.amount_paise || 0)}</span>
                  <Link href={`/app/quotes/${f.quote_id}`} className="text-brand_primary hover:underline">
                    View Quote
                  </Link>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleSnooze(f.id, 24)}
                  className="flex items-center gap-1.5 px-4 py-2 border border-line bg-paper hover:bg-black/5 dark:hover:bg-white/5 rounded-full text-sm font-medium transition-colors shadow-sm"
                  title="Snooze for 24h"
                >
                  <Clock className="w-4 h-4" />
                  Snooze
                </button>
                <button
                  onClick={() => handleSendReminder(f.id)}
                  className="flex items-center gap-1.5 px-5 py-2 bg-[#25D366] hover:bg-[#128C7E] text-white rounded-full text-sm font-medium transition-colors shadow-sm active:scale-95"
                >
                  <MessageCircle className="w-4 h-4" />
                  WhatsApp
                </button>
                <button
                  onClick={() => handleDismiss(f.id)}
                  className="p-2 text-gray-400 hover:text-red-500 rounded-md hover:bg-red-50 transition-colors"
                  title="Dismiss"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
