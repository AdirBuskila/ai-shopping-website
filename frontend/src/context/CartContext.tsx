"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "./AuthContext";
import type { Order } from "@/lib/types";

interface CartCtx {
  order: Order | null; // the current TEMP cart
  orders: Order[]; // all orders (TEMP first, then history)
  count: number;
  add: (productId: number, qty?: number) => Promise<void>;
  remove: (productId: number) => Promise<void>;
  purchase: (address: string) => Promise<void>;
  discard: () => Promise<void>;
  refresh: () => Promise<void>;
}

const Ctx = createContext<CartCtx>({
  order: null,
  orders: [],
  count: 0,
  add: async () => {},
  remove: async () => {},
  purchase: async () => {},
  discard: async () => {},
  refresh: async () => {},
});

export const useCart = () => useContext(Ctx);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);

  const order = useMemo(() => orders.find((o) => o.status === "TEMP") ?? null, [orders]);
  const count = useMemo(
    () => (order ? order.items.reduce((s, i) => s + i.quantity, 0) : 0),
    [order],
  );

  const refresh = useCallback(async () => {
    if (!user) {
      setOrders([]);
      return;
    }
    try {
      setOrders(await api.get<Order[]>("/orders"));
    } catch {
      /* ignore */
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const add = useCallback(
    async (productId: number, qty = 1) => {
      await api.post("/orders/items", { product_id: productId, quantity: qty });
      await refresh();
    },
    [refresh],
  );

  const remove = useCallback(
    async (productId: number) => {
      await api.del(`/orders/items/${productId}`);
      await refresh();
    },
    [refresh],
  );

  const purchase = useCallback(
    async (address: string) => {
      if (!order) return;
      await api.post(`/orders/${order.id}/purchase`, { shipping_address: address });
      await refresh();
    },
    [order, refresh],
  );

  const discard = useCallback(async () => {
    if (!order) return;
    await api.del(`/orders/${order.id}`);
    await refresh();
  }, [order, refresh]);

  return (
    <Ctx.Provider value={{ order, orders, count, add, remove, purchase, discard, refresh }}>
      {children}
    </Ctx.Provider>
  );
}
