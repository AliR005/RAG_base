"use client";

import { useCallback, useEffect, useState } from "react";
import { api, uploadDocument, type DocumentInfo } from "@/lib/api";

const STATUS_LABEL: Record<string, string> = {
  pending: "в очереди",
  processing: "обрабатывается",
  done: "готов",
  error: "ошибка",
};

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setDocs(await api.documents());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = setInterval(refresh, 3000);
    return () => clearInterval(timer);
  }, [refresh]);

  async function addUrl(e: React.FormEvent) {
    e.preventDefault();
    const value = url.trim();
    if (!value) return;
    setBusy(true);
    setError(null);
    try {
      await api.createDocument(value);
      setUrl("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка добавления");
    } finally {
      setBusy(false);
    }
  }

  async function addFile(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await uploadDocument(file);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: string) {
    setError(null);
    try {
      await api.deleteDocument(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка удаления");
    }
  }

  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-8">
      <h1 className="text-xl font-semibold">База знаний</h1>
      <p className="mt-1 text-sm text-gray-500">
        Файлы, статьи по ссылке и YouTube-видео. Статусы обновляются сами.
      </p>

      <form onSubmit={addUrl} className="mt-6 flex gap-2">
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://… статья или YouTube-видео"
          aria-label="Ссылка на источник"
          className="flex-1 rounded-md border border-border px-3 py-2 text-sm outline-none focus:border-gray-400"
        />
        <button
          type="submit"
          disabled={busy || !url.trim()}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Добавить
        </button>
      </form>

      <label className="mt-3 flex items-center gap-2 text-sm">
        <span className="text-gray-500">Или файл</span>
        <input
          type="file"
          accept=".pdf,.docx,.pptx,.xlsx,.html,.htm,.md,.png,.jpg,.jpeg"
          disabled={busy}
          onChange={(e) => void addFile(e.target.files?.[0])}
          className="text-sm"
        />
      </label>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <ul className="mt-6 flex flex-col gap-2">
        {docs.map((d) => (
          <li
            key={d.id}
            className="flex items-start justify-between gap-3 rounded-lg border border-border px-4 py-3 text-sm"
          >
            <div className="min-w-0">
              <p className="truncate font-medium">
                {d.title ?? d.origin}
              </p>
              <p className="mt-0.5 text-xs text-gray-500">
                {d.source_type} · {STATUS_LABEL[d.status] ?? d.status}
                {d.status === "error" && d.error ? ` — ${d.error}` : ""}
              </p>
            </div>
            <button
              onClick={() => void remove(d.id)}
              className="shrink-0 rounded-md border border-border px-2 py-1 text-xs text-gray-500 hover:text-red-600"
              aria-label={`Удалить ${d.title ?? d.id}`}
            >
              Удалить
            </button>
          </li>
        ))}
        {docs.length === 0 && (
          <p className="text-sm text-gray-400">
            Пока пусто — добавьте первый источник выше.
          </p>
        )}
      </ul>
    </main>
  );
}
