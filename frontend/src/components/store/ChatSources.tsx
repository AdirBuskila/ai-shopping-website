"use client";

import { useState } from "react";
import Link from "next/link";
import { Package, ArrowRight } from "lucide-react";
import { usd } from "@/lib/format";
import type { ProductRef } from "@/lib/types";

function Thumb({ src, className }: { src?: string | null; className: string }) {
  const [err, setErr] = useState(false);
  return (
    <span className={`grid shrink-0 place-items-center overflow-hidden rounded-lg bg-surface-soft ${className}`}>
      {src && !err ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt="" onError={() => setErr(true)} className="h-full w-full object-contain p-1" />
      ) : (
        <Package className="h-5 w-5 text-ink-subtle" />
      )}
    </span>
  );
}

export function ChatSources({ sources }: { sources: ProductRef[] }) {
  if (!sources.length) return null;
  const [top, ...rest] = sources;

  return (
    <div className="mt-3 space-y-2 border-t border-border pt-3">
      {/* Featured "Top pick" — the product the assistant recommended */}
      <Link
        href={`/products/${top.id}`}
        className="group flex items-center gap-3 rounded-xl border border-accent/40 bg-accent-soft/40 p-3 transition-colors hover:border-accent"
      >
        <Thumb src={top.image_url} className="h-14 w-14" />
        <div className="min-w-0 flex-1">
          <span className="text-[10px] font-bold uppercase tracking-wide text-accent">Top pick</span>
          <p className="truncate text-sm font-bold text-ink">{top.name}</p>
          <p className="text-sm font-semibold text-ink-muted">{usd(top.price_usd)}</p>
        </div>
        <ArrowRight className="h-4 w-4 shrink-0 text-ink-subtle transition-transform group-hover:translate-x-0.5" />
      </Link>

      {/* Smaller alternatives */}
      {rest.length > 0 && (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          {rest.map((s) => (
            <Link
              key={s.id}
              href={`/products/${s.id}`}
              className="flex items-center gap-2 rounded-lg border border-border bg-surface px-2 py-1.5 transition-colors hover:border-border-strong hover:shadow-sm"
            >
              <Thumb src={s.image_url} className="h-9 w-9" />
              <span className="min-w-0">
                <span className="block truncate text-xs font-semibold text-ink">{s.name}</span>
                <span className="text-[11px] text-ink-muted">{usd(s.price_usd)}</span>
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
