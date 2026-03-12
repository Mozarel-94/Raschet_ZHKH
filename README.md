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


## Troubleshooting Streamlit Cloud

### Ошибка с `make_server(...)` / `socket.bind` в логах
Если в логе есть traceback c `make_server(HOST, PORT, application)`, это значит, что в деплой попала **старая версия** (WSGI), а не текущий Streamlit-код.

Что сделать:
1. Проверьте в Streamlit Cloud:
   - **Repository**: `mozarel-94/Raschet_ZHKH`
   - **Branch**: актуальная ветка, куда запушен последний коммит
   - **Main file path**: `app.py`
2. В меню приложения нажмите **Manage app → Reboot app**.
3. Если не помогло — **Delete app** и создайте заново с теми же параметрами.
4. Убедитесь, что в открываемом `app.py` нет `make_server` и `serve_forever`.

### Ошибка авторизации Google Sheets
- Проверьте, что в Secrets добавлены `SPREADSHEET_ID` и блок `[gcp_service_account]` из шаблона `.streamlit/secrets.toml.example`.
- Убедитесь, что таблица расшарена на `client_email` сервисного аккаунта.
