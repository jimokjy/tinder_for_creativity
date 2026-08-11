"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { CreationWithStats } from "@/lib/types";
import { resolveFileUrl } from "@/lib/api";

export default function MinePage() {
  const [items, setItems] = useState<CreationWithStats[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMyCreations()
      .then(setItems)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Не получилось загрузить ваши работы.")
      );
  }, []);

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await api.deleteCreation(id);
      setItems((prev) => (prev ? prev.filter((c) => c.id !== id) : prev));
    } catch {
      // молча оставляем карточку, если удаление не удалось
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <div className="mb-8 text-center">
        <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-slate-light">
          то, что вы прикололи к куче
        </p>
      </div>

      {error && (
        <p className="mx-auto max-w-sm rounded border border-coral/40 bg-coral/10 px-4 py-3 text-center text-sm text-coral">
          {error}
        </p>
      )}

      {!items && !error && (
        <p className="text-center font-display italic text-slate-light">Заглядываем на доску…</p>
      )}

      {items && items.length === 0 && (
        <div className="pinned-card mx-auto max-w-sm px-8 py-14 text-center">
          <div className="pin-dot" aria-hidden="true" />
          <p className="mb-3 font-display text-xl italic text-ink">Тут пока пусто</p>
          <p className="mb-6 text-sm text-ink/70">
            Вы ещё не сдавали работы в общую кучу.
          </p>
          <Link
            href="/upload"
            className="inline-block rounded-full bg-coral px-5 py-2 font-mono text-xs font-bold uppercase tracking-wider text-paper"
          >
            Сдать первую
          </Link>
        </div>
      )}

      {items && items.length > 0 && (
        <div className="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-3">
          {items.map((c, i) => {
            const rotation = ((i * 37) % 5) - 2; // стабильный лёгкий разброс наклона
            const fileUrl = resolveFileUrl(c.file_url);
            return (
              <div
                key={c.id}
                className="pinned-card group relative px-3 pb-4 pt-6"
                style={{ transform: `rotate(${rotation}deg)` }}
              >
                <div className="pin-dot h-4 w-4" aria-hidden="true" />

                {c.is_hidden && (
                  <span className="absolute right-2 top-2 z-10 rounded bg-ink/80 px-1.5 py-0.5 font-mono text-[9px] uppercase text-paper">
                    скрыто
                  </span>
                )}

                {fileUrl && c.media_type === "image" ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={fileUrl}
                    alt={c.title ?? ""}
                    className="mb-2 h-28 w-full rounded object-cover"
                  />
                ) : (
                  <div className="mb-2 flex h-28 w-full items-center justify-center rounded bg-paper-dim">
                    <span className="font-display text-2xl italic text-slate">
                      {c.media_type === "audio" ? "♪" : "✎"}
                    </span>
                  </div>
                )}

                <p className="truncate font-display text-sm font-semibold text-ink">
                  {c.title || "Без названия"}
                </p>

                <div className="mt-2 flex items-center justify-between">
                  <span className="font-mono text-xs text-coral">♥ {c.likes_count}</span>
                  <button
                    onClick={() => handleDelete(c.id)}
                    disabled={deletingId === c.id}
                    className="font-mono text-[10px] uppercase tracking-wider text-slate opacity-0 transition-opacity hover:text-coral group-hover:opacity-100 disabled:opacity-100"
                  >
                    {deletingId === c.id ? "…" : "снять"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
