"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Creation } from "@/lib/types";
import SwipeCard, { type SwipeCardHandle } from "@/components/SwipeCard";
import EmptyState from "@/components/EmptyState";
import CategoryFilter from "@/components/CategoryFilter";

type Status = "loading" | "ready" | "exhausted" | "error";

export default function FeedPage() {
  const [creation, setCreation] = useState<Creation | null>(null);
  const [status, setStatus] = useState<Status>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [category, setCategory] = useState<string | null>(null);
  const cardRef = useRef<SwipeCardHandle>(null);

  const loadNext = useCallback(async () => {
    setStatus("loading");
    setErrorMessage(null);
    try {
      const res = await api.getRandomFeedItem(category);
      if (res.exhausted || !res.creation) {
        setCreation(null);
        setStatus("exhausted");
      } else {
        setCreation(res.creation);
        setStatus("ready");
      }
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError
          ? err.message
          : "Не получилось загрузить ленту. Проверьте соединение с сервером."
      );
      setStatus("error");
    }
  }, [category]);

  useEffect(() => {
    loadNext();
  }, [loadNext]);

  const handleCategoryChange = useCallback((next: string | null) => {
    setCreation(null); // сразу убираем текущую карточку — фильтр сменился
    setCategory(next);
  }, []);

  const handleSwiped = useCallback(
    async (direction: "like" | "pass") => {
      const current = creation;
      setCreation(null); // карточка уже улетела с экрана
      if (direction === "like" && current) {
        try {
          await api.likeCreation(current.id);
        } catch {
          // Лайк не критичен для продолжения ленты — молча продолжаем.
          // В интерфейсе это не блокирует пользователя, но можно добавить тост об ошибке.
        }
      }
      loadNext();
    },
    [creation, loadNext]
  );

  // Пропущенные ("мимо") и лайкнутые творения исключаются из ленты навсегда —
  // "обновить кучу" просто проверяет, не появилось ли что-то новое,
  // а не возвращает уже просмотренное.
  const handleRefill = useCallback(() => {
    loadNext();
  }, [loadNext]);

  // Клавиатурная альтернатива свайпу: ← мимо, → нравится.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (status !== "ready") return;
      if (e.key === "ArrowRight") cardRef.current?.swipe("like");
      if (e.key === "ArrowLeft") cardRef.current?.swipe("pass");
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [status]);

  return (
    <div className="flex flex-col items-center gap-8">
      <div className="text-center">
        <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-slate-light">
          случайная работа из общей кучи
        </p>
      </div>

      <div className="relative mx-auto w-full max-w-md">
        <CategoryFilter value={category} onChange={handleCategoryChange} />

        {status === "loading" && !creation && (
          <div className="flex h-96 items-center justify-center">
            <span className="font-display italic text-slate-light">
              Достаём из кучи…
            </span>
          </div>
        )}

        {status === "error" && (
          <div className="pinned-card mx-auto max-w-md px-8 py-12 text-center">
            <div className="pin-dot" aria-hidden="true" />
            <p className="mb-4 font-display text-lg italic text-ink">
              Что-то пошло не так
            </p>
            <p className="mb-5 text-sm text-ink/70">{errorMessage}</p>
            <button
              onClick={loadNext}
              className="rounded-full bg-teal px-5 py-2 font-mono text-xs font-bold uppercase tracking-wider text-paper"
            >
              Повторить
            </button>
          </div>
        )}

        {status === "exhausted" && (
          <EmptyState onRefill={handleRefill} loading={false} />
        )}

        {creation && (
          <SwipeCard key={creation.id} ref={cardRef} creation={creation} onSwiped={handleSwiped} />
        )}
      </div>

      {creation && (
        <>
          <div className="flex items-center gap-6">
            <button
              onClick={() => cardRef.current?.swipe("pass")}
              className="stamp-btn border-slate-light/40 bg-board-light text-slate-light hover:border-slate-light"
              aria-label="Пропустить творение"
            >
              ✕
            </button>
            <button
              onClick={() => cardRef.current?.swipe("like")}
              className="stamp-btn border-coral bg-coral/10 text-coral hover:bg-coral/20"
              aria-label="Нравится"
            >
              ♥
            </button>
          </div>

          <p className="font-mono text-[10px] uppercase tracking-widest text-slate-light">
            свайп, клик или стрелки ← →
          </p>
        </>
      )}
    </div>
  );
}
