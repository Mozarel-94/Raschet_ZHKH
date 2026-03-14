# Расчёт коммунальных платежей

Приложение подготовлено для схемы `GitHub -> Netlify + Supabase`.

Технически проект теперь состоит из:

- статического фронтенда в `web/`
- Netlify Functions в `netlify/functions/`
- хранения помесячных показаний в `Supabase Postgres`
- клиентской авторизации через `Supabase Auth`

## Что умеет приложение

- выбор года и месяца расчёта
- сохранение показаний по месяцам
- автоподстановка ранее сохранённых данных при переключении месяца
- расчёт как разницы между текущим и предыдущим месяцем
- редактируемые тарифы с блокировкой и сворачиванием
- регистрация и вход по `email/password`
- защищённый доступ к основной странице через `/login`

## Структура для Netlify

- `web/index.html` — защищённая страница приложения
- `web/login/index.html` — страница входа и регистрации
- `web/styles.css` — стили интерфейса
- `web/app.js` — клиентская логика калькулятора
- `web/lib/supabase-browser.js` — клиент Supabase для браузера
- `web/lib/auth.js` — auth-логика на клиенте
- `netlify/functions/auth-config.mjs` — публичный конфиг для browser auth client
- `netlify/functions/month.mjs` — загрузка данных выбранного месяца
- `netlify/functions/calculate.mjs` — сохранение и расчёт
- `netlify/functions/_lib/storage.mjs` — работа с Supabase
- `supabase/schema.sql` — SQL-схема таблицы показаний
- `supabase/meter_readings_user_scope.sql` — миграция для привязки показаний к `user_id`
- `supabase/auth_profiles.sql` — SQL для `profiles` и trigger'а пользователей
- `netlify.toml` — конфиг деплоя

## Настройка Supabase

1. Создайте проект в Supabase.
2. В `Authentication -> Providers` включите `Email`.
3. Откройте SQL Editor.
4. Выполните содержимое `supabase/schema.sql`.
5. Если таблица `meter_readings` уже существует, выполните `supabase/meter_readings_user_scope.sql`.
6. Выполните содержимое `supabase/auth_profiles.sql`.
7. Возьмите:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

## Настройка Netlify

В `Site configuration -> Environment variables` добавьте:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

`SUPABASE_ANON_KEY` используется клиентской авторизацией через Supabase Auth.

`SUPABASE_SERVICE_ROLE_KEY` нужен только серверным Netlify Functions. Во фронтенд он не попадает напрямую: клиент получает только публичную конфигурацию через `auth-config` endpoint.

## Локальный запуск

```bash
npm install
npx netlify dev
```

Для локального запуска также нужны переменные окружения `SUPABASE_URL`, `SUPABASE_ANON_KEY` и `SUPABASE_SERVICE_ROLE_KEY`.

## Деплой через GitHub в Netlify

1. Запушьте репозиторий на GitHub.
2. В Netlify выберите `Add new site` -> `Import an existing project`.
3. Подключите GitHub-репозиторий.
4. Netlify сам прочитает `netlify.toml`.
5. Если настройки нужно указать вручную:
   - Build command: `npm install`
   - Publish directory: `web`
   - Functions directory: `netlify/functions`
6. Проверьте, что заданы `SUPABASE_URL`, `SUPABASE_ANON_KEY` и `SUPABASE_SERVICE_ROLE_KEY`.
7. Запустите deploy.

## Авторизация

В проект добавлена базовая клиентская авторизация через `Supabase Auth`:

- страница входа и регистрации: `/login`
- защищённая главная страница `/`
- проверка сессии при загрузке приложения
- выход из системы через кнопку в интерфейсе
- SQL для таблицы профилей и trigger'а: `supabase/auth_profiles.sql`

## Импорт января и февраля

Январь и февраль 2026 уже зашиты в `netlify/functions/_lib/seed-data.mjs`.

Если этих месяцев ещё нет в Supabase, сервер автоматически импортирует их при первом обращении к соответствующему месяцу.
## Тесты

```bash
npm test
```

Тесты покрывают:

- расчётную логику
- auth helper'ы
- user-scoped storage
- handlers для проверки, что чтение и запись идут в контексте авторизованного пользователя
