import {
  calculateTotals,
  getDefaultTariffs,
  getPreviousMonthKey,
  normalizeMonthKey,
  parseReading,
  parseTariff,
} from "./_lib/calculations.mjs";
import { getAuthenticatedUser } from "./_lib/auth.mjs";
import { getSupabaseAdmin } from "./_lib/supabase-admin.mjs";
import { createStorageService } from "./_lib/storage.mjs";

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

export function createCalculateHandler({
  getSupabase = getSupabaseAdmin,
  authenticateUser = getAuthenticatedUser,
  createStorage = createStorageService,
} = {}) {
  return async function handler(event) {
    if (event.httpMethod !== "POST") {
      return json(405, { error: "Method Not Allowed" });
    }

    try {
      const supabase = getSupabase();
      const user = await authenticateUser(supabase, event.headers);
      const storage = createStorage({ supabase });
      const body = JSON.parse(event.body || "{}");
      const monthKey = normalizeMonthKey(body.year, body.month);

      const readings = {
        cold_water: parseReading(body.readings?.cold_water, "Холодная вода"),
        hot_water: parseReading(body.readings?.hot_water, "Горячая вода"),
        electricity_t1: parseReading(body.readings?.electricity_t1, "Т1"),
        electricity_t2: parseReading(body.readings?.electricity_t2, "Т2"),
        electricity_t3: parseReading(body.readings?.electricity_t3, "Т3"),
      };

      const rawTariffs = body.tariffs || getDefaultTariffs();
      const tariffs = {
        cold_water: parseTariff(rawTariffs.cold_water, "Тариф холодной воды"),
        hot_water: parseTariff(rawTariffs.hot_water, "Тариф горячей воды"),
        wastewater: parseTariff(rawTariffs.wastewater, "Тариф водоотведения"),
        electricity_t1: parseTariff(rawTariffs.electricity_t1, "Тариф электроэнергии 1"),
        electricity_t2: parseTariff(rawTariffs.electricity_t2, "Тариф электроэнергии 2"),
        electricity_t3: parseTariff(rawTariffs.electricity_t3, "Тариф электроэнергии 3"),
      };

      await storage.saveMonthReadings(user.id, monthKey, readings);

      const previousMonthKey = getPreviousMonthKey(monthKey);
      const previousReadings = await storage.getMonthReadings(user.id, previousMonthKey);

      if (previousReadings === null) {
        return json(200, {
          month_key: monthKey,
          saved: true,
          previous_month_key: previousMonthKey,
          result: null,
          message: `Показания за ${monthKey} сохранены. Для расчёта нужны данные за предыдущий месяц: ${previousMonthKey}.`,
        });
      }

      const result = calculateTotals(readings, previousReadings, tariffs);

      return json(200, {
        month_key: monthKey,
        saved: true,
        previous_month_key: previousMonthKey,
        result,
        message: `Показания за ${monthKey} сохранены.`,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Ошибка расчёта.";
      return json(message === "Unauthorized." ? 401 : 400, {
        error: message,
        code: "CALCULATION_FAILED",
      });
    }
  };
}

export const handler = createCalculateHandler();
