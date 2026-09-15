"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  API_URL,
  api,
  getToken,
  type ChatMessage,
  type Citation,
  type ModelInfo,
} from "@/lib/api";
import ModelSelect from "@/components/ModelSelect";
import SourceChips from "@/components/SourceChips";
import { CHATS_CHANGED } from "@/components/Sidebar";

interface ViewMessage {
  id: string;
  role: string;
  content: string;
  model_used: string | null;
  sources: Citation[];
}

export default function ChatPage() {
  return (
    <Suspense fallback={<main className="mx-auto max-w-2xl px-4 py-16" />}>
      <ChatView />
    </Suspense>
  );
}

function ChatView() {
  const searchParams = useSearchParams();
  const [chatId, setChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ViewMessage[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelId, setModelId] = useState("local");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const initial = searchParams.get("chat");
    (async () => {
      try {
        const [fetchedModels] = await Promise.all([
          api.models().catch(() => [] as ModelInfo[]),
        ]);
        setModels(fetchedModels);
        if (fetchedModels.length > 0) setModelId(fetchedModels[0].id);
        if (initial) {
          setChatId(initial);
          const history = await api.messages(initial);
          setMessages(history);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Ошибка загрузки");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const send = useCallback(async () => {
    const query = input.trim();
    if (!query || loading) return;
    setError(null);
    setLoading(true);
    setInput("");
    try {
      let id = chatId;
      let firstInChat = false;
      if (!id) {
        const chat = await api.createChat("Новый чат");
        id = chat.id;
        setChatId(id);
        firstInChat = true;
      }
      const userMsg: ViewMessage = {
        id: `local-${Date.now()}`,
        role: "user",
        content: query,
        model_used: null,
        sources: [],
      };
      const assistantId = `local-${Date.now()}-a`;
      setMessages((prev) => [
        ...prev,
        userMsg,
        { id: assistantId, role: "assistant", content: "", model_used: modelId, sources: [] },
      ]);
      const res = await fetch(`${API_URL}/chats/${id}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ query, model_id: modelId }),
      });
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let doneSources: Citation[] = [];
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data:")) continue;
          const event = JSON.parse(line.slice(5));
          if (event.token) {
            const token: string = event.token;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + token }
                  : m
              )
            );
          }
          if (event.done) doneSources = event.sources ?? [];
        }
      }
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, sources: doneSources } : m
        )
      );
      if (firstInChat && id) {
        const title = query.slice(0, 40);
        await api.renameChat(id, title).catch(() => undefined);
        window.dispatchEvent(new Event(CHATS_CHANGED));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка отправки");
    } finally {
      setLoading(false);
    }
  }, [input, loading, chatId, modelId]);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col px-4 pb-6">
      <header className="flex items-center justify-between py-4">
        <h1 className="text-lg font-semibold">RAG-ассистент</h1>
        <ModelSelect models={models} value={modelId} onChange={setModelId} />
      </header>
      <div className="flex flex-1 flex-col gap-4 overflow-y-auto py-2" role="log" aria-live="polite">
        {messages.length === 0 && (
          <p className="mt-16 text-center text-sm text-gray-400">
            Задайте вопрос по вашим документам
          </p>
        )}
        {messages.map((m) => (
          <article
            key={m.id}
            className={
              m.role === "user"
                ? "self-end rounded-lg bg-primary px-4 py-2 text-sm text-white"
                : "self-start w-full rounded-lg border border-border px-4 py-2 text-sm"
            }
          >
            <p className="whitespace-pre-wrap">{m.content}</p>
            {m.role === "assistant" && m.model_used && (
              <p className="mt-1 text-xs text-gray-400">{m.model_used}</p>
            )}
            {m.role === "assistant" && <SourceChips sources={m.sources} />}
          </article>
        ))}
        <div ref={bottomRef} />
      </div>
      {error && <p className="py-1 text-sm text-red-600">{error}</p>}
      <form
        className="flex gap-2 pt-2"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Введите ваш вопрос"
          aria-label="Вопрос"
          className="flex-1 rounded-md border border-border px-3 py-2 text-sm outline-none focus:border-gray-400"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "…" : "Отправить"}
        </button>
      </form>
    </main>
  );
}
