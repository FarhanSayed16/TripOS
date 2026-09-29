import Link from "next/link";
import {
  CreditCard,
  Settings,
  Users,
  ChevronRight,
} from "lucide-react";

const links = [
  { name: "Customers", href: "/app/customers", icon: Users },
  { name: "Payments", href: "/app/payments", icon: CreditCard },
  { name: "Settings", href: "/app/settings", icon: Settings },
];

export default function MorePage() {
  return (
    <div className="space-y-6 max-w-lg mx-auto">
      <div>
        <h1 className="font-display text-3xl tracking-tight text-ink">More</h1>
        <p className="text-muted-foreground text-sm mt-1">Agency tools and account.</p>
      </div>
      <ul className="bg-paper border border-line rounded-lg overflow-hidden divide-y divide-line">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <li key={link.href}>
              <Link
                href={link.href}
                className="flex items-center gap-3 px-4 py-3.5 hover:bg-sand/40 transition-colors"
              >
                <Icon className="h-5 w-5 text-teal" />
                <span className="flex-1 font-medium text-ink">{link.name}</span>
                <ChevronRight className="h-4 w-4 text-muted-foreground/60" />
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
