"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { RegisterData, UserPublic } from "@/lib/types";

interface AuthCtx {
  user: UserPublic | null;
  ready: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  deleteAccount: () => Promise<void>;
}

const Ctx = createContext<AuthCtx>({
  user: null,
  ready: false,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  deleteAccount: async () => {},
});

export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("token")) {
      setReady(true);
      return;
    }
    api
      .get<UserPublic>("/auth/me")
      .then(setUser)
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setReady(true));
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const { access_token } = await api.post<{ access_token: string }>("/auth/login", {
      username,
      password,
    });
    localStorage.setItem("token", access_token);
    setUser(await api.get<UserPublic>("/auth/me"));
  }, []);

  const register = useCallback(
    async (data: RegisterData) => {
      await api.post("/auth/register", data);
      await login(data.username, data.password);
    },
    [login],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setUser(null);
  }, []);

  const deleteAccount = useCallback(async () => {
    await api.del("/auth/me");
    logout();
  }, [logout]);

  return (
    <Ctx.Provider value={{ user, ready, login, register, logout, deleteAccount }}>
      {children}
    </Ctx.Provider>
  );
}
