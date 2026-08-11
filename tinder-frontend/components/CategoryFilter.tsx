"use client";

import { CATEGORIES } from "@/lib/categories";

interface CategoryFilterProps {
  value: string | null;
  onChange: (value: string | null) => void;
}

export default function CategoryFilter({ value, onChange }: CategoryFilterProps) {
  return (
    <div className="absolute -top-3 right-3 z-30 rotate-2">
      <div className="flex items-center rounded-sm border border-mustard/60 bg-paper px-2 py-1 shadow-card">
        <label htmlFor="category-filter" className="sr-only">
          Фильтр по категории
        </label>
        <select
          id="category-filter"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value || null)}
          className="cursor-pointer bg-transparent pr-1 font-mono text-[10px] font-bold uppercase tracking-wider text-ink outline-none"
        >
          <option value="">Все категории</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
