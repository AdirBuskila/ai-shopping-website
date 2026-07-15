"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const { login } = useAuth();
  const toast = useToast();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(username, password);
      toast(`Welcome back, ${username}!`, "success");
      router.push("/");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Login failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-sm px-4 py-14">
      <Card className="p-6">
        <h1 className="text-2xl font-bold tracking-tight">Welcome back</h1>
        <p className="mt-1 text-sm text-ink-muted">Log in to your Shopwise account.</p>
        <form onSubmit={onSubmit} className="mt-6 space-y-3">
          <Input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Button type="submit" variant="accent" fullWidth isLoading={loading}>
            Log in
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-ink-muted">
          No account?{" "}
          <Link href="/register" className="font-semibold text-accent hover:underline">
            Sign up
          </Link>
        </p>
      </Card>
    </div>
  );
}
