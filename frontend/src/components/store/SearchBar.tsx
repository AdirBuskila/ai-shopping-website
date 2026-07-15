"use client";

import { useState } from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import type { Product } from "@/lib/types";

const OPS = ["<", ">", "="];

export function SearchBar({ onResults }: { onResults: (p: Product[] | null) => void }) {
  const toast = useToast();
  const [q, setQ] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [priceOp, setPriceOp] = useState("");
  const [priceVal, setPriceVal] = useState("");
  const [stockOp, setStockOp] = useState("");
  const [stockVal, setStockVal] = useState("");
  const [loading, setLoading] = useState(false);

  const search = async (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (priceOp && priceVal) {
      params.set("price_op", priceOp);
      params.set("price_value", priceVal);
    }
    if (stockOp && stockVal) {
      params.set("stock_op", stockOp);
      params.set("stock_value", stockVal);
    }
    if ([...params].length === 0) {
      onResults(null);
      return;
    }
    setLoading(true);
    try {
      onResults(await api.get<Product[]>(`/products/search?${params.toString()}`));
    } catch {
      toast("Search failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const clear = () => {
    setQ("");
    setPriceOp("");
    setPriceVal("");
    setStockOp("");
    setStockVal("");
    onResults(null);
  };

  const opSelect = (value: string, onChange: (v: string) => void, label: string) => (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label={label}
      className="h-11 rounded-lg border border-border-strong bg-surface px-2 text-sm"
    >
      <option value="">{label}</option>
      {OPS.map((o) => (
        <option key={o} value={o}>
          {o}
        </option>
      ))}
    </select>
  );

  return (
    <form onSubmit={search} className="space-y-3">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-subtle" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search products — try several words, e.g. iphone samsung"
            className="pl-9"
          />
        </div>
        <Button type="button" variant="outline" onClick={() => setShowFilters((s) => !s)}>
          <SlidersHorizontal className="h-4 w-4" /> Filters
        </Button>
        <Button type="submit" variant="accent" isLoading={loading}>
          Search
        </Button>
      </div>

      {showFilters && (
        <div className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-surface p-3 text-sm">
          <span className="font-medium text-ink-muted">Price ($)</span>
          {opSelect(priceOp, setPriceOp, "op")}
          <Input
            type="number"
            value={priceVal}
            onChange={(e) => setPriceVal(e.target.value)}
            placeholder="value"
            className="h-11 w-28"
          />
          <span className="ml-3 font-medium text-ink-muted">Stock</span>
          {opSelect(stockOp, setStockOp, "op")}
          <Input
            type="number"
            value={stockVal}
            onChange={(e) => setStockVal(e.target.value)}
            placeholder="value"
            className="h-11 w-28"
          />
          <button type="button" onClick={clear} className="ml-auto flex items-center gap-1 text-ink-muted hover:text-ink">
            <X className="h-3.5 w-3.5" /> Clear
          </button>
        </div>
      )}
    </form>
  );
}
