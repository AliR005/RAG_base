"use client";

import type { ModelInfo } from "@/lib/api";

export default function ModelSelect({
  models,
  value,
  onChange,
}: {
  models: ModelInfo[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="text-gray-500">Модель</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-border bg-white px-2 py-1.5 outline-none focus:border-gray-400"
        aria-label="Выбор модели"
      >
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name}
          </option>
        ))}
      </select>
    </label>
  );
}
