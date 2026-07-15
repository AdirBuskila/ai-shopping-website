"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Heart, Minus, Plus, Smartphone } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/utils";
import { usd } from "@/lib/format";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useCart } from "@/context/CartContext";
import { useFavorites } from "@/context/FavoritesContext";
import { useToast } from "@/components/ui/Toast";
import type { Product } from "@/lib/types";

export default function ProductPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { add } = useCart();
  const { has, toggle } = useFavorites();
  const toast = useToast();

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [qty, setQty] = useState(1);
  const [busy, setBusy] = useState(false);
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    api
      .get<Product>(`/products/${id}`)
      .then(setProduct)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center py-32">
        <Spinner size="lg" className="text-accent" />
      </div>
    );
  }

  if (notFound || !product) {
    return (
      <div className="mx-auto max-w-md px-4 py-24 text-center">
        <h1 className="text-2xl font-bold">Product not found</h1>
        <Link href="/" className="mt-4 inline-block">
          <Button variant="outline">Back to shop</Button>
        </Link>
      </div>
    );
  }

  const outOfStock = product.stock <= 0;
  const favorited = has(product.id);
  const showImage = product.image_url && !imgError;

  const onAdd = async () => {
    if (!user) return toast("Log in to add to cart", "info");
    setBusy(true);
    try {
      await add(product.id, qty);
      toast(`Added ${qty} × ${product.name} to cart`, "success");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Could not add to cart", "error");
    } finally {
      setBusy(false);
    }
  };
  const onFav = async () => {
    if (!user) return toast("Log in to save favorites", "info");
    try {
      await toggle(product.id);
    } catch {
      toast("Could not update favorites", "error");
    }
  };

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8">
      <Link href="/" className="mb-6 inline-flex items-center gap-1.5 text-sm font-medium text-ink-muted hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> Back to shop
      </Link>

      <div className="grid gap-8 md:grid-cols-2">
        <div className="relative flex aspect-square items-center justify-center overflow-hidden rounded-2xl border border-border bg-surface-soft p-8">
          {showImage ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={product.image_url!}
              alt={product.name}
              onError={() => setImgError(true)}
              className="h-full w-full object-contain"
            />
          ) : (
            <div className="flex flex-col items-center gap-2 text-ink-subtle">
              <Smartphone className="h-20 w-20" strokeWidth={1} />
              <span className="text-sm font-semibold uppercase tracking-wide">{product.brand}</span>
            </div>
          )}
        </div>

        <div className="flex flex-col">
          {product.brand && (
            <p className="text-xs font-bold uppercase tracking-[0.12em] text-ink-muted">{product.brand}</p>
          )}
          <h1 className="mt-1 text-3xl font-black tracking-tight">{product.name}</h1>

          <div className="mt-4 flex items-center gap-3">
            <span className="text-3xl font-black">{usd(product.price_usd)}</span>
            {outOfStock ? (
              <Badge variant="danger">Out of stock</Badge>
            ) : product.stock <= 5 ? (
              <Badge variant="warning">Only {product.stock} left</Badge>
            ) : (
              <Badge variant="success">In stock</Badge>
            )}
          </div>

          {product.description && (
            <p className="mt-5 leading-relaxed text-ink-soft">{product.description}</p>
          )}

          {!outOfStock && (
            <div className="mt-6 flex items-center gap-3">
              <span className="text-sm font-semibold text-ink-muted">Quantity</span>
              <div className="flex items-center rounded-lg border border-border-strong">
                <button
                  onClick={() => setQty((q) => Math.max(1, q - 1))}
                  className="grid h-10 w-10 place-items-center text-ink-muted hover:text-ink"
                  aria-label="Decrease quantity"
                >
                  <Minus className="h-4 w-4" />
                </button>
                <span className="w-10 text-center font-semibold">{qty}</span>
                <button
                  onClick={() => setQty((q) => Math.min(product.stock, q + 1))}
                  className="grid h-10 w-10 place-items-center text-ink-muted hover:text-ink"
                  aria-label="Increase quantity"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          <div className="mt-6 flex gap-3">
            <Button variant="accent" size="lg" onClick={onAdd} disabled={outOfStock} isLoading={busy}>
              {outOfStock ? "Out of stock" : "Add to cart"}
            </Button>
            <button
              onClick={onFav}
              aria-label="Toggle favorite"
              className="grid h-13 w-13 place-items-center rounded-xl border border-border-strong hover:bg-surface-muted"
            >
              <Heart className={cn("h-5 w-5", favorited ? "fill-danger text-danger" : "text-ink-muted")} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
