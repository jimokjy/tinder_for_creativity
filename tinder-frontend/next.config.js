// Адрес бэкенда С ТОЧКИ ЗРЕНИЯ САМОГО NEXT.JS-СЕРВЕРА (не браузера!).
// Next.js и FastAPI работают на одном ноутбуке, поэтому это всегда localhost,
// даже когда сайт открыт снаружи через туннель — наружу торчит только Next.js.
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
      },
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },

  // Проксируем запросы к бэкенду через сам Next.js-сервер. Благодаря этому
  // браузер всегда обращается только к одному адресу (адресу фронтенда) —
  // не нужен CORS, не нужно вручную менять адрес API при каждом перезапуске
  // туннеля, и cookie авторизации работает без сложностей с доменами.
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND_URL}/:path*` },
      { source: "/uploads/:path*", destination: `${BACKEND_URL}/uploads/:path*` },
      // Отдельно от /api — чтобы Redirect URI/Post-logout Redirect URI,
      // зарегистрированные в ЛК Силаэдра, совпадали буквально с адресом
      // сайта (https://example.ru/auth/silaeder/callback), без /api.
      { source: "/auth/silaeder/:path*", destination: `${BACKEND_URL}/auth/silaeder/:path*` },
    ];
  },
};

module.exports = nextConfig;
