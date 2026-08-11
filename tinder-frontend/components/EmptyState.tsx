interface EmptyStateProps {
  onRefill: () => void;
  loading?: boolean;
}

export default function EmptyState({ onRefill, loading }: EmptyStateProps) {
  return (
    <div className="pinned-card mx-auto flex max-w-sm flex-col items-center gap-4 px-8 py-14 text-center">
      <div className="pin-dot" aria-hidden="true" />
      <p className="font-display text-2xl italic text-ink">Куча опустела</p>
      <p className="text-sm leading-relaxed text-ink/70">
        Вы пролистали все работы, которые пока лежат в общей куче. Загляните
        позже — или начните смотреть заново.
      </p>
      <button
        onClick={onRefill}
        disabled={loading}
        className="mt-2 rounded-full bg-coral px-6 py-2.5 font-mono text-xs font-bold uppercase tracking-wider text-paper transition-transform hover:-translate-y-0.5 disabled:opacity-60"
      >
        {loading ? "Открываем заново…" : "Смотреть заново"}
      </button>
    </div>
  );
}
