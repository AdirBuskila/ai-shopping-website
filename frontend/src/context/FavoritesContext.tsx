"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "./AuthContext";
import type { Product } from "@/lib/types";

interface FavCtx {
  favorites: Product[];
  has: (id: number) => boolean;
  toggle: (id: number) => Promise<void>;
  loading: boolean;
}

const Ctx = createContext<FavCtx>({
  favorites: [],
  has: () => false,
  toggle: async () => {},
  loading: false,
});

export const useFavorites = () => useContext(Ctx);

export function FavoritesProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [favorites, setFavorites] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!user) {
      setFavorites([]);
      return;
    }
    setLoading(true);
    try {
      setFavorites(await api.get<Product[]>("/favorites"));
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const has = useCallback((id: number) => favorites.some((f) => f.id === id), [favorites]);

  const toggle = useCallback(
    async (id: number) => {
      const updated = has(id)
        ? await api.del<Product[]>(`/favorites/${id}`)
        : await api.post<Product[]>(`/favorites/${id}`);
      setFavorites(updated);
    },
    [has],
  );

  return <Ctx.Provider value={{ favorites, has, toggle, loading }}>{children}</Ctx.Provider>;
}
