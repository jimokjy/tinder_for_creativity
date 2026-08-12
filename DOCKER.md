# Запуск через Docker Compose

## Структура

```
tinder-app/
  tinder-backend/     - FastAPI-бэкенд + Dockerfile
  tinder-frontend/     - Next.js-фронтенд + Dockerfile
  docker-compose.yml   - объединяет оба сервиса
```

Ничего никуда переносить не нужно — все пути в `docker-compose.yml` уже
настроены на эту структуру папок "как есть".

## Запуск

```bash
# Настройте бэкенд (обязательно смените JWT_SECRET_KEY!)
cp tinder-backend/.env.example tinder-backend/.env
# откройте tinder-backend/.env и впишите свой секрет, например:
# python -c "import secrets; print(secrets.token_hex(32))"

# Соберите и запустите оба сервиса
docker compose up --build
```

Фронтенд будет на http://localhost:3000, бэкенд — на http://localhost:8000
(документация API — http://localhost:8000/docs).

Если эти порты у вас уже заняты, скопируйте `.env.example` в `.env` в
корне репозитория и поменяйте `BACKEND_PORT`/`FRONTEND_PORT` — Docker
Compose подхватывает `.env` автоматически:
```bash
cp .env.example .env
```

Дальше для повседневного запуска (без пересборки) достаточно:
```bash
docker compose up
```
Остановить:
```bash
docker compose down
```

## Как устроено

- **Бэкенд** — обычный образ на `python:3.12-slim`, зависимости ставятся
  из `requirements.txt` отдельным слоем для кэширования.
- **Фронтенд** — многоступенчатая сборка на `node:20-alpine`: сначала
  ставятся зависимости, затем собирается прод-версия Next.js, в финальный
  образ попадает только собранный результат.
- **Данные бэкенда сохраняются между перезапусками** через именованные
  Docker-тома:
  - `backend_data` — файл базы данных SQLite (`/app/data/app.db`)
  - `backend_uploads` — загруженные пользователями файлы (`/app/uploads`)

  Если хотите начать с чистой базы — удалите тома:
  ```bash
  docker compose down -v
  ```

## Как фронтенд находит бэкенд

Браузер никогда не обращается к бэкенду напрямую. Next.js-сервер сам
проксирует запросы `/api/*` и `/uploads/*` на бэкенд — это настроено в
`tinder-frontend/next.config.js` через `rewrites()`. Плюс подхода: браузеру
достаточно знать только адрес самого сайта, не нужен CORS, а адрес бэкенда
можно менять без пересборки *браузерного* кода.

Важный нюанс: Next.js вызывает `rewrites()` **один раз, во время
`npm run build`**, и сохраняет получившийся адрес в
`.next/routes-manifest.json` — при обычном старте контейнера (`next start`)
эта функция уже не перевызывается. Поэтому `BACKEND_URL` нужно знать именно
**на этапе сборки образа**, а не только во время его запуска — в
`docker-compose.yml` он передаётся как `build.args`, а не как `environment:`:
```yaml
build:
  args:
    BACKEND_URL: ${BACKEND_URL:-http://backend:8000}
```
`backend` здесь — имя сервиса из этого же `docker-compose.yml`, Docker сам
резолвит его в адрес нужного контейнера внутри общей сети. Если вместо
этого указать `localhost`/`127.0.0.1` — контейнер фронтенда будет стучаться
сам в себя, а не в бэкенд, и вы получите `ECONNREFUSED`.

Значение по умолчанию (`http://backend:8000`) подходит, пока оба сервиса
запускаются этим же `docker-compose.yml` на одном сервере. Если бэкенд
вынесен на отдельный внешний сервер/домен — задайте `BACKEND_URL` в
корневом `.env` (см. `.env.example`), например `BACKEND_URL=https://api.example.ru`.

**Если меняете `BACKEND_URL`** — простого `docker compose up` (без
`--build`) недостаточно, старый адрес уже зашит в собранный образ:
```bash
docker compose up --build
```

Если разворачиваете не через этот `docker-compose.yml` (например, вручную
собираете образ), передайте build-arg явно:
```bash
docker build --build-arg BACKEND_URL=http://ваш-адрес:8000 ./tinder-frontend
```

## Что стоит доделать перед реальным продакшеном

Для запуска на сервере (публичный домен) используйте
`tinder-backend/.env.production.example` вместо `.env.example` — там те
же переменные, но со значениями под публичный домен (`APP_URL`,
`CORS_ORIGINS`, `CRM_OIDC_REDIRECT_URI`) вместо `localhost`:
```bash
cp tinder-backend/.env.production.example tinder-backend/.env
# отредактируйте .env: домен и секреты (см. пункт 0 ниже)
```

0. **Если включаете вход через ЛК Силаэдра** — при запуске через
   `docker compose` задайте `APP_URL`, `CRM_OIDC_*` и
   `SESSION_SECRET_KEY` в **корневом** `.env` (см. `.env.example`), а не
   в `tinder-backend/.env` — `docker-compose.yml` прокидывает эти
   переменные в контейнер именно оттуда, и то, что записано в
   `tinder-backend/.env`, для них не используется. `MAIL_*` (если нужны
   письма подтверждения) — по-прежнему в `tinder-backend/.env`.
   Redirect URI для регистрации в ЛК Силаэдра: `{APP_URL}/auth/silaeder/callback`.
   Пересборка образа не нужна — это runtime-переменные бэкенда, в
   отличие от `BACKEND_URL` фронтенда.

1. **PostgreSQL вместо SQLite** — для этого добавьте отдельный сервис
   `db:` (образ `postgres:16`) в `docker-compose.yml` и поменяйте
   `DATABASE_URL` в окружении бэкенда на
   `postgresql+psycopg2://user:password@db:5432/creations_db`
   (плюс `psycopg2-binary` в `requirements.txt`).
2. **HTTPS** — сейчас всё поднимается по http; для реального домена
   нужен обратный прокси (например, Caddy или nginx + certbot) перед
   обоими сервисами. Пример для nginx:

   ```bash
   sudo apt install nginx certbot python3-certbot-nginx

   sudo cp nginx/tinder.conf.example /etc/nginx/sites-available/tinder
   # отредактируйте server_name (домен) и порт в proxy_pass, если меняли
   # FRONTEND_PORT

   sudo ln -s /etc/nginx/sites-available/tinder /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx

   sudo certbot --nginx -d example.ru
   ```
   `certbot` сам получит сертификат, допишет SSL-настройки в конфиг и
   добавит редирект с http на https.

   Проксировать наружу нужен только фронтенд (`FRONTEND_PORT`, по
   умолчанию 3000) — сам Next.js-сервер уже проксирует `/api/*`,
   `/uploads/*` и `/auth/silaeder/*` на бэкенд внутри docker-сети (см.
   "Как фронтенд находит бэкенд" выше). Порт бэкенда (`BACKEND_PORT`)
   можно не открывать наружу вовсе — например, публиковать его только на
   loopback, поменяв в `docker-compose.yml`:
   ```yaml
   ports:
     - "127.0.0.1:${BACKEND_PORT:-8000}:8000"
   ```

   После настройки HTTPS не забудьте поменять `APP_URL`,
   `CORS_ORIGINS` и `CRM_OIDC_REDIRECT_URI` в `tinder-backend/.env` на
   `https://` (см. пункт 0 выше) — иначе редиректы после логина и OIDC
   не будут работать.
3. **Хранилище файлов** — для продакшн-нагрузки лучше вынести
   `/app/uploads` в S3-совместимое хранилище вместо тома на диске
   (см. `app/storage.py` в бэкенде).
