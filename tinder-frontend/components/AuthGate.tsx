"use client";

import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const PUBLIC_ROUTES = new Set(["/login"]);

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const isPublic = PUBLIC_ROUTES.has(pathname);

  // Пока не знаем, авторизован ли пользователь — не показываем ни защищённый
  // контент, ни форму логина, чтобы не было "мигания" чужого экрана.
  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <span className="font-display italic text-slate-light">Открываем доску…</span>
      </div>
    );
  }

  // AuthProvider уже инициировал редирект в нужную сторону — здесь просто
  // не рендерим контент, которому пока не место (защищённый гостю,
  // либо форму логина авторизованному).
  if (!user && !isPublic) return null;
  if (user && isPublic) return null;

  return <>{children}</>;
}
