# Расчет коммунальных платежей (MVP)

MVP-приложение на **Streamlit** для ввода показаний счетчиков и получения итоговых сумм из **Google Sheets**.

> Важно: приложение **не считает** платежи само. Все формулы находятся в Google Sheets.

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Настройка Google Sheets

1. Создайте service account в Google Cloud.
2. Дайте ему доступ к Google Sheets (поделитесь таблицей с `client_email`).
3. Укажите:
   - `SPREADSHEET_ID`
   - данные service account
4. Настройте ячейки в `config.py`.

## Деплой на Streamlit Community Cloud

1. Запушьте репозиторий в GitHub.
2. Откройте [share.streamlit.io](https://share.streamlit.io/).
3. Нажмите **New app** и выберите:
   - Repository: `mozarel-94/Raschet_ZHKH`
   - Branch: `main` (или ваш рабочий)
   - Main file path: `app.py`
4. В настройках приложения откройте **Secrets** и вставьте содержимое по шаблону `.streamlit/secrets.toml.example`.
5. Нажмите **Deploy**.

После деплоя приложение будет доступно по ссылке вида:
`https://<app-name>.streamlit.app`

## Почему не GitHub Pages

GitHub Pages публикует только статические сайты. Streamlit-приложению нужен Python runtime, поэтому его нужно деплоить на Streamlit Cloud или другой backend-хостинг.
