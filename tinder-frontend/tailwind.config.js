/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        board: {
          DEFAULT: "#10192E", // тёмный фон-стенд ("доска" в мастерской ночью)
          light: "#182238",
        },
        paper: {
          DEFAULT: "#F7F3E8", // бумажные карточки-творения
          dim: "#EDE7D6",
        },
        ink: "#1C1C1C",
        coral: {
          DEFAULT: "#FF5A4E", // лайк / основной CTA
          dim: "#E14A3F",
        },
        mustard: "#F5B942", // булавки, метки категорий
        teal: "#2F7A6E", // вторичный акцент, ссылки
        slate: {
          DEFAULT: "#7C8397", // приглушённый текст на бумаге
          light: "#B8BFD1", // приглушённый текст на тёмном фоне
        },
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Inter", "sans-serif"],
        mono: ['"Space Mono"', "monospace"],
      },
      boxShadow: {
        pinned: "0 18px 40px -12px rgba(0,0,0,0.55)",
        card: "0 8px 24px -8px rgba(0,0,0,0.35)",
      },
      keyframes: {
        "fly-left": {
          "0%": { transform: "translateX(0) rotate(-2deg)", opacity: "1" },
          "100%": { transform: "translateX(-140%) rotate(-24deg)", opacity: "0" },
        },
        "fly-right": {
          "0%": { transform: "translateX(0) rotate(-2deg)", opacity: "1" },
          "100%": { transform: "translateX(140%) rotate(24deg)", opacity: "0" },
        },
      },
    },
  },
  plugins: [],
};
