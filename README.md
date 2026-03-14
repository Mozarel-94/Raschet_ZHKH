# Расчёт коммунальных платежей

Приложение подготовлено для схемы `GitHub -> Netlify + Supabase`.

Технически проект состоит из:

- статического фронтенда в `web/`
- Netlify Functions в `netlify/functions/`
- хранения помесячных показаний в `Supabase Postgres`
- клиентской авторизации через `Supabase Auth`
- экрана истории и аналитики по месяцам

## Что умеет приложение

- выбор года и месяца расчёта
- сохранение показаний по месяцам
- автоподстановка ранее сохранённых данных при переключении месяца
- расчёт как разницы между текущим и предыдущим месяцем
- редактируемые тарифы с блокировкой и сворачиванием
- регистрация и вход по `email/password`
- восстановление пароля по email
- история по месяцам и аналитика потребления/платежей
- защищённый доступ к основной странице через `/login`

## Структура

- `web/index.html` — защищённая страница калькулятора
- `web/app.js` — клиентская логика калькулятора
- `web/history/index.html` — экран истории и аналитики
- `web/history/app.js` — клиентская логика истории
- `web/login/index.html` — страница входа и регистрации
- `web/reset-password/index.html` — страница установки нового пароля
- `web/lib/auth.js` — auth-логика на клиенте
- `web/lib/history-api.js` — клиентский сервис истории
- `web/lib/supabase-browser.js` — клиент Supabase для браузера
- `web/types/history-analytics.d.ts` — reference-типы для интеграции
- `netlify/functions/month.mjs` — загрузка данных выбранного месяца
- `netlify/functions/calculate.mjs` — сохранение и расчёт
- `netlify/functions/history.mjs` — история и аналитика
- `netlify/functions/auth-config.mjs` — публичный конфиг для browser auth client
- `netlify/functions/_lib/calculations.mjs` — доменная логика расчёта
- `netlify/functions/_lib/storage.mjs` — чтение/запись истории
- `netlify/functions/_lib/history.mjs` — серверная аналитика
- `supabase/schema.sql` — новая полная схема таблицы показаний
- `supabase/meter_readings_user_scope.sql` — миграция для привязки показаний к `user_id`
- `supabase/history_analytics.sql` — миграция для тарифов и аналитики
- `supabase/auth_profiles.sql` — SQL для `profiles` и trigger'а пользователей
- `reference/react/HistoryAnalyticsPage.tsx` — React reference-компоненты
- `docs/history-analytics-plan.md` — архитектурный план и инструкция по интеграции

## Настройка Supabase

1. Создайте проект в Supabase.
2. В `Authentication -> Providers` включите `Email`.
3. В `Authentication -> URL Configuration -> Redirect URLs` добавьте:
   - `https://<your-netlify-site>.netlify.app/reset-password`
   - `http://localhost:8888/reset-password`
4. Откройте SQL Editor.
5. Если начинаете с нуля, выполните `supabase/schema.sql`.
6. Если таблица `meter_readings` уже существует, выполните:
   - `supabase/meter_readings_user_scope.sql`
   - `supabase/history_analytics.sql`
7. Выполните `supabase/auth_profiles.sql`.
8. Возьмите:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

## Настройка Netlify

В `Site configuration -> Environment variables` добавьте:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

`SUPABASE_ANON_KEY` используется клиентской авторизацией через Supabase Auth.

`SUPABASE_SERVICE_ROLE_KEY` нужен только серверным Netlify Functions.

## Локальный запуск

```bash
npm install
npx netlify dev
```

Для локального запуска нужны `SUPABASE_URL`, `SUPABASE_ANON_KEY` и `SUPABASE_SERVICE_ROLE_KEY`.

## Деплой

1. Запушьте репозиторий на GitHub.
2. В Netlify выберите `Add new site -> Import an existing project`.
3. Подключите GitHub-репозиторий.
4. Проверьте, что заданы `SUPABASE_URL`, `SUPABASE_ANON_KEY` и `SUPABASE_SERVICE_ROLE_KEY`.
5. Запустите deploy.

## История и аналитика

Экран `/history` показывает:

- список месяцев
- детализацию выбранного месяца
- график общего платежа
- графики расхода воды и электричества
- средние значения
- самый дорогой месяц
- сравнение с предыдущим месяцем и прошлым годом

Подробный план и интеграция:

- `docs/history-analytics-plan.md`

## Тесты

```bash
npm test
```

Тесты покрывают:

- расчётную логику
- auth helper'ы
- user-scoped storage
- handlers
- агрегацию истории и аналитики
