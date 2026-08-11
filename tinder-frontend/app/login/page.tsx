"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";

type Mode = "login" | "register";

const SILAEDER_ERROR_MESSAGES: Record<string, string> = {
  auth_failed: "Не получилось войти через ЛК Силаэдра. Попробуйте ещё раз.",
  no_sub: "ЛК Силаэдра не передал данные пользователя. Попробуйте ещё раз.",
  user_not_found: "Аккаунт не найден. Попробуйте войти ещё раз.",
  already_linked: "Эта учётка ЛК Силаэдра уже привязана к другому аккаунту.",
  link_expired: "Ссылка подтверждения устарела или уже использована.",
};

// useSearchParams требует границы Suspense в App Router — выносим её
// использование в отдельный компонент, а не в саму страницу.
function SilaederNotice() {
  const searchParams = useSearchParams();
  const silaederError = searchParams.get("silaeder_error");
  const silaederPending = searchParams.get("silaeder_pending") === "1";

  if (!silaederError && !silaederPending) return null;

  return (
    <>
      {silaederPending && (
        <p className="mb-4 w-full rounded border border-mustard/50 bg-mustard/10 px-3 py-2 text-center text-xs text-mustard">
          На вашу почту отправлена ссылка подтверждения — перейдите по ней,
          чтобы привязать ЛК Силаэдра к существующему аккаунту.
        </p>
      )}
      {silaederError && (
        <p className="mb-4 w-full rounded border border-coral/40 bg-coral/10 px-3 py-2 text-center text-xs text-coral">
          {SILAEDER_ERROR_MESSAGES[silaederError] ?? "Не получилось войти через ЛК Силаэдра."}
        </p>
      )}
    </>
  );
}

export default function LoginPage() {
  const { refresh } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "register") {
        await api.register(username, password);
      } else {
        await api.login(username, password);
      }
      await refresh(); // подтянет пользователя и AuthGate сам перекинет на ленту
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Что-то пошло не так. Попробуйте ещё раз."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-sm flex-col items-center justify-center">
      <div className="mb-8 text-center">
        <p className="font-display text-3xl font-semibold italic text-paper">Куча</p>
        <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.25em] text-slate-light">
          анонимная доска творчества
        </p>
      </div>

      <Suspense fallback={null}>
        <SilaederNotice />
      </Suspense>

      <form onSubmit={handleSubmit} className="pinned-card w-full space-y-4 px-6 py-8">
        <div className="pin-dot" aria-hidden="true" />

        <div className="flex justify-center gap-1 font-mono text-xs uppercase tracking-wider">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`rounded-full px-3 py-1 transition-colors ${
              mode === "login" ? "bg-ink text-paper" : "text-ink/50"
            }`}
          >
            Вход
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={`rounded-full px-3 py-1 transition-colors ${
              mode === "register" ? "bg-ink text-paper" : "text-ink/50"
            }`}
          >
            Регистрация
          </button>
        </div>

        <div>
          <label htmlFor="username" className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-slate">
            Логин
          </label>
          <input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
            minLength={3}
            maxLength={30}
            className="w-full rounded border border-ink/15 bg-white/60 px-3 py-2 font-body text-sm text-ink outline-none focus:border-coral"
          />
        </div>

        <div>
          <label htmlFor="password" className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-slate">
            Пароль
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            required
            minLength={6}
            className="w-full rounded border border-ink/15 bg-white/60 px-3 py-2 font-body text-sm text-ink outline-none focus:border-coral"
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
          {submitting
            ? "Секунду…"
            : mode === "login"
            ? "Войти"
            : "Создать аккаунт"}
        </button>

        <div className="flex items-center gap-3 pt-1">
          <span className="h-px flex-1 bg-ink/10" aria-hidden="true" />
          <span className="font-mono text-[10px] uppercase tracking-wider text-ink/40">или</span>
          <span className="h-px flex-1 bg-ink/10" aria-hidden="true" />
        </div>

        {/* Обычная ссылка, а не onClick+fetch — браузер должен реально
            перейти на lk.silaeder.ru и вернуться обратно по редиректу. */}
        <a
          href="/auth/silaeder/login"
          className="flex w-full items-center justify-center rounded-full border-2 border-teal py-3 font-mono text-xs font-bold uppercase tracking-wider text-teal transition-transform hover:-translate-y-0.5"
        >
          {mode === "login" ? "Войти через ЛК Силаэдра" : "Зарегистрироваться через ЛК Силаэдра"}
        </a>

        <p className="text-center text-[11px] leading-relaxed text-ink/50">
          Аккаунт нужен только для того, чтобы вы не теряли доступ к своим
          работам. Ваш логин никому не виден — в ленте и лайках всё
          по-прежнему анонимно.
        </p>
      </form>
    </div>
  );
}
