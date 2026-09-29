import Link from "next/link";

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-sand/30 flex flex-col">
      <header className="h-14 flex items-center justify-between px-4 sm:px-6 border-b border-line bg-paper/90 backdrop-blur-sm">
        <Link href="/" className="font-display text-xl tracking-tight text-ink">
          TripOS
        </Link>
        <span className="text-xs text-muted-foreground">Secure quote</span>
      </header>
      <main className="flex-1 flex flex-col">{children}</main>
      <footer className="py-4 text-center text-xs text-muted-foreground border-t border-line bg-paper">
        Powered by TripOS · Contact your travel agent for changes
      </footer>
    </div>
  );
}
