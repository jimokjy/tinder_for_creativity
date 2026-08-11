export default function Tag({ label }: { label: string }) {
  return (
    <span className="shrink-0 rounded-full border border-mustard/60 bg-mustard/15 px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-mustard">
      {label}
    </span>
  );
}
