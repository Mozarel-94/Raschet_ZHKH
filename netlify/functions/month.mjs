import {
  getDefaultTariffs,
  getPreviousMonthKey,
  normalizeMonthKey,
} from "./_lib/calculations.mjs";
import { getMonthReadings } from "./_lib/storage.mjs";

function json(statusCode, payload) {
  return {
    statusCode,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
    body: JSON.stringify(payload),
  };
}

export async function handler(event) {
  try {
    const params = new URLSearchParams(event.queryStringParameters || {});
    const year = params.get("year");
    const month = params.get("month");
    const monthKey = normalizeMonthKey(year, month);

    const readings = await getMonthReadings(monthKey);
    const previousMonthKey = getPreviousMonthKey(monthKey);
    const previousExists = (await getMonthReadings(previousMonthKey)) !== null;

    return json(200, {
      month_key: monthKey,
      readings,
      previous_month_key: previousMonthKey,
      previous_exists: previousExists,
      tariffs: getDefaultTariffs(),
    });
  } catch (error) {
    return json(400, {
      error: error instanceof Error ? error.message : "Ошибка запроса.",
      code: "MONTH_LOAD_FAILED",
    });
  }
}
