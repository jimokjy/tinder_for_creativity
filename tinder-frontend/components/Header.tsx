"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const NAV_ITEMS = [
  { href: "/", label: "Лента" },
  { href: "/upload", label: "Сдать работу" },
  { href: "/mine", label: "Мои приколотые" },
];

export default function Header() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <header className="border-b border-white/10">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-5">
        <Link href="/" className="group flex items-baseline gap-2">
          <span className="font-display text-2xl font-semibold italic tracking-tight text-paper">
            Куча
          </span>
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-light">
            анонимная доска
          </span>
        </Link>

        {user && (
          <nav className="flex items-center gap-5 font-mono text-xs uppercase tracking-wider">
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`pb-1 transition-colors ${
                    active
                      ? "border-b-2 border-mustard text-paper"
                      : "text-slate-light hover:text-paper"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}

            <span className="mx-1 h-4 w-px bg-white/15" aria-hidden="true" />

            <span className="text-slate-light" title="Вы вошли под этим логином">
              {user.username}
            </span>
            <button
              onClick={logout}
              className="text-slate-light transition-colors hover:text-coral"
            >
              выйти
            </button>
          </nav>
        )}
      </div>
    </header>
  );
}
