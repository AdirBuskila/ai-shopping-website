"use client";

import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { SearchBar } from "@/components/store/SearchBar";
import { ProductGrid } from "@/components/store/ProductGrid";
import { Spinner } from "@/components/ui/Spinner";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";

export default function Home() {
  const [all, setAll] = useState<Product[]>([]);
  const [results, setResults] = useState<Product[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Product[]>("/products")
      .then(setAll)
      .finally(() => setLoading(false));
  }, []);

  const shown = results ?? all;

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-2xl bg-brand-gradient px-8 py-14 text-white shadow-lg">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold">
          <Sparkles className="h-3.5 w-3.5" /> AI-powered store
        </span>
        <h1 className="mt-4 max-w-2xl text-4xl font-bold tracking-tight sm:text-5xl">
          Electronics, with an assistant that actually knows the shelf.
        </h1>
        <p className="mt-4 max-w-xl text-lg text-white/80">
          Browse the catalog, search by anything, and ask the AI what fits your budget.
        </p>
      </section>

      <SearchBar onResults={setResults} />

      {results !== null && (
        <p className="text-sm text-ink-muted">
          {results.length} result{results.length === 1 ? "" : "s"} — showing search matches.
        </p>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner size="lg" className="text-accent" />
        </div>
      ) : (
        <ProductGrid products={shown} />
      )}
    </div>
  );
}
