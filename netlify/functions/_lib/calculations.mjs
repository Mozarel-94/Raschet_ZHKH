const DEFAULT_TARIFFS = {
  cold_water: 65.77,
  hot_water: 312.5,
  wastewater: 51.62,
  electricity_t1: 10.23,
  electricity_t2: 3.71,
  electricity_t3: 7.16,
};

export function getDefaultTariffs() {
  return { ...DEFAULT_TARIFFS };
}

export function normalizeMonthKey(year, month) {
  const yearNumber = Number.parseInt(String(year), 10);
  const monthNumber = Number.parseInt(String(month), 10);

  if (!Number.isInteger(yearNumber) || yearNumber < 2026) {
    throw new Error("Год расчёта должен быть не меньше 2026.");
  }

  if (!Number.isInteger(monthNumber) || monthNumber < 1 || monthNumber > 12) {
    throw new Error("Месяц расчёта должен быть от 1 до 12.");
  }

  return `${yearNumber}-${String(monthNumber).padStart(2, "0")}`;
}

export function getPreviousMonthKey(monthKey) {
  const [yearText, monthText] = monthKey.split("-");
  const year = Number.parseInt(yearText, 10);
  const month = Number.parseInt(monthText, 10);

  if (month === 1) {
    return `${year - 1}-12`;
  }

  return `${year}-${String(month - 1).padStart(2, "0")}`;
}

export function getPreviousYearMonthKey(monthKey) {
  const [yearText, monthText] = monthKey.split("-");
  const year = Number.parseInt(yearText, 10);
  return `${year - 1}-${monthText}`;
}

export function parseReading(value, label) {
  const normalizedValue = String(value ?? "").trim().replace(",", ".");
  if (!normalizedValue) {
    throw new Error(`Поле "${label}" не может быть пустым.`);
  }

  const parsed = Number.parseFloat(normalizedValue);
  if (Number.isNaN(parsed)) {
    throw new Error(`Поле "${label}" должно быть числом.`);
  }

  if (parsed < 0) {
    throw new Error(`Поле "${label}" не может быть отрицательным.`);
  }

  return parsed;
}

export function parseTariff(value, label) {
  return parseReading(value, label);
}

export function calculateDelta(currentReadings, previousReadings) {
  return {
    cold_water: currentReadings.cold_water - previousReadings.cold_water,
    hot_water: currentReadings.hot_water - previousReadings.hot_water,
    electricity_t1: currentReadings.electricity_t1 - previousReadings.electricity_t1,
    electricity_t2: currentReadings.electricity_t2 - previousReadings.electricity_t2,
    electricity_t3: currentReadings.electricity_t3 - previousReadings.electricity_t3,
  };
}

export function validateDelta(delta) {
  const labels = {
    cold_water: "Холодная вода",
    hot_water: "Горячая вода",
    electricity_t1: "Т1",
    electricity_t2: "Т2",
    electricity_t3: "Т3",
  };

  const negativeFields = Object.entries(delta)
    .filter(([, value]) => value < 0)
    .map(([key]) => labels[key]);

  if (negativeFields.length > 0) {
    throw new Error(
      `Показания за выбранный месяц меньше предыдущего месяца: ${negativeFields.join(", ")}.`
    );
  }
}

export function calculateWaterBill(delta, tariffs) {
  return (
    delta.cold_water * tariffs.cold_water +
    delta.hot_water * tariffs.hot_water +
    (delta.cold_water + delta.hot_water) * tariffs.wastewater
  );
}

export function calculateElectricityBill(delta, tariffs) {
  return (
    delta.electricity_t1 * tariffs.electricity_t1 +
    delta.electricity_t2 * tariffs.electricity_t2 +
    delta.electricity_t3 * tariffs.electricity_t3
  );
}

export function calculateTotals(currentReadings, previousReadings, tariffs) {
  const delta = calculateDelta(currentReadings, previousReadings);
  validateDelta(delta);

  const waterBill = calculateWaterBill(delta, tariffs);
  const electricityBill = calculateElectricityBill(delta, tariffs);

  return {
    water_bill: waterBill,
    electricity_bill: electricityBill,
    total_bill: waterBill + electricityBill,
    delta,
  };
}

export function formatMonthLabel(monthKey) {
  const monthNames = {
    "01": "Январь",
    "02": "Февраль",
    "03": "Март",
    "04": "Апрель",
    "05": "Май",
    "06": "Июнь",
    "07": "Июль",
    "08": "Август",
    "09": "Сентябрь",
    "10": "Октябрь",
    "11": "Ноябрь",
    "12": "Декабрь",
  };

  const [year, month] = monthKey.split("-");
  return `${monthNames[month]} ${year}`;
}
