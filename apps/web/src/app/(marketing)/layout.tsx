import Link from "next/link";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-paper">
      {/* ── Header ── */}
      <header className="h-16 flex items-center justify-between px-6 sm:px-10 glass-header border-b border-line/40 sticky top-0 z-50">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-teal to-teal-dark flex items-center justify-center">
            <span className="text-white text-xs font-bold">T</span>
          </div>
          <span className="font-display text-xl tracking-tight text-ink">
            Trip<span className="text-ink/60">OS</span>
          </span>
        </Link>
        <nav className="flex items-center gap-2">
          <Link href="#features" className="hidden md:inline-flex h-9 items-center rounded-lg px-3 text-sm font-medium text-ink/70 hover:text-ink hover:bg-sand/60 transition-colors">Product</Link>
          <Link href="#how-it-works" className="hidden md:inline-flex h-9 items-center rounded-lg px-3 text-sm font-medium text-ink/70 hover:text-ink hover:bg-sand/60 transition-colors">How it Works</Link>
          <Link
            href="/login"
            className="inline-flex h-9 items-center rounded-lg px-4 text-sm font-medium text-ink hover:bg-sand/60 transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/signup"
            className="inline-flex h-9 items-center rounded-lg btn-gradient px-4 text-sm font-medium text-white"
          >
            Get Started
          </Link>
        </nav>
      </header>

      {/* ── Content ── */}
      <main className="flex-1 flex flex-col">{children}</main>

      {/* ── Footer ── */}
      <footer className="border-t border-line/40 py-8 px-6 sm:px-10">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="h-5 w-5 rounded bg-gradient-to-br from-teal to-teal-dark flex items-center justify-center">
              <span className="text-white text-[8px] font-bold">T</span>
            </div>
            © 2026 TripOS
          </div>
          <div className="flex items-center gap-6 text-xs text-muted-foreground">
            <Link href="#features" className="hover:text-ink transition-colors">Features</Link>
            <Link href="#how-it-works" className="hover:text-ink transition-colors">How it Works</Link>
            <Link href="/login" className="hover:text-ink transition-colors">Privacy</Link>
            <Link href="/login" className="hover:text-ink transition-colors">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
