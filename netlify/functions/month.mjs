import {
  getDefaultTariffs,
  getPreviousMonthKey,
  normalizeMonthKey,
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

export function createMonthHandler({
  getSupabase = getSupabaseAdmin,
  authenticateUser = getAuthenticatedUser,
  createStorage = createStorageService,
} = {}) {
  return async function handler(event) {
    try {
      const supabase = getSupabase();
      const user = await authenticateUser(supabase, event.headers);
      const storage = createStorage({ supabase });
      const params = new URLSearchParams(event.queryStringParameters || {});
      const year = params.get("year");
      const month = params.get("month");
      const monthKey = normalizeMonthKey(year, month);

      const readings = await storage.getMonthReadings(user.id, monthKey);
      const previousMonthKey = getPreviousMonthKey(monthKey);
      const previousExists = (await storage.getMonthReadings(user.id, previousMonthKey)) !== null;

      return json(200, {
        month_key: monthKey,
        readings,
        previous_month_key: previousMonthKey,
        previous_exists: previousExists,
        tariffs: getDefaultTariffs(),
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Ошибка запроса.";
      return json(message === "Unauthorized." ? 401 : 400, {
        error: message,
        code: "MONTH_LOAD_FAILED",
      });
    }
  };
}

export const handler = createMonthHandler();
