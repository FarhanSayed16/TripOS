"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, FileText, MessageCircle, CreditCard, CheckCircle, ArrowRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

const steps = [
  { icon: Search, label: "Search", description: "Find flights & hotels from multiple suppliers in one place." },
  { icon: FileText, label: "Quote", description: "Build beautifully branded quotes with your dynamic markup." },
  { icon: MessageCircle, label: "Share", description: "Send directly via WhatsApp with one-click sharing." },
  { icon: CreditCard, label: "Collect", description: "Get paid instantly with auto-generated payment links." },
  { icon: CheckCircle, label: "Book", description: "Confirm bookings automatically upon payment capture." },
];

export default function MarketingPage() {
  const [email, setEmail] = useState("");
  const [joined, setJoined] = useState(false);

  const handleJoinWaitlist = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setJoined(true);
    // Real implementation would hit an API
  };

  return (
    <div className="relative flex-1 flex flex-col items-center overflow-hidden w-full">
      {/* ── Ambient Background ── */}
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -10%, hsl(173 58% 39% / 0.12), transparent 60%), radial-gradient(ellipse 40% 30% at 80% 20%, hsl(190 60% 32% / 0.06), transparent), linear-gradient(180deg, hsl(210 20% 98%) 0%, hsl(0 0% 100%) 60%)",
        }}
      />

      {/* ── Decorative grid ── */}
      <div
        className="pointer-events-none absolute inset-0 -z-10 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(hsl(220 20% 14%) 1px, transparent 1px), linear-gradient(90deg, hsl(220 20% 14%) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />

      {/* ── Hero ── */}
      <section className="w-full flex flex-col items-center text-center px-6 pt-20 pb-16 sm:pt-28 sm:pb-24 max-w-4xl mx-auto">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal/5 border border-teal/15 text-xs font-semibold text-teal-dark mb-8 shadow-sm">
          <span className="h-2 w-2 rounded-full bg-teal animate-pulse" />
          TripOS 2.0 is now in Private Beta
        </div>

        {/* Headline */}
        <h1 className="font-display text-5xl sm:text-6xl md:text-7xl tracking-tight text-ink leading-[1.05] font-extrabold">
          The operating system for{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-dark to-teal">
            modern travel
          </span>{" "}
          agencies
        </h1>

        {/* Sub */}
        <p className="mt-8 text-lg sm:text-xl text-ink/70 max-w-2xl leading-relaxed">
          Search inventory, draft stunning quotes, collect payments, and automatically issue tickets — all from one premium workspace.
        </p>

        {/* CTAs / Waitlist Inline Form */}
        <div className="mt-10 w-full max-w-md mx-auto">
          {joined ? (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-xl flex items-center justify-center gap-2 shadow-sm animate-in zoom-in-95">
              <Check className="w-5 h-5 text-emerald-600" />
              <span className="font-semibold">You're on the list! Keep an eye on your inbox.</span>
            </div>
          ) : (
            <form onSubmit={handleJoinWaitlist} className="flex flex-col sm:flex-row gap-3">
              <input
                type="email"
                required
                placeholder="Enter your work email"
                className="flex-1 h-12 px-4 rounded-xl border border-line bg-paper shadow-sm focus:ring-2 focus:ring-teal/20 focus:border-teal outline-none transition-all placeholder:text-muted-foreground text-ink"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <Button type="submit" className="h-12 px-6 rounded-xl bg-teal hover:bg-teal-dark text-white font-semibold shadow-sm transition-all gap-2">
                Join Waitlist <ArrowRight className="w-4 h-4" />
              </Button>
            </form>
          )}
          <p className="text-xs text-muted-foreground mt-3 text-center">Already have an account? <Link href="/login" className="text-teal font-medium hover:underline">Sign in here</Link></p>
        </div>
      </section>

      {/* ── Full-bleed Hero Image (§12.2) ── */}
      <section className="w-full relative h-[280px] sm:h-[360px] -mt-4 mb-8 overflow-hidden">
        <img
          src="/hero-india.jpg"
          alt="India travel — from the Taj Mahal to tropical beaches"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-paper via-transparent to-paper" />
        <div className="absolute inset-0 bg-gradient-to-r from-teal-dark/20 to-transparent" />
      </section>

      {/* ── App Preview Mockup ── */}
      <section className="w-full max-w-5xl mx-auto px-6 pb-20 z-10">
        <div className="relative rounded-2xl border border-line/60 bg-paper/50 p-2 shadow-2xl backdrop-blur-sm -rotate-1 hover:rotate-0 transition-transform duration-500 ease-out">
          <div className="rounded-xl overflow-hidden border border-line/80 bg-paper shadow-inner relative flex flex-col">
            {/* Mock Window Chrome */}
            <div className="h-10 bg-surface border-b border-line flex items-center px-4 gap-2">
              <div className="w-3 h-3 rounded-full bg-coral/80"></div>
              <div className="w-3 h-3 rounded-full bg-amber-400"></div>
              <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
              <div className="mx-auto flex items-center h-6 px-24 bg-paper border border-line rounded-md text-[10px] text-muted-foreground/50 font-medium">app.tripos.com</div>
            </div>
            
            {/* Mock App Content */}
            <div className="p-6 bg-sand/30 flex gap-6 h-[400px]">
              {/* Sidebar */}
              <div className="w-48 bg-paper border border-line rounded-lg p-4 space-y-3">
                <div className="h-8 bg-surface rounded w-3/4 mb-6"></div>
                <div className="h-4 bg-surface rounded w-full"></div>
                <div className="h-4 bg-teal/10 rounded w-5/6"></div>
                <div className="h-4 bg-surface rounded w-4/5"></div>
                <div className="h-4 bg-surface rounded w-full"></div>
              </div>
              
              {/* Main Content */}
              <div className="flex-1 space-y-6">
                <div className="flex justify-between items-center">
                  <div className="space-y-2">
                    <div className="h-6 w-48 bg-paper border border-line shadow-sm rounded-md"></div>
                    <div className="h-4 w-32 bg-surface rounded"></div>
                  </div>
                  <div className="h-10 w-32 bg-teal rounded-md shadow-sm"></div>
                </div>
                
                {/* Search Cards */}
                <div className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-20 bg-paper border border-line shadow-sm rounded-xl p-4 flex justify-between items-center">
                      <div className="flex gap-4 items-center">
                        <div className="w-12 h-12 rounded-full bg-surface"></div>
                        <div className="space-y-2">
                          <div className="h-4 w-24 bg-surface rounded"></div>
                          <div className="h-3 w-16 bg-surface rounded"></div>
                        </div>
                      </div>
                      <div className="h-8 w-24 bg-surface rounded"></div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Workflow Steps / Features ── */}
      <section className="w-full bg-paper border-t border-line py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-ink">Everything you need to scale</h2>
            <p className="mt-4 text-muted-foreground max-w-xl mx-auto">Replace a dozen fragmented tools with one cohesive platform designed specifically for travel professionals.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
            {steps.map((step, i) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.label}
                  className="bg-paper border border-line rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group"
                >
                  <div className="absolute top-0 right-0 w-24 h-24 bg-teal/5 rounded-bl-full -z-10 group-hover:bg-teal/10 transition-colors"></div>
                  <div className="h-12 w-12 rounded-xl bg-teal/10 flex items-center justify-center mb-5 border border-teal/20">
                    <Icon className="h-6 w-6 text-teal" />
                  </div>
                  <h3 className="text-lg font-bold text-ink mb-2">{step.label}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {step.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Trust strip ── */}
      <section className="w-full bg-surface border-t border-line py-12 text-center">
        <p className="text-xs uppercase tracking-[0.15em] font-bold text-muted-foreground">
          Built for travel agencies across India
        </p>
      </section>
    </div>
  );
}
