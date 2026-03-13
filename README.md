# Расчёт коммунальных платежей

Приложение подготовлено для схемы `GitHub -> Netlify + Supabase`.

Технически проект теперь состоит из:

- статического фронтенда в `web/`
- Netlify Functions в `netlify/functions/`
- хранения помесячных показаний в `Supabase Postgres`

## Что умеет приложение

- выбор года и месяца расчёта
- сохранение показаний по месяцам
- автоподстановка ранее сохранённых данных при переключении месяца
- расчёт как разницы между текущим и предыдущим месяцем
- редактируемые тарифы с блокировкой и сворачиванием

## Структура для Netlify

- `web/index.html` — страница приложения
- `web/styles.css` — стили интерфейса
- `web/app.js` — клиентская логика
- `netlify/functions/month.mjs` — загрузка данных выбранного месяца
- `netlify/functions/calculate.mjs` — сохранение и расчёт
- `netlify/functions/_lib/storage.mjs` — работа с Supabase
- `supabase/schema.sql` — SQL-схема таблицы
- `netlify.toml` — конфиг деплоя

## Настройка Supabase

1. Создайте проект в Supabase.
2. Откройте SQL Editor.
3. Выполните содержимое `supabase/schema.sql`.
4. Возьмите:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`

## Настройка Netlify

В `Site configuration -> Environment variables` добавьте:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

`SUPABASE_SERVICE_ROLE_KEY` нужен только серверным Netlify Functions. Во фронтенд он не попадает.

## Локальный запуск

```bash
npm install
npx netlify dev
```

Для локального запуска также нужны переменные окружения `SUPABASE_URL` и `SUPABASE_SERVICE_ROLE_KEY`.

## Деплой через GitHub в Netlify

1. Запушьте репозиторий на GitHub.
2. В Netlify выберите `Add new site` -> `Import an existing project`.
3. Подключите GitHub-репозиторий.
4. Netlify сам прочитает `netlify.toml`.
5. Если настройки нужно указать вручную:
   - Build command: `npm install`
   - Publish directory: `web`
   - Functions directory: `netlify/functions`
6. Проверьте, что заданы `SUPABASE_URL` и `SUPABASE_SERVICE_ROLE_KEY`.
7. Запустите deploy.

## Импорт января и февраля

Январь и февраль 2026 уже зашиты в `netlify/functions/_lib/seed-data.mjs`.

Если этих месяцев ещё нет в Supabase, сервер автоматически импортирует их при первом обращении к соответствующему месяцу.
