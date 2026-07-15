"use client";

import * as React from "react";
import { Check, X, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastKind = "success" | "error" | "info";
type Toast = { id: number; message: string; kind: ToastKind };

const ToastContext = React.createContext<(message: string, kind?: ToastKind) => void>(() => {});

export function useToast() {
  return React.useContext(ToastContext);
}

let _id = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const toast = React.useCallback((message: string, kind: ToastKind = "info") => {
    const id = ++_id;
    setToasts((t) => [...t, { id, message, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  }, []);

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto flex items-start gap-2.5 rounded-lg border bg-surface px-3.5 py-3 text-sm shadow-lg",
              "animate-[slidein_0.2s_ease-out]",
              t.kind === "success" && "border-success-soft",
              t.kind === "error" && "border-danger-soft",
              t.kind === "info" && "border-border-strong",
            )}
          >
            <span className="mt-0.5 shrink-0">
              {t.kind === "success" && <Check className="h-4 w-4 text-success" />}
              {t.kind === "error" && <X className="h-4 w-4 text-danger" />}
              {t.kind === "info" && <AlertTriangle className="h-4 w-4 text-accent" />}
            </span>
            <span className="text-ink-soft">{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
