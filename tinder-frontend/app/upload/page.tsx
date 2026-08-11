"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { CATEGORIES } from "@/lib/categories";

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<string>(CATEGORIES[0]);
  const [fileName, setFileName] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const file = fileInputRef.current?.files?.[0];
    if (!file && !description.trim()) {
      setError("Приложите файл или хотя бы напишите описание — иначе сдавать нечего.");
      return;
    }

    const formData = new FormData();
    if (title.trim()) formData.append("title", title.trim());
    if (description.trim()) formData.append("description", description.trim());
    formData.append("category", category);
    if (file) formData.append("file", file);

    setSubmitting(true);
    try {
      await api.publishCreation(formData);
      setDone(true);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Не получилось отправить работу. Попробуйте ещё раз."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <div className="pinned-card mx-auto max-w-md px-8 py-14 text-center">
        <div className="pin-dot" aria-hidden="true" />
        <p className="mb-3 font-display text-2xl italic text-ink">Приколото!</p>
        <p className="mb-6 text-sm leading-relaxed text-ink/70">
          Работа анонимно добавлена в общую кучу — теперь её могут увидеть
          другие в ленте.
        </p>
        <div className="flex justify-center gap-3">
          <button
            onClick={() => {
              setDone(false);
              setTitle("");
              setDescription("");
              setFileName(null);
              if (fileInputRef.current) fileInputRef.current.value = "";
            }}
            className="rounded-full border border-ink/20 px-5 py-2 font-mono text-xs font-bold uppercase tracking-wider text-ink"
          >
            Сдать ещё одну
          </button>
          <button
            onClick={() => router.push("/")}
            className="rounded-full bg-coral px-5 py-2 font-mono text-xs font-bold uppercase tracking-wider text-paper"
          >
            В ленту
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md">
      <form
        onSubmit={handleSubmit}
        className="pinned-card space-y-5 border-t-2 border-dashed border-ink/15 px-6 py-8"
      >
        <div className="pin-dot" aria-hidden="true" />

        <div>
          <label htmlFor="title" className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-slate">
            Название (необязательно)
          </label>
          <input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={200}
            placeholder="Без названия"
            className="w-full rounded border border-ink/15 bg-white/60 px-3 py-2 font-body text-sm text-ink outline-none focus:border-coral"
          />
        </div>

        <div>
          <label htmlFor="category" className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-slate">
            Категория
          </label>
          <select
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full rounded border border-ink/15 bg-white/60 px-3 py-2 font-body text-sm text-ink outline-none focus:border-coral"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="description" className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-slate">
            Описание {`{`}или сам текст, если это стихи/проза{`}`}
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            placeholder="Пара слов о работе…"
            className="w-full resize-none rounded border border-ink/15 bg-white/60 px-3 py-2 font-body text-sm text-ink outline-none focus:border-coral"
          />
        </div>

        <div>
          <label className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-slate">
            Файл (фото или аудио, необязательно)
          </label>
          <label
            htmlFor="file"
            className="flex cursor-pointer items-center justify-between rounded border border-dashed border-ink/25 px-3 py-3 text-sm text-ink/70 hover:border-coral"
          >
            <span className="truncate">{fileName ?? "Выбрать файл…"}</span>
            <span className="shrink-0 font-mono text-xs text-teal">обзор</span>
          </label>
          <input
            id="file"
            ref={fileInputRef}
            type="file"
            accept="image/*,audio/*"
            className="hidden"
            onChange={(e) => setFileName(e.target.files?.[0]?.name ?? null)}
          />
        </div>

        {error && (
          <p className="rounded border border-coral/40 bg-coral/10 px-3 py-2 text-xs text-coral">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-full bg-coral py-3 font-mono text-xs font-bold uppercase tracking-wider text-paper transition-transform hover:-translate-y-0.5 disabled:opacity-60"
        >
          {submitting ? "Сдаём анонимно…" : "Приколоть к куче"}
        </button>

        <p className="text-center text-[11px] leading-relaxed text-ink/50">
          Никто не узнает, что это вы — ни автор, ни зрители не привязаны к
          имени или аккаунту.
        </p>
      </form>
    </div>
  );
}
