"use client";

import { useState } from "react";
import { Heart, Plus } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { usd } from "@/lib/format";
import { useAuth } from "@/context/AuthContext";
import { useFavorites } from "@/context/FavoritesContext";
import { useCart } from "@/context/CartContext";
import { useToast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api";
import type { Product } from "@/lib/types";

export function ProductCard({ product }: { product: Product }) {
  const { user } = useAuth();
  const { has, toggle } = useFavorites();
  const { add } = useCart();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  const outOfStock = product.stock <= 0;
  const favorited = has(product.id);

  const onFavorite = async () => {
    if (!user) return toast("Log in to save favorites", "info");
    try {
      await toggle(product.id);
      toast(favorited ? "Removed from favorites" : "Saved to favorites", "success");
    } catch {
      toast("Could not update favorites", "error");
    }
  };

  const onAdd = async () => {
    if (!user) return toast("Log in to add to cart", "info");
    setBusy(true);
    try {
      await add(product.id);
      toast(`Added ${product.name} to cart`, "success");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Could not add to cart", "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="group flex flex-col overflow-hidden transition-shadow hover:shadow-md">
      <div className="relative aspect-square bg-surface-muted">
        {product.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image_url}
            alt={product.name}
            className="h-full w-full object-contain p-4 mix-blend-multiply"
          />
        ) : (
          <div className="grid h-full place-items-center text-4xl font-bold text-ink-subtle">
            {product.brand?.[0] ?? product.name[0]}
          </div>
        )}
        <button
          onClick={onFavorite}
          aria-label="Toggle favorite"
          className="absolute right-2 top-2 grid h-8 w-8 place-items-center rounded-full bg-surface/90 shadow-sm hover:bg-surface"
        >
          <Heart className={cn("h-4 w-4", favorited ? "fill-danger text-danger" : "text-ink-muted")} />
        </button>
        {outOfStock && (
          <span className="absolute left-2 top-2">
            <Badge variant="danger">Out of stock</Badge>
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        {product.brand && <span className="text-xs font-medium uppercase tracking-wide text-ink-subtle">{product.brand}</span>}
        <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-ink">{product.name}</h3>
        <div className="mt-auto flex items-center justify-between pt-2">
          <span className="text-lg font-bold">{usd(product.price_usd)}</span>
          {!outOfStock && product.stock <= 5 && <Badge variant="warning">Only {product.stock} left</Badge>}
        </div>
        <button
          onClick={onAdd}
          disabled={outOfStock || busy}
          className={cn(
            "mt-1 flex h-10 items-center justify-center gap-1.5 rounded-lg text-sm font-semibold transition-colors",
            outOfStock
              ? "cursor-not-allowed bg-surface-muted text-ink-subtle"
              : "bg-ink text-white hover:bg-ink-soft",
          )}
        >
          <Plus className="h-4 w-4" /> {outOfStock ? "Unavailable" : "Add to cart"}
        </button>
      </div>
    </Card>
  );
}
