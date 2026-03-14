import test from "node:test";
import assert from "node:assert/strict";

import { createStorageService } from "../netlify/functions/_lib/storage.mjs";

function createFakeSupabase() {
  const rows = [];

  return {
    rows,
    from(tableName) {
      assert.equal(tableName, "meter_readings");

      return {
        select() {
          const filters = {};
          const query = {
            eq(column, value) {
              filters[column] = value;
              return query;
            },
            order() {
              return query;
            },
            async maybeSingle() {
              const row =
                rows.find(
                  (item) =>
                    item.user_id === filters.user_id && item.month_key === filters.month_key
                ) || null;

              return { data: row, error: null };
            },
            then(resolve) {
              const list = rows
                .filter((item) => item.user_id === filters.user_id)
                .sort((left, right) => right.month_key.localeCompare(left.month_key));
              return Promise.resolve({ data: list, error: null }).then(resolve);
            },
          };

          return query;
        },
        async upsert(payload) {
          const index = rows.findIndex(
            (item) => item.user_id === payload.user_id && item.month_key === payload.month_key
          );

          const storedRow = {
            created_at: "2026-03-01T00:00:00Z",
            updated_at: "2026-03-01T00:00:00Z",
            ...payload,
          };

          if (index >= 0) {
            rows[index] = { ...rows[index], ...storedRow };
          } else {
            rows.push(storedRow);
          }

          return { error: null };
        },
      };
    },
  };
}

test("storage saves and reads month records per user", async () => {
  const fakeSupabase = createFakeSupabase();
  const storage = createStorageService({ supabase: fakeSupabase });

  await storage.saveMonthRecord(
    "user-1",
    "2026-03",
    {
      cold_water: 10,
      hot_water: 20,
      electricity_t1: 30,
      electricity_t2: 40,
      electricity_t3: 50,
    },
    {
      cold_water: 1,
      hot_water: 2,
      wastewater: 3,
      electricity_t1: 4,
      electricity_t2: 5,
      electricity_t3: 6,
    },
    {
      water_bill: 100,
      electricity_bill: 200,
      total_bill: 300,
      delta: {
        cold_water: 1,
        hot_water: 2,
        electricity_t1: 3,
        electricity_t2: 4,
        electricity_t3: 5,
      },
    }
  );

  const record = await storage.getMonthRecord("user-1", "2026-03");

  assert.equal(record.month_key, "2026-03");
  assert.equal(record.tariffs.wastewater, 3);
  assert.equal(record.total_bill, 300);
  assert.equal(record.delta.electricity_t3, 5);
});

test("storage keeps records isolated by user", async () => {
  const fakeSupabase = createFakeSupabase();
  const storage = createStorageService({ supabase: fakeSupabase });

  await storage.saveMonthRecord(
    "user-1",
    "2026-04",
    { cold_water: 1, hot_water: 1, electricity_t1: 1, electricity_t2: 1, electricity_t3: 1 },
    { cold_water: 1, hot_water: 1, wastewater: 1, electricity_t1: 1, electricity_t2: 1, electricity_t3: 1 },
    null
  );
  await storage.saveMonthRecord(
    "user-2",
    "2026-04",
    { cold_water: 9, hot_water: 9, electricity_t1: 9, electricity_t2: 9, electricity_t3: 9 },
    { cold_water: 2, hot_water: 2, wastewater: 2, electricity_t1: 2, electricity_t2: 2, electricity_t3: 2 },
    null
  );

  const firstUser = await storage.getMonthRecord("user-1", "2026-04");
  const secondUser = await storage.getMonthRecord("user-2", "2026-04");

  assert.equal(firstUser.readings.cold_water, 1);
  assert.equal(secondUser.readings.cold_water, 9);
});
