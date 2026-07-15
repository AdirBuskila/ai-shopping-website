"use client";

import { useState } from "react";
import { ShoppingBag, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { usd } from "@/lib/format";
import { useCart } from "@/context/CartContext";
import { useToast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api";

export function CartPanel() {
  const { order, remove, purchase, discard } = useCart();
  const toast = useToast();
  const [address, setAddress] = useState("");
  const [buying, setBuying] = useState(false);

  if (!order) {
    return (
      <Card className="flex flex-col items-center gap-2 py-14 text-center">
        <ShoppingBag className="h-9 w-9 text-ink-subtle" />
        <p className="font-semibold">Your cart is empty</p>
        <p className="text-sm text-ink-muted">Add products from the shop to start an order.</p>
      </Card>
    );
  }

  const onRemove = async (pid: number, name: string) => {
    try {
      await remove(pid);
      toast(`Removed ${name}`, "info");
    } catch {
      toast("Could not remove item", "error");
    }
  };

  const onPurchase = async () => {
    if (!address.trim()) return toast("Enter a shipping address to check out", "info");
    setBuying(true);
    try {
      await purchase(address);
      toast("Order placed — thank you!", "success");
      setAddress("");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Purchase failed", "error");
    } finally {
      setBuying(false);
    }
  };

  return (
    <Card className="border-accent/40 ring-1 ring-accent/20">
      <div className="flex items-center justify-between border-b border-border p-4">
        <div className="flex items-center gap-2">
          <ShoppingBag className="h-5 w-5 text-accent" />
          <h2 className="text-lg font-bold">Your cart</h2>
          <Badge variant="accent">Open order</Badge>
        </div>
        <button onClick={() => discard()} className="text-sm text-ink-muted hover:text-danger">
          Discard
        </button>
      </div>

      <ul className="divide-y divide-border">
        {order.items.map((it) => (
          <li key={it.product_id} className="flex items-center gap-3 p-4">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{it.name}</p>
              <p className="text-xs text-ink-muted">
                {it.quantity} × {usd(it.unit_price)}
              </p>
            </div>
            <span className="font-semibold">{usd(it.line_total)}</span>
            <button
              onClick={() => onRemove(it.product_id, it.name)}
              aria-label="Remove item"
              className="grid h-8 w-8 place-items-center rounded-lg text-ink-muted hover:bg-danger-soft hover:text-danger"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </li>
        ))}
      </ul>

      <div className="space-y-3 border-t border-border p-4">
        <div className="flex items-center justify-between text-lg font-bold">
          <span>Total</span>
          <span>{usd(order.total_price)}</span>
        </div>
        <Input
          placeholder="Shipping address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
        <Button variant="success" fullWidth size="lg" isLoading={buying} onClick={onPurchase}>
          Place order · {usd(order.total_price)}
        </Button>
      </div>
    </Card>
  );
}
