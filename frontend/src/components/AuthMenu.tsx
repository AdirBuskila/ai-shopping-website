"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronDown, LogOut, Trash2, UserRound } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/ui/Toast";

export function AuthMenu() {
  const { user, ready, logout, deleteAccount } = useAuth();
  const [open, setOpen] = useState(false);
  const toast = useToast();
  const router = useRouter();

  if (!ready) return <div className="h-9 w-20 animate-pulse rounded-lg bg-surface-muted" />;

  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Link href="/login" className="rounded-lg px-3 py-2 text-sm font-medium text-ink-muted hover:text-ink">
          Log in
        </Link>
        <Link
          href="/register"
          className="rounded-lg bg-ink px-3.5 py-2 text-sm font-semibold text-white hover:bg-ink-soft"
        >
          Sign up
        </Link>
      </div>
    );
  }

  const onDelete = async () => {
    if (!confirm("Delete your account and all its data? This cannot be undone.")) return;
    try {
      await deleteAccount();
      toast("Account deleted", "success");
      router.push("/");
    } catch {
      toast("Could not delete account", "error");
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-surface-muted"
      >
        <UserRound className="h-4 w-4" />
        <span className="hidden sm:inline">{user.username}</span>
        <ChevronDown className="h-3.5 w-3.5 text-ink-subtle" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-2 w-48 overflow-hidden rounded-xl border border-border bg-surface shadow-lg">
            <button
              onClick={() => {
                logout();
                setOpen(false);
                toast("Logged out", "info");
              }}
              className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm hover:bg-surface-muted"
            >
              <LogOut className="h-4 w-4" /> Log out
            </button>
            <button
              onClick={onDelete}
              className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-danger hover:bg-danger-soft"
            >
              <Trash2 className="h-4 w-4" /> Delete account
            </button>
          </div>
        </>
      )}
    </div>
  );
}
