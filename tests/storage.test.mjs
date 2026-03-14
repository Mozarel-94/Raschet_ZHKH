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

          return {
            eq(column, value) {
              filters[column] = value;
              return this;
            },
            async maybeSingle() {
              const row =
                rows.find(
                  (item) =>
                    item.user_id === filters.user_id && item.month_key === filters.month_key
                ) || null;

              return { data: row, error: null };
            },
          };
        },
        async upsert(payload) {
          const index = rows.findIndex(
            (item) => item.user_id === payload.user_id && item.month_key === payload.month_key
          );

          if (index >= 0) {
            rows[index] = { ...rows[index], ...payload };
          } else {
            rows.push(payload);
          }

          return { error: null };
        },
      };
    },
  };
}

test("storage saves and reads records per user", async () => {
  const fakeSupabase = createFakeSupabase();
  const storage = createStorageService({ supabase: fakeSupabase });

  await storage.saveMonthReadings("user-1", "2026-03", {
    cold_water: 10,
    hot_water: 20,
    electricity_t1: 30,
    electricity_t2: 40,
    electricity_t3: 50,
  });

  await storage.saveMonthReadings("user-2", "2026-03", {
    cold_water: 100,
    hot_water: 200,
    electricity_t1: 300,
    electricity_t2: 400,
    electricity_t3: 500,
  });

  const userOneReadings = await storage.getMonthReadings("user-1", "2026-03");
  const userTwoReadings = await storage.getMonthReadings("user-2", "2026-03");

  assert.deepEqual(userOneReadings, {
    cold_water: 10,
    hot_water: 20,
    electricity_t1: 30,
    electricity_t2: 40,
    electricity_t3: 50,
  });
  assert.deepEqual(userTwoReadings, {
    cold_water: 100,
    hot_water: 200,
    electricity_t1: 300,
    electricity_t2: 400,
    electricity_t3: 500,
  });
});

test("storage upserts within same user and month only", async () => {
  const fakeSupabase = createFakeSupabase();
  const storage = createStorageService({ supabase: fakeSupabase });

  await storage.saveMonthReadings("user-1", "2026-04", {
    cold_water: 1,
    hot_water: 1,
    electricity_t1: 1,
    electricity_t2: 1,
    electricity_t3: 1,
  });

  await storage.saveMonthReadings("user-1", "2026-04", {
    cold_water: 2,
    hot_water: 2,
    electricity_t1: 2,
    electricity_t2: 2,
    electricity_t3: 2,
  });

  await storage.saveMonthReadings("user-2", "2026-04", {
    cold_water: 9,
    hot_water: 9,
    electricity_t1: 9,
    electricity_t2: 9,
    electricity_t3: 9,
  });

  assert.equal(fakeSupabase.rows.length, 2);
  assert.deepEqual(await storage.getMonthReadings("user-1", "2026-04"), {
    cold_water: 2,
    hot_water: 2,
    electricity_t1: 2,
    electricity_t2: 2,
    electricity_t3: 2,
  });
  assert.deepEqual(await storage.getMonthReadings("user-2", "2026-04"), {
    cold_water: 9,
    hot_water: 9,
    electricity_t1: 9,
    electricity_t2: 9,
    electricity_t3: 9,
  });
});
