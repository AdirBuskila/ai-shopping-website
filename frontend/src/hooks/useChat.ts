"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { ChatResponse, ProductRef } from "@/lib/types";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: ProductRef[];
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [remaining, setRemaining] = useState<number | null>(null);
  const [available, setAvailable] = useState(true);
  const [sending, setSending] = useState(false);
  const sessionRef = useRef<string>("");

  useEffect(() => {
    let s = localStorage.getItem("chat_session");
    if (!s) {
      s = crypto.randomUUID();
      localStorage.setItem("chat_session", s);
    }
    sessionRef.current = s;
  }, []);

  const send = useCallback(async (text: string) => {
    setMessages((m) => [...m, { role: "user", content: text }]);
    setSending(true);
    try {
      const res = await api.post<ChatResponse>("/chat", {
        message: text,
        session_id: sessionRef.current,
      });
      setMessages((m) => [...m, { role: "assistant", content: res.reply, sources: res.sources }]);
      setRemaining(res.remaining_prompts);
      setAvailable(res.available);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Something went wrong reaching the assistant. Please try again." },
      ]);
    } finally {
      setSending(false);
    }
  }, []);

  const reset = useCallback(() => {
    const s = crypto.randomUUID();
    localStorage.setItem("chat_session", s);
    sessionRef.current = s;
    setMessages([]);
    setRemaining(null);
    setAvailable(true);
  }, []);

  return { messages, remaining, available, sending, send, reset };
}
