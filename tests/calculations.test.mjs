import test from "node:test";
import assert from "node:assert/strict";

import {
  calculateTotals,
  getPreviousMonthKey,
  normalizeMonthKey,
  validateDelta,
} from "../netlify/functions/_lib/calculations.mjs";

test("normalizeMonthKey formats year and month", () => {
  assert.equal(normalizeMonthKey("2026", "3"), "2026-03");
});

test("getPreviousMonthKey handles year boundary", () => {
  assert.equal(getPreviousMonthKey("2026-01"), "2025-12");
});

test("calculateTotals returns water, electricity and total", () => {
  const result = calculateTotals(
    {
      cold_water: 20,
      hot_water: 10,
      electricity_t1: 100,
      electricity_t2: 50,
      electricity_t3: 25,
    },
    {
      cold_water: 18,
      hot_water: 9,
      electricity_t1: 90,
      electricity_t2: 45,
      electricity_t3: 20,
    },
    {
      cold_water: 10,
      hot_water: 20,
      wastewater: 5,
      electricity_t1: 2,
      electricity_t2: 1,
      electricity_t3: 3,
    }
  );

  assert.deepEqual(result.delta, {
    cold_water: 2,
    hot_water: 1,
    electricity_t1: 10,
    electricity_t2: 5,
    electricity_t3: 5,
  });
  assert.equal(result.water_bill, 55);
  assert.equal(result.electricity_bill, 40);
  assert.equal(result.total_bill, 95);
});

test("validateDelta rejects negative consumption", () => {
  assert.throws(
    () =>
      validateDelta({
        cold_water: -1,
        hot_water: 0,
        electricity_t1: 0,
        electricity_t2: 0,
        electricity_t3: 0,
      }),
    /Холодная вода|Р/
  );
});
