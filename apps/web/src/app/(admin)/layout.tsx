'use client';

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, Users, CalendarDays, AlertTriangle, CreditCard, Box, LogOut, Palette, Banknote, KeyRound, Menu } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerTrigger, DrawerClose } from "@/components/ui/drawer";
import { useEffect } from "react";
import { useGetAdminL2bSurvivalQuery } from "@/lib/api/adminApi";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, logout, user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const { data: survival } = useGetAdminL2bSurvivalQuery(undefined, {
    skip: !user?.is_platform_admin,
    pollingInterval: 60_000,
  });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }
    if (!isLoading && isAuthenticated && !user?.is_platform_admin) {
      router.push('/app');
    }
  }, [isAuthenticated, isLoading, router, user?.is_platform_admin]);

  if (isLoading || !isAuthenticated) {
    return <div className="flex min-h-screen items-center justify-center bg-surface">Loading...</div>;
  }

  if (!user?.is_platform_admin) {
    return <div className="flex min-h-screen items-center justify-center bg-surface">Redirecting...</div>;
  }

  const survivalActive = Boolean(survival?.enabled && survival?.active);

  const navLinks = [
    { name: 'Overview', href: '/admin', icon: Activity },
    { name: 'Analytics', href: '/admin/analytics', icon: Activity },
    { name: 'Agents', href: '/admin/agents', icon: Users },
    { name: 'Commissions', href: '/admin/commissions', icon: CreditCard },
    { name: 'Packages', href: '/admin/packages', icon: Box },
    { name: 'Branding', href: '/admin/branding', icon: Palette },
    { name: 'Bookings', href: '/admin/bookings', icon: CalendarDays },
    { name: 'Failures', href: '/admin/failures', icon: AlertTriangle },
    { name: 'Payments', href: '/admin/payments', icon: CreditCard },
    { name: 'Suppliers', href: '/admin/suppliers', icon: Box },
    { name: 'FX rates', href: '/admin/fx', icon: Banknote },
    { name: 'Partners', href: '/admin/partners', icon: KeyRound },
  ];

  return (
    <div className="flex min-h-screen bg-surface">
      {/* Desktop Sidebar (Distinct Admin Theme) */}
      <aside className="w-64 bg-ink text-paper hidden md:flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-white/10">
          <span className="text-xl font-bold text-paper">TripOS Admin</span>
        </div>
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href || (link.href !== '/admin' && pathname.startsWith(link.href));
            return (
              <Link 
                key={link.name}
                href={link.href} 
                className={`flex items-center gap-3 px-3 py-2 rounded-md font-medium transition-colors ${
                  isActive 
                    ? 'text-paper bg-white/10' 
                    : 'text-white/50 hover:bg-white/10 hover:text-paper'
                }`}
              >
                <Icon className={`h-5 w-5 ${isActive ? 'text-focus' : 'text-white/40'}`} />
                {link.name}
              </Link>
            )
          })}
        </nav>
        <div className="p-4 border-t border-white/10 space-y-1">
          <button onClick={logout} className="w-full flex items-center gap-3 px-3 py-2 text-white/50 hover:bg-white/10 rounded-md font-medium text-left transition-colors">
            <LogOut className="h-5 w-5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-paper border-b border-line flex items-center justify-between px-4 sm:px-6">
          <div className="md:hidden flex items-center gap-3">
            <Drawer swipeDirection="left">
              <DrawerTrigger asChild>
                <button className="p-2 -ml-2 text-ink hover:bg-surface rounded-md">
                  <Menu className="w-5 h-5" />
                </button>
              </DrawerTrigger>
              <DrawerContent className="w-64 border-r border-line rounded-none" swipeDirection="left">
                <DrawerHeader className="border-b border-line text-left px-6 py-4">
                  <DrawerTitle className="text-xl font-bold text-ink">TripOS Admin</DrawerTitle>
                </DrawerHeader>
                <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                  {navLinks.map((link) => {
                    const Icon = link.icon;
                    const isActive = pathname === link.href || (link.href !== '/admin' && pathname.startsWith(link.href));
                    return (
                      <DrawerClose asChild key={link.name}>
                        <Link 
                          href={link.href} 
                          className={`flex items-center gap-3 px-3 py-3 rounded-md font-medium transition-colors ${
                            isActive 
                              ? 'text-teal bg-teal/10' 
                              : 'text-muted-foreground hover:bg-surface hover:text-ink'
                          }`}
                        >
                          <Icon className={`h-5 w-5 ${isActive ? 'text-teal' : 'text-muted-foreground/80'}`} />
                          {link.name}
                        </Link>
                      </DrawerClose>
                    )
                  })}
                </nav>
                <div className="p-4 border-t border-line space-y-1">
                  <button onClick={logout} className="w-full flex items-center gap-3 px-3 py-3 text-muted-foreground hover:bg-surface rounded-md font-medium text-left transition-colors">
                    <LogOut className="h-5 w-5" />
                    Sign Out
                  </button>
                </div>
              </DrawerContent>
            </Drawer>
            <span className="text-xl font-bold text-ink">TripOS Admin</span>
          </div>
          <div className="flex-1 flex justify-end">
            <div className="flex items-center gap-4">
              <div className="flex flex-col text-right hidden sm:flex">
                <span className="text-sm font-medium text-ink">{user?.email}</span>
                <span className="text-xs text-muted-foreground">Administrator</span>
              </div>
              <div className="h-8 w-8 rounded-full bg-coral/10 flex items-center justify-center text-coral font-semibold uppercase">
                {user?.email?.charAt(0) || 'A'}
              </div>
            </div>
          </div>
        </header>
        {survivalActive && (
          <div
            role="alert"
            className="bg-amber-500 text-white px-4 sm:px-6 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 shadow-sm"
          >
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-sm">
                  L2B survival active — platform look-to-book critical
                </p>
                <p className="text-xs text-amber-50 mt-0.5">
                  Ratio {survival?.l2b_ratio} (looks {survival?.looks} / confirmed{" "}
                  {survival?.confirmed_bookings}). TTL ×{survival?.ttl_multiplier}
                  {survival?.pause_warm_refresh ? "; warm refresh paused" : ""}.
                </p>
              </div>
            </div>
            <Link
              href="/admin/analytics"
              className="text-xs font-medium underline underline-offset-2 shrink-0 hover:text-white/80"
            >
              View analytics
            </Link>
          </div>
        )}
        <main className="flex-1 p-4 sm:p-6 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
