import { CheckCircle2 } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { usd } from "@/lib/format";
import type { Order } from "@/lib/types";

function fmtDate(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

export function OrderHistoryCard({ order }: { order: Order }) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold">Order #{order.id}</span>
          <Badge variant="success">
            <CheckCircle2 className="h-3 w-3" /> Completed
          </Badge>
        </div>
        <span className="text-sm text-ink-muted">{fmtDate(order.closed_at ?? order.created_at)}</span>
      </div>

      <ul className="mt-3 space-y-1 text-sm">
        {order.items.map((it) => (
          <li key={it.product_id} className="flex justify-between text-ink-muted">
            <span className="truncate pr-2">
              {it.quantity} × {it.name}
            </span>
            <span>{usd(it.line_total)}</span>
          </li>
        ))}
      </ul>

      <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
        {order.shipping_address && (
          <span className="truncate pr-2 text-xs text-ink-subtle">Ship to: {order.shipping_address}</span>
        )}
        <span className="ml-auto font-bold">{usd(order.total_price)}</span>
      </div>
    </Card>
  );
}
