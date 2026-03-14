import { getDefaultTariffs } from "./calculations.mjs";
import { getSupabaseAdmin } from "./supabase-admin.mjs";

function toNumberOrNull(value) {
  return value === null || value === undefined ? null : Number(value);
}

function mapRowToMonthlyRecord(row) {
  return {
    month_key: row.month_key,
    calculation_year: Number(row.calculation_year),
    calculation_month: Number(row.calculation_month),
    readings: {
      cold_water: Number(row.cold_water),
      hot_water: Number(row.hot_water),
      electricity_t1: Number(row.electricity_t1),
      electricity_t2: Number(row.electricity_t2),
      electricity_t3: Number(row.electricity_t3),
    },
    tariffs: {
      cold_water: Number(row.cold_water_tariff),
      hot_water: Number(row.hot_water_tariff),
      wastewater: Number(row.wastewater_tariff),
      electricity_t1: Number(row.electricity_t1_tariff),
      electricity_t2: Number(row.electricity_t2_tariff),
      electricity_t3: Number(row.electricity_t3_tariff),
    },
    delta: row.delta_cold_water === null
      ? null
      : {
          cold_water: Number(row.delta_cold_water),
          hot_water: Number(row.delta_hot_water),
          electricity_t1: Number(row.delta_electricity_t1),
          electricity_t2: Number(row.delta_electricity_t2),
          electricity_t3: Number(row.delta_electricity_t3),
        },
    water_bill: toNumberOrNull(row.water_bill),
    electricity_bill: toNumberOrNull(row.electricity_bill),
    total_bill: toNumberOrNull(row.total_bill),
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function getSelectColumns() {
  return [
    "month_key",
    "calculation_year",
    "calculation_month",
    "cold_water",
    "hot_water",
    "electricity_t1",
    "electricity_t2",
    "electricity_t3",
    "cold_water_tariff",
    "hot_water_tariff",
    "wastewater_tariff",
    "electricity_t1_tariff",
    "electricity_t2_tariff",
    "electricity_t3_tariff",
    "delta_cold_water",
    "delta_hot_water",
    "delta_electricity_t1",
    "delta_electricity_t2",
    "delta_electricity_t3",
    "water_bill",
    "electricity_bill",
    "total_bill",
    "created_at",
    "updated_at",
  ].join(", ");
}

export function createStorageService({ supabase = getSupabaseAdmin() } = {}) {
  async function getMonthRecord(userId, monthKey) {
    const { data, error } = await supabase
      .from("meter_readings")
      .select(getSelectColumns())
      .eq("user_id", userId)
      .eq("month_key", monthKey)
      .maybeSingle();

    if (error) {
      throw new Error(`Ошибка чтения из Supabase: ${error.message}`);
    }

    return data ? mapRowToMonthlyRecord(data) : null;
  }

  async function getMonthReadings(userId, monthKey) {
    const record = await getMonthRecord(userId, monthKey);
    return record?.readings ?? null;
  }

  async function listMonthRecords(userId) {
    const { data, error } = await supabase
      .from("meter_readings")
      .select(getSelectColumns())
      .eq("user_id", userId)
      .order("calculation_year", { ascending: false })
      .order("calculation_month", { ascending: false });

    if (error) {
      throw new Error(`Ошибка чтения истории из Supabase: ${error.message}`);
    }

    return (data || []).map(mapRowToMonthlyRecord);
  }

  async function saveMonthRecord(userId, monthKey, readings, tariffs, result) {
    const [year, month] = monthKey.split("-");
    const safeTariffs = tariffs || getDefaultTariffs();
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
      cold_water_tariff: Number(safeTariffs.cold_water),
      hot_water_tariff: Number(safeTariffs.hot_water),
      wastewater_tariff: Number(safeTariffs.wastewater),
      electricity_t1_tariff: Number(safeTariffs.electricity_t1),
      electricity_t2_tariff: Number(safeTariffs.electricity_t2),
      electricity_t3_tariff: Number(safeTariffs.electricity_t3),
      delta_cold_water: result ? Number(result.delta.cold_water) : null,
      delta_hot_water: result ? Number(result.delta.hot_water) : null,
      delta_electricity_t1: result ? Number(result.delta.electricity_t1) : null,
      delta_electricity_t2: result ? Number(result.delta.electricity_t2) : null,
      delta_electricity_t3: result ? Number(result.delta.electricity_t3) : null,
      water_bill: result ? Number(result.water_bill) : null,
      electricity_bill: result ? Number(result.electricity_bill) : null,
      total_bill: result ? Number(result.total_bill) : null,
    };

    const { error } = await supabase.from("meter_readings").upsert(payload, {
      onConflict: "user_id,month_key",
    });

    if (error) {
      throw new Error(`Ошибка сохранения в Supabase: ${error.message}`);
    }
  }

  return {
    getMonthRecord,
    getMonthReadings,
    listMonthRecords,
    saveMonthRecord,
  };
}

export async function getMonthRecord(userId, monthKey) {
  return createStorageService().getMonthRecord(userId, monthKey);
}

export async function getMonthReadings(userId, monthKey) {
  return createStorageService().getMonthReadings(userId, monthKey);
}

export async function listMonthRecords(userId) {
  return createStorageService().listMonthRecords(userId);
}

export async function saveMonthRecord(userId, monthKey, readings, tariffs, result) {
  return createStorageService().saveMonthRecord(userId, monthKey, readings, tariffs, result);
}
