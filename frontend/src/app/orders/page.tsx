"use client";

import Link from "next/link";
import { ShoppingBag } from "lucide-react";
import { CartPanel } from "@/components/store/CartPanel";
import { OrderHistoryCard } from "@/components/store/OrderHistoryCard";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/context/AuthContext";
import { useCart } from "@/context/CartContext";

export default function OrdersPage() {
  const { user, ready } = useAuth();
  const { orders } = useCart();

  if (!ready) {
    return (
      <div className="flex justify-center py-20">
        <Spinner size="lg" className="text-accent" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-md py-20 text-center">
        <ShoppingBag className="mx-auto h-10 w-10 text-ink-subtle" />
        <h1 className="mt-4 text-2xl font-bold">Your orders live here</h1>
        <p className="mt-2 text-ink-muted">Log in to build a cart and check out.</p>
        <Link href="/login" className="mt-6 inline-block">
          <Button variant="accent">Log in</Button>
        </Link>
      </div>
    );
  }

  const history = orders.filter((o) => o.status === "CLOSE");

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr]">
      <section className="space-y-4">
        <h1 className="text-2xl font-bold tracking-tight">Cart</h1>
        <CartPanel />
      </section>

      <section className="space-y-4">
        <h1 className="text-2xl font-bold tracking-tight">Order history</h1>
        {history.length === 0 ? (
          <p className="rounded-xl border border-dashed border-border-strong py-16 text-center text-sm text-ink-muted">
            No completed orders yet.
          </p>
        ) : (
          <div className="space-y-3">
            {history.map((o) => (
              <OrderHistoryCard key={o.id} order={o} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
