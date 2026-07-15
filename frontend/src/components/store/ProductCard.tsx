"use client";

import { useState } from "react";
import { Heart, Smartphone } from "lucide-react";
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
  const [imgError, setImgError] = useState(false);

  const outOfStock = product.stock <= 0;
  const favorited = has(product.id);
  const showImage = product.image_url && !imgError;

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
    <article className="group flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-surface transition-all duration-300 hover:-translate-y-1 hover:border-border-strong hover:shadow-lg">
      <div className="relative aspect-square overflow-hidden bg-surface-soft">
        {showImage ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image_url!}
            alt={product.name}
            loading="lazy"
            onError={() => setImgError(true)}
            className="h-full w-full object-contain p-6 transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-ink-subtle">
            <Smartphone className="h-12 w-12" strokeWidth={1.25} />
            <span className="text-xs font-semibold uppercase tracking-wide">{product.brand ?? "Device"}</span>
          </div>
        )}

        <button
          onClick={onFavorite}
          aria-label="Toggle favorite"
          className="absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-full bg-surface/90 shadow-sm backdrop-blur transition-transform hover:scale-110"
        >
          <Heart className={cn("h-4 w-4", favorited ? "fill-danger text-danger" : "text-ink-muted")} />
        </button>

        {outOfStock ? (
          <span className="absolute left-3 top-3">
            <Badge variant="danger">Out of stock</Badge>
          </span>
        ) : product.stock <= 5 ? (
          <span className="absolute left-3 top-3">
            <Badge variant="warning">Only {product.stock} left</Badge>
          </span>
        ) : null}
      </div>

      <div className="flex flex-1 flex-col p-4">
        {product.brand && (
          <p className="mb-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-ink-muted">{product.brand}</p>
        )}
        <h3 className="line-clamp-2 text-base font-extrabold leading-tight text-ink transition-colors group-hover:text-accent-hover">
          {product.name.replace(/^(Apple|Samsung|Xiaomi)\s+/, "")}
        </h3>

        <div className="flex-1" />

        <div className="mt-3 flex items-baseline gap-1">
          <span className="text-2xl font-black tracking-tight text-ink">{usd(product.price_usd)}</span>
        </div>

        <button
          onClick={onAdd}
          disabled={outOfStock || busy}
          className={cn(
            "mt-3 flex h-10 items-center justify-center gap-1.5 rounded-lg text-sm font-bold transition-colors",
            outOfStock
              ? "cursor-not-allowed bg-surface-muted text-ink-subtle"
              : "bg-ink text-white hover:bg-accent",
          )}
        >
          {outOfStock ? "Out of stock" : busy ? "Adding…" : "Add to cart"}
        </button>
      </div>
    </article>
  );
}
