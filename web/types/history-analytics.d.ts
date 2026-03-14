export type Tariffs = {
  cold_water: number;
  hot_water: number;
  wastewater: number;
  electricity_t1: number;
  electricity_t2: number;
  electricity_t3: number;
};

export type MeterReadings = {
  cold_water: number;
  hot_water: number;
  electricity_t1: number;
  electricity_t2: number;
  electricity_t3: number;
};

export type ConsumptionDelta = MeterReadings;

export type MonthlyRecord = {
  month_key: string;
  calculation_year: number;
  calculation_month: number;
  readings: MeterReadings;
  tariffs: Tariffs;
  delta: ConsumptionDelta | null;
  water_bill: number | null;
  electricity_bill: number | null;
  total_bill: number | null;
  created_at: string;
  updated_at: string;
};

export type MonthComparison = {
  previous_month_total_diff: number | null;
  previous_year_total_diff: number | null;
  previous_month_delta_diff: ConsumptionDelta | null;
  previous_year_delta_diff: ConsumptionDelta | null;
};

export type HistoryAnalytics = {
  total_payment_chart: Array<{ month_key: string; value: number }>;
  water_consumption_chart: Array<{ month_key: string; value: number }>;
  electricity_consumption_chart: Array<{ month_key: string; value: number }>;
  averages: {
    total_bill: number | null;
    water_bill: number | null;
    electricity_bill: number | null;
    cold_water: number | null;
    hot_water: number | null;
    electricity_total: number | null;
  };
  most_expensive_month: {
    month_key: string;
    total_bill: number;
  } | null;
};
