import type { Metadata } from "next";
import { Rubik } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { Providers } from "@/components/Providers";
import { Header } from "@/components/Header";

const rubik = Rubik({ variable: "--font-body", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NovaShop — AI-powered electronics store",
  description: "Browse, search, and shop electronics with an AI assistant that knows the catalog.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${rubik.variable} h-full`}>
      <body className="min-h-full flex flex-col font-sans">
        <Providers>
          <Header
            authSlot={
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
            }
          />
          <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
          <footer className="border-t border-border py-6 text-center text-xs text-ink-subtle">
            NovaShop · a course project · FastAPI + Next.js + OpenAI
          </footer>
        </Providers>
      </body>
    </html>
  );
}
