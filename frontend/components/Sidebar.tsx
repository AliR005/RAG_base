"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { api, clearToken, getToken, type Chat } from "@/lib/api";

export const CHATS_CHANGED = "rag:chats-changed";

export default function Sidebar() {
  const pathname = usePathname();
  const [authed, setAuthed] = useState(false);
  const [chats, setChats] = useState<Chat[]>([]);
  const [open, setOpen] = useState(false);

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setAuthed(false);
      return;
    }
    setAuthed(true);
    try {
      setChats(await api.chats());
    } catch {
      setChats([]);
    }
  }, []);

  useEffect(() => {
    void refresh();
    window.addEventListener(CHATS_CHANGED, refresh);
    return () => window.removeEventListener(CHATS_CHANGED, refresh);
  }, [refresh, pathname]);

  if (!authed) return null;

  async function logout() {
    clearToken();
    window.location.href = "/login";
  }

  async function remove(id: string) {
    await api.deleteChat(id).catch(() => undefined);
    await refresh();
    if (window.location.pathname === "/chat") window.location.reload();
  }

  const list = (
    <div className="flex h-full flex-col gap-1 p-3">
      <a
        href="/chat"
        className="rounded-md bg-primary px-3 py-2 text-center text-sm font-medium text-white"
      >
        + Новый чат
      </a>
      <nav aria-label="Сохранённые чаты" className="mt-2 flex flex-1 flex-col gap-1 overflow-y-auto">
        {chats.map((c) => (
          <div
            key={c.id}
            className="group flex items-center gap-1 rounded-md px-2 py-1.5 text-sm hover:bg-muted"
          >
            <a href={`/chat?chat=${c.id}`} className="min-w-0 flex-1 truncate">
              {c.title}
            </a>
            <button
              onClick={() => void remove(c.id)}
              aria-label={`Удалить чат ${c.title}`}
              className="hidden shrink-0 text-gray-400 hover:text-red-600 group-hover:block"
            >
              ×
            </button>
          </div>
        ))}
        {chats.length === 0 && (
          <p className="px-2 text-xs text-gray-400">Чатов пока нет</p>
        )}
      </nav>
      <div className="flex flex-col gap-1 border-t border-border pt-2 text-sm">
        <a href="/documents" className="rounded-md px-2 py-1.5 hover:bg-muted">
          База знаний
        </a>
        <a href="/settings" className="rounded-md px-2 py-1.5 hover:bg-muted">
          Настройки
        </a>
        <button
          onClick={() => void logout()}
          className="rounded-md px-2 py-1.5 text-left text-gray-500 hover:bg-muted"
        >
          Выйти
        </button>
      </div>
    </div>
  );

  return (
    <>
      <button
        className="fixed left-3 top-3 z-20 rounded-md border border-border bg-white px-2 py-1 text-sm md:hidden"
        onClick={() => setOpen((v) => !v)}
        aria-label="Меню"
      >
        ☰
      </button>
      <aside className="hidden w-64 shrink-0 border-r border-border md:block">
        {list}
      </aside>
      {open && (
        <aside className="fixed inset-y-0 left-0 z-10 w-64 border-r border-border bg-white md:hidden">
          {list}
        </aside>
      )}
    </>
  );
}
