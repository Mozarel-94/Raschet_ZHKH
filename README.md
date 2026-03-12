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

После запуска приложение будет доступно на `http://localhost:8501`.

## Переменные окружения

Сервис теперь можно настраивать через переменные окружения — это удобно для деплоя из GitHub-репозитория на серверные платформы (Render/Railway/Heroku-like):

- `HOST` (по умолчанию `0.0.0.0`)
- `PORT` (по умолчанию `8501`)
- `SERVICE_ACCOUNT_FILE` (по умолчанию `service_account.json`)
- `SPREADSHEET_ID`
- `WORKSHEET_NAME` (по умолчанию `Расчет`)
- `COLD_WATER_CELL`, `HOT_WATER_CELL`, `ELECTRICITY_DAY_CELL`, `ELECTRICITY_NIGHT_CELL`
- `WATER_TOTAL_CELL`, `ELECTRICITY_TOTAL_CELL`, `GRAND_TOTAL_CELL`
- `FORMULAS_WAIT_SECONDS` (по умолчанию `1.5`)

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

Для проверки доступности добавлен health-check:

- `GET /health` → `ok`
