import type { Creation } from "@/lib/types";
import { resolveFileUrl } from "@/lib/api";

export default function CreationMedia({ creation }: { creation: Creation }) {
  const url = resolveFileUrl(creation.file_url);

  if (creation.media_type === "image" && url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- URL зависит от бэкенда, домен неизвестен заранее
      <img
        src={url}
        alt={creation.title ?? "Творение без названия"}
        className="h-80 w-full select-none object-cover"
        draggable={false}
      />
    );
  }

  if (creation.media_type === "audio" && url) {
    return (
      <div className="flex h-80 w-full flex-col items-center justify-center gap-4 bg-paper-dim px-6">
        <span className="font-display text-5xl italic text-slate">♪</span>
        <audio controls src={url} className="w-full max-w-xs" />
      </div>
    );
  }

  // Текстовое творение (или неизвестный тип без файла) — показываем как есть.
  return (
    <div className="flex h-80 w-full items-center justify-center bg-paper-dim px-8 py-6">
      <p className="max-h-full overflow-y-auto whitespace-pre-line text-center font-display text-lg italic leading-relaxed text-ink">
        {creation.description || "Без описания"}
      </p>
    </div>
  );
}
