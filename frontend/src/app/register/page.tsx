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

export default function RegisterPage() {
  const { register } = useAuth();
  const toast = useToast();
  const router = useRouter();
  const [form, setForm] = useState({ username: "", email: "", password: "", first_name: "", city: "" });
  const [loading, setLoading] = useState(false);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(form);
      toast("Account created — you're in!", "success");
      router.push("/");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Registration failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-sm py-10">
      <Card className="p-6">
        <h1 className="text-2xl font-bold tracking-tight">Create your account</h1>
        <p className="mt-1 text-sm text-ink-muted">Join NovaShop to save favorites and check out.</p>
        <form onSubmit={onSubmit} className="mt-6 space-y-3">
          <Input placeholder="Username" value={form.username} onChange={set("username")} required />
          <Input type="email" placeholder="Email" value={form.email} onChange={set("email")} required />
          <Input type="password" placeholder="Password" value={form.password} onChange={set("password")} required minLength={6} />
          <div className="grid grid-cols-2 gap-3">
            <Input placeholder="First name" value={form.first_name} onChange={set("first_name")} />
            <Input placeholder="City" value={form.city} onChange={set("city")} />
          </div>
          <Button type="submit" variant="accent" fullWidth isLoading={loading}>
            Create account
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-ink-muted">
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-accent hover:underline">
            Log in
          </Link>
        </p>
      </Card>
    </div>
  );
}
