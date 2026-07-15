"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Sparkles, Truck, ShieldCheck, Lock } from "lucide-react";
import { SearchBar } from "@/components/store/SearchBar";
import { ProductGrid } from "@/components/store/ProductGrid";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";

const CATEGORY_LABELS: Record<string, string> = {
  smartphone: "Phones",
  headphones: "Audio",
  tablet: "Tablets",
  smartwatch: "Watches",
  accessory: "Accessories",
};

export default function Home() {
  const [all, setAll] = useState<Product[]>([]);
  const [results, setResults] = useState<Product[] | null>(null);
  const [category, setCategory] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Product[]>("/products")
      .then(setAll)
      .finally(() => setLoading(false));
  }, []);

  const categories = useMemo(() => {
    const set = new Set(all.map((p) => p.category).filter(Boolean) as string[]);
    return ["all", ...[...set]];
  }, [all]);

  const featured = useMemo(
    () =>
      [...all]
        .filter((p) => p.image_url && p.stock > 0)
        .sort((a, b) => b.price_usd - a.price_usd)
        .slice(0, 4),
    [all],
  );

  const shown = useMemo(() => {
    if (results !== null) return results;
    return category === "all" ? all : all.filter((p) => p.category === category);
  }, [results, all, category]);

  return (
    <div className="mx-auto w-full max-w-6xl space-y-10 px-4 py-8">
      {/* Hero */}
      <section className="grid overflow-hidden rounded-3xl border border-border shadow-sm lg:grid-cols-2">
        <div className="flex flex-col justify-center bg-ink p-8 text-white sm:p-12">
          <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold">
            New arrivals in stock
          </span>
          <h1 className="mt-5 text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl">
            The latest iPhone, Galaxy &amp; Xiaomi — honestly priced.
          </h1>
          <p className="mt-4 max-w-md text-white/70">
            Phones, audio, tablets and more. Search the catalog or let our assistant find the
            right fit for your budget.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <a
              href="#catalog"
              className="rounded-xl bg-accent px-6 py-3 text-sm font-bold text-white shadow-md transition-colors hover:bg-accent-hover"
            >
              Shop all products
            </a>
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 rounded-xl border border-white/20 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              <Sparkles className="h-4 w-4" /> Ask the assistant
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-2 bg-surface-soft">
          {featured.map((p, i) => (
            <a
              key={p.id}
              href="#catalog"
              className={cn(
                "flex aspect-square items-center justify-center border-border p-6 transition-colors hover:bg-surface",
                i % 2 === 0 && "border-r",
                i < 2 && "border-b",
              )}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={p.image_url!} alt={p.name} className="h-full w-full object-contain" />
            </a>
          ))}
          {featured.length === 0 && <div className="col-span-2 aspect-[2/1]" />}
        </div>
      </section>

      {/* Trust strip */}
      <section className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { icon: Truck, title: "Fast delivery", sub: "Ships in 72 hours" },
          { icon: ShieldCheck, title: "1-year warranty", sub: "On every device" },
          { icon: Lock, title: "Secure checkout", sub: "Encrypted & safe" },
          { icon: Sparkles, title: "AI assistant", sub: "Knows the catalog" },
        ].map(({ icon: Icon, title, sub }) => (
          <div key={title} className="flex items-center gap-3 rounded-xl border border-border bg-surface p-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent">
              <Icon className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-bold">{title}</p>
              <p className="truncate text-xs text-ink-muted">{sub}</p>
            </div>
          </div>
        ))}
      </section>

      {/* Catalog */}
      <section id="catalog" className="scroll-mt-20 space-y-5">
        <div className="flex flex-col gap-4">
          <h2 className="text-2xl font-black tracking-tight">Shop the catalog</h2>
          <SearchBar onResults={setResults} />
          {results === null && (
            <div className="flex flex-wrap gap-2">
              {categories.map((c) => (
                <button
                  key={c}
                  onClick={() => setCategory(c)}
                  className={cn(
                    "rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors",
                    category === c
                      ? "border-ink bg-ink text-white"
                      : "border-border-strong text-ink-muted hover:border-ink hover:text-ink",
                  )}
                >
                  {c === "all" ? "All" : CATEGORY_LABELS[c] ?? c}
                </button>
              ))}
            </div>
          )}
          {results !== null && (
            <p className="text-sm text-ink-muted">
              {results.length} result{results.length === 1 ? "" : "s"} — showing search matches.
            </p>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <Spinner size="lg" className="text-accent" />
          </div>
        ) : (
          <ProductGrid products={shown} />
        )}
      </section>
    </div>
  );
}
