"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Heart, ShoppingBag, Sparkles, Store } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCart } from "@/context/CartContext";

const NAV = [
  { href: "/", label: "Shop", icon: Store },
  { href: "/favorites", label: "Favorites", icon: Heart },
  { href: "/orders", label: "Orders", icon: ShoppingBag },
  { href: "/chat", label: "Assistant", icon: Sparkles },
];

export function Header({ authSlot }: { authSlot?: React.ReactNode }) {
  const pathname = usePathname();
  const { count } = useCart();
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-2 px-4">
        <Link href="/" className="mr-2 flex items-center gap-2 font-bold tracking-tight">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-gradient text-white">
            <ShoppingBag className="h-4 w-4" />
          </span>
          <span className="text-lg">Shopwise</span>
        </Link>

        <nav className="ml-1 flex items-center gap-0.5 sm:ml-2 sm:gap-1">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                title={label}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-2 py-2 text-sm font-medium transition-colors sm:px-3",
                  active ? "bg-surface-muted text-ink" : "text-ink-muted hover:bg-surface-muted hover:text-ink",
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{label}</span>
                {href === "/orders" && count > 0 && (
                  <span className="ml-0.5 grid h-5 min-w-5 place-items-center rounded-full bg-accent px-1 text-[11px] font-bold text-white">
                    {count}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto">{authSlot}</div>
      </div>
    </header>
  );
}
