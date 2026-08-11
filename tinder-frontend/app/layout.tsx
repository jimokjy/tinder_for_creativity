import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import AuthGate from "@/components/AuthGate";
import { AuthProvider } from "@/lib/auth-context";

// Шрифты подключены обычными <link>-тегами (а не next/font/google), чтобы
// их загружал браузер пользователя во время работы сайта, а не Docker во
// время сборки образа — next/font/google скачивает файлы шрифтов именно
// на этапе `npm run build`, и если у сборочной среды нет доступа к
// fonts.googleapis.com/fonts.gstatic.com, сборка падает с ошибкой.

export const metadata: Metadata = {
  title: "Куча — доска анонимного творчества",
  description:
    "Выкладывай своё творчество анонимно и листай ленту случайных работ других людей.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,500;0,600;1,400;1,500;1,600&family=Inter:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-body min-h-screen">
        <AuthProvider>
          <Header />
          <main className="mx-auto max-w-3xl px-4 pb-24 pt-8">
            <AuthGate>{children}</AuthGate>
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
