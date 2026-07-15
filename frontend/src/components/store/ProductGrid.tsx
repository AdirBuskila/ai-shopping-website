import { PackageOpen } from "lucide-react";
import { ProductCard } from "./ProductCard";
import type { Product } from "@/lib/types";

export function ProductGrid({ products }: { products: Product[] }) {
  if (products.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border-strong py-20 text-center">
        <PackageOpen className="h-10 w-10 text-ink-subtle" />
        <p className="font-semibold text-ink">No products match your search</p>
        <p className="text-sm text-ink-muted">Try fewer words or a wider price/stock range.</p>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {products.map((p) => (
        <ProductCard key={p.id} product={p} />
      ))}
    </div>
  );
}
