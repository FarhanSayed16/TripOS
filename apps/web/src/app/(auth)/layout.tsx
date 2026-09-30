import Link from "next/link";
import { PageTransition } from "@/components/PageTransition";
import { Search, FileText, MessageCircle, CreditCard, CheckCircle } from "lucide-react";
import { LottieWorldMap, LottieGlobe } from "./LottieBackground";

const features = [
  { icon: Search, text: "Multi-supplier inventory search" },
  { icon: FileText, text: "Branded quotes with your markup" },
  { icon: MessageCircle, text: "WhatsApp sharing in one click" },
  { icon: CreditCard, text: "Automatic payment collection" },
  { icon: CheckCircle, text: "Real-time booking confirmation" },
];

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">
      {/* ── Brand Panel (desktop only) ── */}
      <div className="hidden lg:flex lg:w-[480px] xl:w-[520px] flex-col justify-between p-10 relative overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 -z-10 bg-ink overflow-hidden">
          {/* Abstract glowing orbs */}
          <div className="absolute -top-[20%] -left-[10%] w-[70%] h-[70%] rounded-full bg-teal-500/20 blur-[120px] mix-blend-screen" />
          <div className="absolute top-[40%] -right-[20%] w-[60%] h-[60%] rounded-full bg-teal/15 blur-[100px] mix-blend-screen" />
          <div className="absolute -bottom-[20%] left-[20%] w-[80%] h-[80%] rounded-full bg-teal-dark/20 blur-[120px] mix-blend-screen" />

          {/* World Map watermark — faint, behind everything */}
          <LottieWorldMap />

          {/* Subtle noise texture */}
          <div className="absolute inset-0 opacity-[0.04] z-10 pointer-events-none" style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E')" }} />
        </div>

        {/* ── Zone 1: Logo ── */}
        <div className="relative z-20 flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-teal to-teal-dark flex items-center justify-center">
            <span className="text-white text-sm font-bold">T</span>
          </div>
          <span className="font-display text-2xl tracking-tight text-white">
            Trip<span className="text-white/50">OS</span>
          </span>
        </div>

        {/* ── Zone 2: Content (headline + features) ── */}
        <div className="space-y-10 relative z-20">
          <div>
            <h2 className="font-display text-[2.75rem] tracking-tight text-white leading-[1.15] font-medium">
              The operating system for modern travel agencies
            </h2>
            <p className="mt-5 text-[15px] text-white/60 leading-relaxed max-w-[420px]">
              Manage your entire travel business from one elegant platform. Search, quote, collect, and book — all without leaving your desk.
            </p>
          </div>

          {/* Feature List */}
          <div className="space-y-4">
            {features.map((f) => {
              const Icon = f.icon;
              return (
                <div key={f.text} className="flex items-center gap-4 group">
                  <div className="h-10 w-10 rounded-xl bg-white/[0.03] border border-white/[0.05] flex items-center justify-center flex-shrink-0 backdrop-blur-md transition-all duration-300 group-hover:bg-white/[0.08] group-hover:border-white/[0.1] group-hover:shadow-[0_0_20px_rgba(20,184,166,0.15)]">
                    <Icon className="h-[18px] w-[18px] text-teal transition-transform group-hover:scale-110 duration-300" />
                  </div>
                  <span className="text-[15px] font-medium text-white/70 group-hover:text-white transition-colors">{f.text}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Zone 3: Globe Animation + Footer ── */}
        <div className="relative z-20 space-y-6">
          {/* Globe in its own dedicated space — never overlaps text */}
          <LottieGlobe />
          <p className="text-xs text-white/25 text-center">
            © 2026 TripOS. Built for travel agencies across India.
          </p>
        </div>
      </div>

      {/* ── Form Panel ── */}
      <div className="flex-1 flex flex-col bg-surface relative overflow-hidden">
        {/* Soft radial background for the form side */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-teal/5 via-surface to-surface pointer-events-none" />
        {/* Mobile-only header */}
        <header className="lg:hidden h-16 flex items-center justify-center px-6 border-b border-line/40">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-md bg-gradient-to-br from-teal to-teal-dark flex items-center justify-center">
              <span className="text-white text-[10px] font-bold">T</span>
            </div>
            <span className="font-display text-lg tracking-tight text-ink">
              Trip<span className="text-ink/60">OS</span>
            </span>
          </Link>
        </header>

        {/* Centered form */}
        <main className="flex-1 flex items-center justify-center p-6 sm:p-10">
          <PageTransition>
            <div className="w-full max-w-[400px]">{children}</div>
          </PageTransition>
        </main>
      </div>
    </div>
  );
}
