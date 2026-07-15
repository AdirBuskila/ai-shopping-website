"use client";

import { useEffect, useRef, useState } from "react";
import { Sparkles, Send, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/utils";
import { Markdown } from "@/components/ui/Markdown";
import { ChatSources } from "@/components/store/ChatSources";
import { useChat } from "@/hooks/useChat";

const SUGGESTIONS = [
  "What's a good phone under $400?",
  "Do you have any Apple products in stock?",
  "Recommend wireless earbuds",
];

export default function ChatPage() {
  const { messages, remaining, available, sending, send, reset } = useChat();
  const [text, setText] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const blocked = remaining !== null && remaining <= 0;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const t = text.trim();
    if (!t || sending || blocked) return;
    send(t);
    setText("");
  };

  return (
    <div className="mx-auto flex h-[calc(100dvh-6.5rem)] w-full max-w-4xl flex-col px-3 py-4 sm:px-4 sm:py-6">
      <div className="flex items-center justify-between gap-2 pb-3 sm:pb-4">
        <div className="flex min-w-0 items-center gap-2">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-brand-gradient text-white">
            <Sparkles className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <h1 className="truncate text-base font-bold leading-tight sm:text-lg">Shopping assistant</h1>
            <p className="hidden text-xs text-ink-muted sm:block">Grounded in our live catalog</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          {remaining !== null && (
            <Badge variant={blocked ? "danger" : "neutral"}>{remaining} left</Badge>
          )}
          <button onClick={reset} className="flex items-center gap-1 text-sm text-ink-muted hover:text-ink">
            <RotateCcw className="h-3.5 w-3.5" /> <span className="hidden sm:inline">New chat</span>
          </button>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto rounded-2xl border border-border bg-surface p-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <Sparkles className="h-10 w-10 text-accent" />
            <p className="max-w-sm text-ink-muted">
              Ask about products, prices, stock, or recommendations — I only answer from our catalog.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full border border-border-strong px-3 py-1.5 text-sm text-ink-muted hover:border-ink hover:text-ink"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
            <div
              className={cn(
                "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm",
                m.role === "user"
                  ? "bg-ink text-white"
                  : "bg-surface-muted text-ink",
              )}
            >
              {m.role === "assistant" ? (
                <Markdown>{m.content}</Markdown>
              ) : (
                <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
              )}
              {m.role === "assistant" && m.sources && <ChatSources sources={m.sources} />}
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-surface-muted px-4 py-3">
              <Spinner size="sm" className="text-ink-muted" />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {!available && (
        <p className="pt-2 text-center text-sm text-warning-ink">The assistant is currently unavailable.</p>
      )}

      <form onSubmit={submit} className="flex gap-2 pt-4">
        <Input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={blocked ? "Prompt limit reached — start a new chat" : "Ask about a product…"}
          disabled={blocked || sending}
        />
        <Button type="submit" variant="accent" disabled={blocked || sending || !text.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}
