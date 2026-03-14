# История и аналитика

## 1. Архитектурный план

- Источник истины: `public.meter_readings`
- На уровне БД храним не только показания, но и тарифы/итоги месяца
- Расчёт формул и агрегаций выполняется на сервере в Netlify Functions
- Клиент получает готовые DTO для списка месяцев, деталей и аналитики
- История вынесена на отдельный экран `/history`
- Для будущего перехода на React используются те же DTO и API

### Слои

- `netlify/functions/_lib/calculations.mjs`
  - доменная логика расчёта
- `netlify/functions/_lib/storage.mjs`
  - чтение/запись истории
- `netlify/functions/_lib/history.mjs`
  - агрегация и аналитика
- `netlify/functions/history.mjs`
  - API истории
- `web/history/*`
  - текущая реализация экрана в `vanilla JS`
- `reference/react/HistoryAnalyticsPage.tsx`
  - React reference-компоненты на тех же контрактах

## 2. Изменения в схеме Supabase

В `meter_readings` добавлены поля:

- тарифы месяца
  - `cold_water_tariff`
  - `hot_water_tariff`
  - `wastewater_tariff`
  - `electricity_t1_tariff`
  - `electricity_t2_tariff`
  - `electricity_t3_tariff`
- рассчитанные значения
  - `delta_cold_water`
  - `delta_hot_water`
  - `delta_electricity_t1`
  - `delta_electricity_t2`
  - `delta_electricity_t3`
  - `water_bill`
  - `electricity_bill`
  - `total_bill`

Это даёт:

- корректную историчность тарифов
- быструю аналитику без повторного пересчёта на клиенте
- детализацию формул по конкретному месяцу

## 3. SQL migration

Используй:

- новая схема: [supabase/schema.sql](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/supabase/schema.sql)
- миграция для существующей таблицы: [supabase/history_analytics.sql](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/supabase/history_analytics.sql)

Если таблица уже существует, порядок такой:

1. Выполни [supabase/meter_readings_user_scope.sql](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/supabase/meter_readings_user_scope.sql), если ещё не делал привязку к `user_id`
2. Выполни [supabase/history_analytics.sql](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/supabase/history_analytics.sql)
3. Перезадеплой Netlify

## 4. TypeScript types

Готовые типы лежат в:

- [web/types/history-analytics.d.ts](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/web/types/history-analytics.d.ts)

Они описывают:

- запись месяца
- тарифы
- расход
- сравнения
- агрегированную аналитику

## 5. Сервисы для выборки истории

Сервер:

- [netlify/functions/_lib/storage.mjs](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/netlify/functions/_lib/storage.mjs)
  - `getMonthRecord`
  - `listMonthRecords`
  - `saveMonthRecord`

Клиент:

- [web/lib/history-api.js](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/web/lib/history-api.js)
  - `fetchHistory(monthKey?)`

## 6. Функции агрегации и аналитики

Лежат в:

- [netlify/functions/_lib/history.mjs](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/netlify/functions/_lib/history.mjs)

Там собраны:

- `buildHistoryAnalytics`
- `buildMonthComparisons`
- `buildMonthFormulas`
- `toHistoryMonthSummary`

## 7. React-компоненты

Reference-реализация:

- [reference/react/HistoryAnalyticsPage.tsx](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/reference/react/HistoryAnalyticsPage.tsx)

Она не подключена к текущему runtime напрямую, потому что текущий проект без React build-pipeline, но использует те же DTO и подходит как заготовка для переноса экрана в React.

## 8. Полный код

Основные файлы реализации:

- [netlify/functions/history.mjs](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/netlify/functions/history.mjs)
- [netlify/functions/_lib/history.mjs](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/netlify/functions/_lib/history.mjs)
- [netlify/functions/_lib/storage.mjs](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/netlify/functions/_lib/storage.mjs)
- [netlify/functions/_lib/calculations.mjs](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/netlify/functions/_lib/calculations.mjs)
- [web/history/index.html](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/web/history/index.html)
- [web/history/app.js](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/web/history/app.js)
- [web/styles.css](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/web/styles.css)
- [netlify.toml](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/netlify.toml)

## 9. Инструкция по интеграции

1. Выполни [supabase/history_analytics.sql](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/supabase/history_analytics.sql), если база уже существует.
2. Проверь, что в Netlify задеплоен обновлённый [netlify.toml](/c:/Users/user/Documents/GitHub/Raschet_ZHKH/netlify.toml) с `/api/history` и `/history`.
3. Задеплой код.
4. Сохрани несколько месяцев на главной странице `/`.
5. Открой `/history`.
6. Проверь:
   - список месяцев
   - карточки средних значений
   - графики
   - детализацию формул
   - сравнение с прошлым месяцем и прошлым годом

### Ожидаемое поведение

- если данных нет, показываются пустые состояния
- если нет предыдущего месяца, формулы и графики не ломаются
- если нет аналогичного месяца прошлого года, comparison показывает отсутствие данных
- экран корректно складывается в одну колонку на мобильных
