"use client";

import { useEffect, useState } from "react";
import { api, clearToken } from "@/lib/api";

export default function SettingsPage() {
  const [email, setEmail] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .me()
      .then((u) => setEmail(u.email))
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Ошибка")
      );
  }, []);

  function logout() {
    clearToken();
    window.location.href = "/login";
  }

  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-8">
      <h1 className="text-xl font-semibold">Настройки</h1>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <dl className="mt-6 rounded-lg border border-border px-4 py-3 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-gray-500">Email</dt>
          <dd>{email || "…"}</dd>
        </div>
      </dl>
      <button
        onClick={logout}
        className="mt-4 rounded-md border border-border px-4 py-2 text-sm hover:bg-muted"
      >
        Выйти из аккаунта
      </button>
    </main>
  );
}
