import { formatMonthLabel, getPreviousMonthKey, getPreviousYearMonthKey } from "./calculations.mjs";

function round(value) {
  return value === null || value === undefined ? null : Number(value.toFixed(2));
}

function safeAverage(values) {
  if (values.length === 0) {
    return null;
  }

  return round(values.reduce((sum, value) => sum + value, 0) / values.length);
}

function mapChart(records, pickValue) {
  return records
    .filter((record) => pickValue(record) !== null && pickValue(record) !== undefined)
    .map((record) => ({
      month_key: record.month_key,
      label: formatMonthLabel(record.month_key),
      value: round(pickValue(record)),
    }));
}

function getRecordMap(records) {
  return new Map(records.map((record) => [record.month_key, record]));
}

function compareDelta(current, other) {
  if (!current || !other) {
    return null;
  }

  return {
    cold_water: round(current.cold_water - other.cold_water),
    hot_water: round(current.hot_water - other.hot_water),
    electricity_t1: round(current.electricity_t1 - other.electricity_t1),
    electricity_t2: round(current.electricity_t2 - other.electricity_t2),
    electricity_t3: round(current.electricity_t3 - other.electricity_t3),
  };
}

export function buildMonthFormulas(record) {
  const delta = record.delta;
  if (!delta) {
    return null;
  }

  return {
    water: {
      formula:
        "Холодная вода × тариф + Горячая вода × тариф + (Холодная + Горячая) × водоотведение",
      parts: [
        {
          label: "Холодная вода",
          expression: `${delta.cold_water.toFixed(2)} × ${record.tariffs.cold_water.toFixed(2)}`,
          value: round(delta.cold_water * record.tariffs.cold_water),
        },
        {
          label: "Горячая вода",
          expression: `${delta.hot_water.toFixed(2)} × ${record.tariffs.hot_water.toFixed(2)}`,
          value: round(delta.hot_water * record.tariffs.hot_water),
        },
        {
          label: "Водоотведение",
          expression: `${(delta.cold_water + delta.hot_water).toFixed(2)} × ${record.tariffs.wastewater.toFixed(2)}`,
          value: round((delta.cold_water + delta.hot_water) * record.tariffs.wastewater),
        },
      ],
      total: round(record.water_bill),
    },
    electricity: {
      formula: "Т1 × тариф Т1 + Т2 × тариф Т2 + Т3 × тариф Т3",
      parts: [
        {
          label: "Т1",
          expression: `${delta.electricity_t1.toFixed(2)} × ${record.tariffs.electricity_t1.toFixed(2)}`,
          value: round(delta.electricity_t1 * record.tariffs.electricity_t1),
        },
        {
          label: "Т2",
          expression: `${delta.electricity_t2.toFixed(2)} × ${record.tariffs.electricity_t2.toFixed(2)}`,
          value: round(delta.electricity_t2 * record.tariffs.electricity_t2),
        },
        {
          label: "Т3",
          expression: `${delta.electricity_t3.toFixed(2)} × ${record.tariffs.electricity_t3.toFixed(2)}`,
          value: round(delta.electricity_t3 * record.tariffs.electricity_t3),
        },
      ],
      total: round(record.electricity_bill),
    },
  };
}

export function buildHistoryAnalytics(records) {
  const completeRecords = records.filter((record) => record.total_bill !== null && record.delta !== null);
  const mostExpensiveMonth = completeRecords.reduce(
    (currentMax, record) =>
      !currentMax || record.total_bill > currentMax.total_bill
        ? { month_key: record.month_key, label: formatMonthLabel(record.month_key), total_bill: round(record.total_bill) }
        : currentMax,
    null
  );

  return {
    total_payment_chart: mapChart(records, (record) => record.total_bill),
    water_consumption_chart: mapChart(records, (record) =>
      record.delta ? record.delta.cold_water + record.delta.hot_water : null
    ),
    electricity_consumption_chart: mapChart(records, (record) =>
      record.delta
        ? record.delta.electricity_t1 + record.delta.electricity_t2 + record.delta.electricity_t3
        : null
    ),
    averages: {
      total_bill: safeAverage(completeRecords.map((record) => record.total_bill)),
      water_bill: safeAverage(completeRecords.map((record) => record.water_bill)),
      electricity_bill: safeAverage(completeRecords.map((record) => record.electricity_bill)),
      cold_water: safeAverage(completeRecords.map((record) => record.delta.cold_water)),
      hot_water: safeAverage(completeRecords.map((record) => record.delta.hot_water)),
      electricity_total: safeAverage(
        completeRecords.map(
          (record) =>
            record.delta.electricity_t1 + record.delta.electricity_t2 + record.delta.electricity_t3
        )
      ),
    },
    most_expensive_month: mostExpensiveMonth,
  };
}

export function buildMonthComparisons(records, monthKey) {
  const recordMap = getRecordMap(records);
  const current = recordMap.get(monthKey);

  if (!current) {
    return null;
  }

  const previousMonth = recordMap.get(getPreviousMonthKey(monthKey)) || null;
  const previousYear = recordMap.get(getPreviousYearMonthKey(monthKey)) || null;

  return {
    previous_month: previousMonth
      ? {
          month_key: previousMonth.month_key,
          label: formatMonthLabel(previousMonth.month_key),
          total_bill: round(previousMonth.total_bill),
        }
      : null,
    previous_year: previousYear
      ? {
          month_key: previousYear.month_key,
          label: formatMonthLabel(previousYear.month_key),
          total_bill: round(previousYear.total_bill),
        }
      : null,
    previous_month_total_diff:
      previousMonth && current.total_bill !== null && previousMonth.total_bill !== null
        ? round(current.total_bill - previousMonth.total_bill)
        : null,
    previous_year_total_diff:
      previousYear && current.total_bill !== null && previousYear.total_bill !== null
        ? round(current.total_bill - previousYear.total_bill)
        : null,
    previous_month_delta_diff: compareDelta(current.delta, previousMonth?.delta ?? null),
    previous_year_delta_diff: compareDelta(current.delta, previousYear?.delta ?? null),
  };
}

export function toHistoryMonthSummary(record) {
  return {
    month_key: record.month_key,
    label: formatMonthLabel(record.month_key),
    total_bill: round(record.total_bill),
    water_bill: round(record.water_bill),
    electricity_bill: round(record.electricity_bill),
    delta: record.delta,
    has_complete_calculation: Boolean(record.delta && record.total_bill !== null),
    updated_at: record.updated_at,
  };
}
