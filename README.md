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

После запуска приложение доступно на `http://localhost:8501`.

## Переменные окружения

- `HOST` (по умолчанию `0.0.0.0`)
- `PORT` (по умолчанию `8501`)
- `SPREADSHEET_ID`
- `WORKSHEET_NAME` (по умолчанию `Расчет`)
- `COLD_WATER_CELL`, `HOT_WATER_CELL`, `ELECTRICITY_DAY_CELL`, `ELECTRICITY_NIGHT_CELL`
- `WATER_TOTAL_CELL`, `ELECTRICITY_TOTAL_CELL`, `GRAND_TOTAL_CELL`
- `FORMULAS_WAIT_SECONDS` (по умолчанию `1.5`)
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

## Почему не GitHub Pages

GitHub Pages публикует только статические сайты. Этому проекту нужен Python runtime, поэтому нужен Render (или другой backend-хостинг).
