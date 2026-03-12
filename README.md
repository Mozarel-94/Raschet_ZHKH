# Расчет коммунальных платежей (MVP)

Веб-приложение на Python (WSGI) для ввода показаний счётчиков и получения итоговых сумм из **Google Sheets**.

> Важно: приложение **не считает** платежи само. Все формулы находятся в Google Sheets.

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

<<<<<<< codex/deploy-web-service-to-github-server-dxqw8h
После запуска приложение доступно на `http://localhost:8501`.

## Переменные окружения

- `HOST` (по умолчанию `0.0.0.0`)
- `PORT` (по умолчанию `8501`)
=======
После запуска приложение будет доступно на `http://localhost:8501`.

## Переменные окружения

Сервис теперь можно настраивать через переменные окружения — это удобно для деплоя из GitHub-репозитория на серверные платформы (Render/Railway/Heroku-like):

- `HOST` (по умолчанию `0.0.0.0`)
- `PORT` (по умолчанию `8501`)
- `SERVICE_ACCOUNT_FILE` (по умолчанию `service_account.json`)
>>>>>>> main
- `SPREADSHEET_ID`
- `WORKSHEET_NAME` (по умолчанию `Расчет`)
- `COLD_WATER_CELL`, `HOT_WATER_CELL`, `ELECTRICITY_DAY_CELL`, `ELECTRICITY_NIGHT_CELL`
- `WATER_TOTAL_CELL`, `ELECTRICITY_TOTAL_CELL`, `GRAND_TOTAL_CELL`
- `FORMULAS_WAIT_SECONDS` (по умолчанию `1.5`)
<<<<<<< codex/deploy-web-service-to-github-server-dxqw8h
- `SERVICE_ACCOUNT_FILE` (путь к JSON-файлу ключа, по умолчанию `service_account.json`)
- `SERVICE_ACCOUNT_JSON` (содержимое JSON-ключа сервисного аккаунта строкой; удобно для Render)

Если задан `SERVICE_ACCOUNT_JSON`, он имеет приоритет над `SERVICE_ACCOUNT_FILE`.

## Подготовка Google Sheets

1. Создайте service account в Google Cloud.
2. Поделитесь Google-таблицей с `client_email` сервисного аккаунта.
3. Скопируйте `SPREADSHEET_ID` из URL таблицы.

## Deploy на Render

### Вариант 1: Blueprint (render.yaml)

1. Запушьте репозиторий на GitHub.
2. В Render выберите **New + → Blueprint** и укажите этот репозиторий.
3. Render подхватит `render.yaml` и создаст Web Service автоматически.
4. В Environment добавьте:
   - `SPREADSHEET_ID`
   - `SERVICE_ACCOUNT_JSON` (полный JSON сервисного аккаунта)
5. Нажмите Deploy.

### Вариант 2: Web Service вручную

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:application --bind 0.0.0.0:$PORT --workers 2 --threads 4`
- **Health Check Path:** `/health`

И добавьте переменные окружения `SPREADSHEET_ID` и `SERVICE_ACCOUNT_JSON`.

## Проверка после деплоя

- Откройте `https://<your-service>.onrender.com/health` — должен вернуться `ok`.
- Откройте главную страницу и выполните пробный расчет.
=======

## Настройка Google Sheets

1. Создайте service account в Google Cloud.
2. Дайте ему доступ к Google Sheets (поделитесь таблицей с `client_email`).
3. Сохраните JSON-ключ как `service_account.json` (или укажите другой путь в `SERVICE_ACCOUNT_FILE`).
4. Укажите `SPREADSHEET_ID` и (при необходимости) остальные параметры через переменные окружения.

## Деплой из GitHub на серверную платформу

> Важно: **GitHub Pages** подходит только для статических сайтов. Для этого проекта нужен Python runtime.

### Вариант 1 (рекомендуется): Render

1. Запушьте репозиторий на GitHub.
2. В Render создайте **New Web Service** и подключите GitHub-репозиторий.
3. Render автоматически использует:
   - `requirements.txt` для установки зависимостей;
   - `Procfile` для запуска (`gunicorn app:application ...`).
4. В переменных окружения Render задайте минимум:
   - `SPREADSHEET_ID`
   - `SERVICE_ACCOUNT_FILE`
5. Добавьте файл ключа сервисного аккаунта на сервер (или смонтируйте через Secret File).

### Вариант 2: Railway/другой хостинг

Используйте команду запуска из `Procfile`:

```bash
gunicorn app:application --bind 0.0.0.0:$PORT --workers 2 --threads 4
```

## Техническая проверка
>>>>>>> main

Для проверки доступности добавлен health-check:

<<<<<<< codex/deploy-web-service-to-github-server-dxqw8h
GitHub Pages публикует только статические сайты. Этому проекту нужен Python runtime, поэтому нужен Render (или другой backend-хостинг).
=======
- `GET /health` → `ok`
>>>>>>> main
