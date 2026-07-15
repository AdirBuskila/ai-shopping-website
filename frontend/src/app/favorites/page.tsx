"use client";

import Link from "next/link";
import { Heart } from "lucide-react";
import { ProductGrid } from "@/components/store/ProductGrid";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/context/AuthContext";
import { useFavorites } from "@/context/FavoritesContext";

export default function FavoritesPage() {
  const { user, ready } = useAuth();
  const { favorites, loading } = useFavorites();

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
        <Heart className="mx-auto h-10 w-10 text-ink-subtle" />
        <h1 className="mt-4 text-2xl font-bold">Your favorites live here</h1>
        <p className="mt-2 text-ink-muted">Log in to save products and find them again later.</p>
        <Link href="/login" className="mt-6 inline-block">
          <Button variant="accent">Log in</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 px-4 py-10">
      <div className="flex items-center gap-2">
        <Heart className="h-6 w-6 fill-danger text-danger" />
        <h1 className="text-3xl font-bold tracking-tight">Favorites</h1>
        <span className="text-ink-muted">({favorites.length})</span>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner size="lg" className="text-accent" />
        </div>
      ) : favorites.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border-strong py-20 text-center">
          <p className="font-semibold">No favorites yet</p>
          <p className="mt-1 text-sm text-ink-muted">Tap the heart on any product to save it here.</p>
          <Link href="/" className="mt-4 inline-block">
            <Button variant="outline">Browse products</Button>
          </Link>
        </div>
      ) : (
        <ProductGrid products={favorites} />
      )}
    </div>
  );
}
