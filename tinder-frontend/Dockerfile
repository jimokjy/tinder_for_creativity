# Многоступенчатая сборка: отдельно ставим зависимости, отдельно собираем,
# отдельно запускаем — итоговый образ не тащит лишний кэш сборки.

# --- 1. Зависимости ---
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# --- 2. Сборка ---
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# ВАЖНО: next.config.js вызывает rewrites() один раз во время `next build`
# и сохраняет результат в .next/routes-manifest.json — переменная
# окружения контейнера, заданная уже ПОСЛЕ сборки образа (в
# docker-compose.yml через environment:), на этот адрес не повлияет.
# Поэтому BACKEND_URL передаётся именно как build-arg.
ARG BACKEND_URL=http://127.0.0.1:8000
ENV BACKEND_URL=$BACKEND_URL

RUN npm run build

# --- 3. Запуск ---
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

CMD ["npm", "run", "start"]
