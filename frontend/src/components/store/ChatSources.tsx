"use client";

import { useState } from "react";
import Link from "next/link";
import { Package } from "lucide-react";
import { usd } from "@/lib/format";
import type { ProductRef } from "@/lib/types";

function Chip({ s }: { s: ProductRef }) {
  const [err, setErr] = useState(false);
  return (
    <Link
      href={`/products/${s.id}`}
      className="flex items-center gap-2 rounded-lg border border-border bg-surface px-2 py-1.5 transition-colors hover:border-border-strong hover:shadow-sm"
    >
      <span className="grid h-8 w-8 shrink-0 place-items-center overflow-hidden rounded bg-surface-soft">
        {s.image_url && !err ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={s.image_url}
            alt=""
            onError={() => setErr(true)}
            className="h-full w-full object-contain p-0.5"
          />
        ) : (
          <Package className="h-4 w-4 text-ink-subtle" />
        )}
      </span>
      <span className="min-w-0">
        <span className="block max-w-[11rem] truncate text-xs font-semibold text-ink">{s.name}</span>
        <span className="text-[11px] text-ink-muted">{usd(s.price_usd)}</span>
      </span>
    </Link>
  );
}

export function ChatSources({ sources }: { sources: ProductRef[] }) {
  if (!sources.length) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-2 border-t border-border pt-3">
      {sources.slice(0, 4).map((s) => (
        <Chip key={s.id} s={s} />
      ))}
    </div>
  );
}
