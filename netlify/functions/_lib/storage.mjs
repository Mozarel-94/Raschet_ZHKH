import { seedData } from "./seed-data.mjs";
import { getSupabaseAdmin } from "./supabase-admin.mjs";

function mapRowToReadings(row) {
  return {
    cold_water: Number(row.cold_water),
    hot_water: Number(row.hot_water),
    electricity_t1: Number(row.electricity_t1),
    electricity_t2: Number(row.electricity_t2),
    electricity_t3: Number(row.electricity_t3),
  };
}

export function createStorageService({ supabase = getSupabaseAdmin() } = {}) {
  async function upsertSeedMonth(userId, monthKey) {
    const seedReadings = seedData[monthKey];
    if (!seedReadings) {
      return null;
    }

    await saveMonthReadings(userId, monthKey, seedReadings);
    return seedReadings;
  }

  async function getMonthReadings(userId, monthKey) {
    const { data, error } = await supabase
      .from("meter_readings")
      .select("month_key, cold_water, hot_water, electricity_t1, electricity_t2, electricity_t3")
      .eq("user_id", userId)
      .eq("month_key", monthKey)
      .maybeSingle();

    if (error) {
      throw new Error(`Ошибка чтения из Supabase: ${error.message}`);
    }

    if (data) {
      return mapRowToReadings(data);
    }

    return upsertSeedMonth(userId, monthKey);
  }

  async function saveMonthReadings(userId, monthKey, readings) {
    const [year, month] = monthKey.split("-");
    const payload = {
      user_id: userId,
      month_key: monthKey,
      calculation_year: Number(year),
      calculation_month: Number(month),
      cold_water: Number(readings.cold_water),
      hot_water: Number(readings.hot_water),
      electricity_t1: Number(readings.electricity_t1),
      electricity_t2: Number(readings.electricity_t2),
      electricity_t3: Number(readings.electricity_t3),
    };

    const { error } = await supabase.from("meter_readings").upsert(payload, {
      onConflict: "user_id,month_key",
    });

    if (error) {
      throw new Error(`Ошибка сохранения в Supabase: ${error.message}`);
    }
  }

  return {
    getMonthReadings,
    saveMonthReadings,
  };
}

export async function getMonthReadings(userId, monthKey) {
  return createStorageService().getMonthReadings(userId, monthKey);
}

export async function saveMonthReadings(userId, monthKey, readings) {
  return createStorageService().saveMonthReadings(userId, monthKey, readings);
}
