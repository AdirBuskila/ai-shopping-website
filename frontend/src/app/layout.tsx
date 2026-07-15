import type { Metadata } from "next";
import { Rubik } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";
import { Header } from "@/components/Header";
import { AuthMenu } from "@/components/AuthMenu";

const rubik = Rubik({ variable: "--font-body", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Shopwise — AI-powered electronics store",
  description: "Browse, search, and shop electronics with an AI assistant that knows the catalog.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${rubik.variable} h-full`}>
      <body className="min-h-full flex flex-col font-sans">
        <Providers>
          <Header authSlot={<AuthMenu />} />
          <main className="w-full flex-1">{children}</main>
          <footer className="border-t border-border py-6 text-center text-xs text-ink-subtle">
            Shopwise · a course project · FastAPI + Next.js + OpenAI
          </footer>
        </Providers>
      </body>
    </html>
  );
}
