import { formatMonthLabel, normalizeMonthKey } from "./_lib/calculations.mjs";
import { getAuthenticatedUser } from "./_lib/auth.mjs";
import { buildHistoryAnalytics, buildMonthComparisons, buildMonthFormulas, toHistoryMonthSummary } from "./_lib/history.mjs";
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

export async function handler(event) {
  try {
    const supabase = getSupabaseAdmin();
    const user = await getAuthenticatedUser(supabase, event.headers);
    const storage = createStorageService({ supabase });
    const params = new URLSearchParams(event.queryStringParameters || {});
    const selectedMonth = params.get("month");
    const records = await storage.listMonthRecords(user.id);
    const summaries = records.map(toHistoryMonthSummary);
    const analytics = buildHistoryAnalytics(records);
    const selectedMonthKey =
      selectedMonth && selectedMonth.trim() !== ""
        ? normalizeMonthKey(...selectedMonth.split("-"))
        : records[0]?.month_key ?? null;
    const selectedRecord = selectedMonthKey
      ? records.find((record) => record.month_key === selectedMonthKey) || null
      : null;

    return json(200, {
      months: summaries,
      analytics,
      selected_month: selectedRecord
        ? {
            ...selectedRecord,
            label: formatMonthLabel(selectedRecord.month_key),
            formulas: buildMonthFormulas(selectedRecord),
            comparisons: buildMonthComparisons(records, selectedRecord.month_key),
          }
        : null,
      empty: records.length === 0,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Ошибка истории.";
    return json(message === "Unauthorized." ? 401 : 400, {
      error: message,
      code: "HISTORY_FAILED",
    });
  }
}
