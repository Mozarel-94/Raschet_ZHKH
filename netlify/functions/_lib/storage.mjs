import { createClient } from "@supabase/supabase-js";
import { seedData } from "./seed-data.mjs";

let supabaseClient;

function getSupabaseAdmin() {
  if (supabaseClient) {
    return supabaseClient;
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl || !serviceRoleKey) {
    throw new Error(
      "Не заданы переменные окружения SUPABASE_URL и SUPABASE_SERVICE_ROLE_KEY."
    );
  }

  supabaseClient = createClient(supabaseUrl, serviceRoleKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });

  return supabaseClient;
}

function mapRowToReadings(row) {
  return {
    cold_water: Number(row.cold_water),
    hot_water: Number(row.hot_water),
    electricity_t1: Number(row.electricity_t1),
    electricity_t2: Number(row.electricity_t2),
    electricity_t3: Number(row.electricity_t3),
  };
}

async function upsertSeedMonth(monthKey) {
  const seedReadings = seedData[monthKey];
  if (!seedReadings) {
    return null;
  }

  await saveMonthReadings(monthKey, seedReadings);
  return seedReadings;
}

export async function getMonthReadings(monthKey) {
  const supabase = getSupabaseAdmin();
  const { data, error } = await supabase
    .from("meter_readings")
    .select("month_key, cold_water, hot_water, electricity_t1, electricity_t2, electricity_t3")
    .eq("month_key", monthKey)
    .maybeSingle();

  if (error) {
    throw new Error(`Ошибка чтения из Supabase: ${error.message}`);
  }

  if (data) {
    return mapRowToReadings(data);
  }

  return upsertSeedMonth(monthKey);
}

export async function saveMonthReadings(monthKey, readings) {
  const supabase = getSupabaseAdmin();
  const [year, month] = monthKey.split("-");
  const payload = {
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
    onConflict: "month_key",
  });

  if (error) {
    throw new Error(`Ошибка сохранения в Supabase: ${error.message}`);
  }
}
