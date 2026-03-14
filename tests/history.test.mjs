import test from "node:test";
import assert from "node:assert/strict";

import {
  buildHistoryAnalytics,
  buildMonthComparisons,
  buildMonthFormulas,
} from "../netlify/functions/_lib/history.mjs";

const records = [
  {
    month_key: "2026-03",
    tariffs: {
      cold_water: 10,
      hot_water: 20,
      wastewater: 5,
      electricity_t1: 2,
      electricity_t2: 1,
      electricity_t3: 3,
    },
    delta: {
      cold_water: 2,
      hot_water: 1,
      electricity_t1: 10,
      electricity_t2: 5,
      electricity_t3: 5,
    },
    water_bill: 55,
    electricity_bill: 40,
    total_bill: 95,
    updated_at: "2026-03-01T00:00:00Z",
  },
  {
    month_key: "2026-02",
    tariffs: {
      cold_water: 10,
      hot_water: 20,
      wastewater: 5,
      electricity_t1: 2,
      electricity_t2: 1,
      electricity_t3: 3,
    },
    delta: {
      cold_water: 1,
      hot_water: 2,
      electricity_t1: 6,
      electricity_t2: 4,
      electricity_t3: 2,
    },
    water_bill: 65,
    electricity_bill: 22,
    total_bill: 87,
    updated_at: "2026-02-01T00:00:00Z",
  },
];

test("buildHistoryAnalytics computes averages and expensive month", () => {
  const analytics = buildHistoryAnalytics(records);

  assert.equal(analytics.averages.total_bill, 91);
  assert.equal(analytics.most_expensive_month.month_key, "2026-03");
  assert.equal(analytics.total_payment_chart.length, 2);
});

test("buildMonthComparisons compares with previous month", () => {
  const comparisons = buildMonthComparisons(records, "2026-03");

  assert.equal(comparisons.previous_month_total_diff, 8);
  assert.equal(comparisons.previous_month.month_key, "2026-02");
});

test("buildMonthFormulas builds readable breakdown", () => {
  const formulas = buildMonthFormulas(records[0]);

  assert.equal(formulas.water.parts.length, 3);
  assert.equal(formulas.electricity.total, 40);
});
