"use client";

import Link from "next/link";
import { Settings, Building, Users, Bell, Palette } from "lucide-react";

export function ComingSoon({
  title,
  description,
  phase,
}: {
  title: string;
  description?: string;
  phase?: string;
}) {
  return (
    <div className="empty-state-container animate-scale-in">
      <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-teal/10 to-teal-dark/10 flex items-center justify-center mb-2">
        <Settings className="w-7 h-7 text-teal/40" />
      </div>
      <h1 className="page-title text-xl">{title}</h1>
      <p className="text-sm text-muted-foreground max-w-md mt-1">
        {description || "This feature is coming soon and will be available in a future update."}
      </p>
      {phase ? (
        <span className="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-teal/5 text-teal border border-teal/15 mt-2">
          Coming in {phase}
        </span>
      ) : null}
      <Link
        href="/app"
        className="mt-4 inline-flex items-center gap-2 btn-gradient rounded-lg px-5 py-2.5 text-sm font-medium text-white no-underline"
      >
        Back to Home
      </Link>
    </div>
  );
}
