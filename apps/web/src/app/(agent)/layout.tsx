'use client';

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  FileText,
  CalendarDays,
  Settings,
  Search as SearchIcon,
  CreditCard,
  MoreHorizontal,
  Bell,
  Sparkles,
  Globe,
  Package,
  Wallet,
  ChevronDown,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useEffect, useMemo } from "react";
import { PageTransition } from "@/components/PageTransition";
import { useI18n } from "@/lib/i18n";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerTrigger, DrawerClose } from "@/components/ui/drawer";

export default function AgentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, logout, user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const { t, locale, setLocale } = useI18n();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  const navSections = useMemo(
    () => [
      {
        labelKey: "nav.workspace",
        items: [
          { nameKey: "nav.home", href: "/app", icon: LayoutDashboard },
          { nameKey: "nav.search", href: "/app/search", icon: SearchIcon },
          { nameKey: "nav.aiAssistant", href: "/app/ai", icon: Sparkles },
        ],
      },
      {
        labelKey: "nav.operations",
        items: [
          { nameKey: "nav.quotes", href: "/app/quotes", icon: FileText },
          { nameKey: "nav.bookings", href: "/app/bookings", icon: CalendarDays },
          { nameKey: "nav.packages", href: "/app/packages", icon: Package },
          { nameKey: "nav.customers", href: "/app/customers", icon: Users },
          { nameKey: "nav.network", href: "/app/network", icon: Globe },
        ],
      },
      {
        labelKey: "nav.money",
        items: [
          { nameKey: "nav.wallet", href: "/app/wallet", icon: Wallet },
          { nameKey: "nav.payments", href: "/app/payments", icon: CreditCard },
        ],
      },
    ],
    []
  );

  const mobileTabs = useMemo(
    () => [
      { nameKey: "nav.home", href: "/app", icon: LayoutDashboard },
      { nameKey: "nav.search", href: "/app/search", icon: SearchIcon },
      { nameKey: "nav.quotes", href: "/app/quotes", icon: FileText },
      { nameKey: "nav.bookings", href: "/app/bookings", icon: CalendarDays },
      { nameKey: "nav.more", href: "#more", icon: MoreHorizontal, isDrawer: true },
    ],
    []
  );

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 rounded-full border-2 border-teal border-t-transparent animate-spin" />
          <span className="text-sm text-muted-foreground">{t("nav.loading")}</span>
        </div>
      </div>
    );
  }

  const isActive = (href: string) =>
    pathname === href || (href !== "/app" && pathname.startsWith(href));

  const userInitial = user?.email?.charAt(0)?.toUpperCase() || "A";

  const getPageContext = (path: string) => {
    if (path === "/app") return { title: "Home", subtitle: "Welcome to your workspace" };
    if (path.startsWith("/app/search")) return { title: "Search", subtitle: "Find flights and hotels" };
    if (path.startsWith("/app/quotes")) return { title: "Quotes", subtitle: "Manage customer quotes" };
    if (path.startsWith("/app/bookings")) return { title: "Bookings", subtitle: "View and modify bookings" };
    if (path.startsWith("/app/wallet")) return { title: "Wallet", subtitle: "Manage your funds" };
    if (path.startsWith("/app/settings")) return { title: "Settings", subtitle: "Preferences and configuration" };
    return { title: "TripOS", subtitle: "Agent Workspace" };
  };

  const pageContext = getPageContext(pathname);

  return (
    <div className="flex min-h-screen bg-paper">
      <aside className="w-[240px] bg-paper border-r border-line hidden md:flex flex-col fixed inset-y-0 left-0 z-30">
        <div className="h-16 flex items-center gap-2.5 px-6 border-b border-line/80">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-teal to-teal-dark flex items-center justify-center">
            <span className="text-white text-xs font-bold">T</span>
          </div>
          <span className="font-display text-xl tracking-tight text-ink">
            Trip<span className="text-ink/60">OS</span>
          </span>
        </div>

        <nav className="flex-1 px-3 pt-4 pb-2 overflow-y-auto space-y-1">
          {navSections.map((section) => (
            <div key={section.labelKey}>
              <div className="nav-group-label">{t(section.labelKey)}</div>
              <div className="space-y-0.5">
                {section.items.map((link) => {
                  const Icon = link.icon;
                  const active = isActive(link.href);
                  return (
                    <Link
                      key={link.nameKey}
                      href={link.href}
                      className={`relative flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-200 ${
                        active
                          ? "text-ink bg-teal/[0.06] nav-active-bar"
                          : "text-muted-foreground hover:bg-sand/50 hover:text-ink"
                      }`}
                    >
                      <Icon
                        className={`h-[18px] w-[18px] transition-colors duration-200 ${
                          active ? "text-teal" : "text-muted-foreground/60"
                        }`}
                      />
                      {t(link.nameKey)}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="px-3 py-3 border-t border-line/80">
          <Link
            href="/app/settings"
            className={`relative flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-200 ${
              isActive("/app/settings")
                ? "text-ink bg-teal/[0.06] nav-active-bar"
                : "text-muted-foreground hover:bg-sand/50 hover:text-ink"
            }`}
          >
            <Settings
              className={`h-[18px] w-[18px] transition-colors duration-200 ${
                isActive("/app/settings") ? "text-teal" : "text-muted-foreground/60"
              }`}
            />
            {t("nav.settings")}
          </Link>

          <div className="mt-2 flex items-center gap-3 px-3 py-2 rounded-lg bg-surface border border-line">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-teal to-teal-dark flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
              {userInitial}
            </div>
            <div className="flex-1 min-w-0 flex flex-col justify-center">
              <div className="text-[13px] font-medium text-ink truncate">Sahil Doe</div>
              <div className="text-[11px] text-muted-foreground truncate">Sahil Travels</div>
            </div>
            <button
              onClick={logout}
              className="text-[11px] text-muted-foreground hover:text-coral transition-colors flex-shrink-0"
              title="Logout"
            >
              Log out
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 md:ml-[240px]">
        <header className="h-16 bg-surface border-b border-line flex items-center justify-between px-6 sticky top-0 z-20">
          <div className="flex items-center gap-8 flex-1">
            <div className="hidden lg:flex flex-col">
              <h1 className="text-lg font-semibold text-ink leading-tight">{pageContext.title}</h1>
              <span className="text-xs text-muted-foreground">{pageContext.subtitle}</span>
            </div>
            <div className="relative max-w-md w-full hidden md:block">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input 
                type="text" 
                placeholder="Search bookings, PNR, customer..." 
                className="w-full pl-9 pr-4 h-9 bg-paper border border-line rounded-lg text-sm focus:outline-none focus:border-teal focus:ring-1 focus:ring-teal/30 transition-all placeholder:text-muted-foreground/60"
              />
            </div>
          </div>
          
          <div className="flex items-center gap-4 ml-4">
            <button className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-muted/50 transition-colors border border-transparent hover:border-line">
              <span className="text-sm font-medium text-ink">Sahil Travels</span>
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
            </button>
            
            <div className="hidden sm:flex items-center bg-paper border border-line rounded-md p-0.5">
              <button onClick={() => setLocale('en')} className={`px-2.5 py-1 text-[11px] font-medium rounded transition-colors ${locale === 'en' ? 'bg-surface shadow-sm text-ink' : 'text-muted-foreground hover:text-ink'}`}>EN</button>
              <button onClick={() => setLocale('hi')} className={`px-2.5 py-1 text-[11px] font-medium rounded transition-colors ${locale === 'hi' ? 'bg-surface shadow-sm text-ink' : 'text-muted-foreground hover:text-ink'}`}>HI</button>
            </div>

            <button className="relative p-2 rounded-full hover:bg-muted/50 transition-colors">
              <Bell className="h-4 w-4 text-ink" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-coral border-2 border-surface" />
            </button>
            
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-teal to-teal-dark flex items-center justify-center text-white text-xs font-semibold cursor-pointer">
              {userInitial}
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto pb-20 md:pb-8">
          <PageTransition>{children}</PageTransition>
        </main>
      </div>

      <nav className="md:hidden fixed bottom-0 left-0 right-0 glass-header border-t border-line/60 flex justify-around items-center h-16 z-50 px-2 pb-safe">
        {mobileTabs.map((link) => {
          const Icon = link.icon;
          const active = isActive(link.href) && !link.isDrawer;
          
          if (link.isDrawer) {
            return (
              <Drawer key={link.nameKey} swipeDirection="down">
                <DrawerTrigger asChild>
                  <button className="flex flex-col items-center justify-center w-full h-full space-y-0.5 text-muted-foreground hover:text-ink">
                    <Icon className="h-5 w-5" />
                    <span className="text-[10px] font-medium">{t(link.nameKey)}</span>
                  </button>
                </DrawerTrigger>
                <DrawerContent showSwipeHandle className="max-h-[85vh] rounded-t-2xl">
                  <DrawerHeader className="border-b border-line pb-4 pt-2">
                    <DrawerTitle className="text-lg text-ink font-semibold">Menu</DrawerTitle>
                  </DrawerHeader>
                  <div className="overflow-y-auto px-4 py-2 pb-8">
                    {navSections.map((section) => (
                      <div key={section.labelKey} className="py-2">
                        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">{t(section.labelKey)}</div>
                        <div className="space-y-1">
                          {section.items.map((subLink) => {
                            const SubIcon = subLink.icon;
                            const subActive = isActive(subLink.href);
                            return (
                              <DrawerClose asChild key={subLink.nameKey}>
                                <Link
                                  href={subLink.href}
                                  className={`flex items-center gap-3 px-3 py-3 rounded-xl font-medium transition-colors ${
                                    subActive ? "bg-teal/10 text-teal" : "text-ink hover:bg-surface"
                                  }`}
                                >
                                  <SubIcon className={`w-5 h-5 ${subActive ? "text-teal" : "text-muted-foreground"}`} />
                                  {t(subLink.nameKey)}
                                </Link>
                              </DrawerClose>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                    <div className="py-2 mt-2 border-t border-line">
                      <DrawerClose asChild>
                        <Link
                          href="/app/settings"
                          className="flex items-center gap-3 px-3 py-3 rounded-xl font-medium text-ink hover:bg-surface"
                        >
                          <Settings className="w-5 h-5 text-muted-foreground" />
                          {t("nav.settings")}
                        </Link>
                      </DrawerClose>
                    </div>
                  </div>
                </DrawerContent>
              </Drawer>
            );
          }

          return (
            <Link
              key={link.nameKey}
              href={link.href}
              className={`flex flex-col items-center justify-center w-full h-full space-y-0.5 transition-colors duration-200 ${
                active ? "text-teal" : "text-muted-foreground hover:text-ink"
              }`}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] font-medium">{t(link.nameKey)}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
