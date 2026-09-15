"use client";

import { useState } from "react";
import type { Citation } from "@/lib/api";

export default function SourceChips({
  sources,
}: {
  sources: Citation[];
}) {
  const [open, setOpen] = useState(false);
  if (sources.length === 0) return null;
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((v) => !v)}
        className="text-xs text-gray-500 underline underline-offset-2"
        aria-expanded={open}
      >
        {open ? "Скрыть источники" : `Источники (${sources.length})`}
      </button>
      {open && (
        <ul className="mt-2 flex flex-col gap-2">
          {sources.map((s) => (
            <li
              key={s.chunk_id}
              className="rounded-md border border-border bg-muted px-3 py-2 text-xs"
            >
              <div className="font-medium">
                {s.title ?? s.document_id}
                {s.url && (
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="ml-2 underline"
                  >
                    ссылка
                  </a>
                )}
              </div>
              {s.snippet && (
                <p className="mt-1 text-gray-600">{s.snippet}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
