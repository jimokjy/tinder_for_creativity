import type {
  Creation,
  CreationWithStats,
  FeedResponse,
  LikeToggleResponse,
  User,
} from "./types";

// Все запросы идут на /api/... — этот путь проксируется самим Next.js-сервером
// на бэкенд (см. rewrites() в next.config.js). Благодаря этому браузер всегда
// обращается только к одному адресу (адресу сайта), что упрощает CORS,
// cookie-авторизацию и не требует менять адрес API при переезде/туннелях.
const API_PREFIX = "/api";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_PREFIX}${path}`, {
    ...options,
    credentials: "include", // важно: так браузер шлёт/принимает cookie авторизации
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
    } catch {
      // тело не JSON — оставляем statusText
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export function resolveFileUrl(fileUrl: string | null): string | null {
  if (!fileUrl) return null;
  if (fileUrl.startsWith("http")) return fileUrl;
  // /uploads/... тоже проксируется Next.js-сервером на бэкенд — можно
  // использовать как обычный относительный путь, без указания хоста.
  return fileUrl;
}

export const api = {
  register: (username: string, password: string) =>
    request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  login: (username: string, password: string) =>
    request<User>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  logout: () => request<{ status: string }>("/auth/logout", { method: "POST" }),

  me: () => request<User>("/auth/me"),

  getRandomFeedItem: (category?: string | null) =>
    request<FeedResponse>(
      `/feed/random${category ? `?category=${encodeURIComponent(category)}` : ""}`
    ),

  likeCreation: (id: string) =>
    request<LikeToggleResponse>(`/likes/${id}`, { method: "POST" }),

  unlikeCreation: (id: string) =>
    request<LikeToggleResponse>(`/likes/${id}`, { method: "DELETE" }),

  reportCreation: (id: string, reason?: string) =>
    request<{ status: string }>(`/creations/${id}/report`, {
      method: "POST",
      body: JSON.stringify({ reason: reason ?? null }),
    }),

  getMyCreations: () => request<CreationWithStats[]>("/creations/mine"),

  deleteCreation: (id: string) =>
    request<void>(`/creations/${id}`, { method: "DELETE" }),

  publishCreation: (formData: FormData) =>
    request<Creation>("/creations", { method: "POST", body: formData }),
};

export { ApiError };
