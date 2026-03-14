import {
  authFetch,
  getCurrentUser,
  onAuthStateChange,
  requireAuth,
  signOutUser,
} from "./lib/auth.js";

const monthOptions = [
  ["01", "Январь"],
  ["02", "Февраль"],
  ["03", "Март"],
  ["04", "Апрель"],
  ["05", "Май"],
  ["06", "Июнь"],
  ["07", "Июль"],
  ["08", "Август"],
  ["09", "Сентябрь"],
  ["10", "Октябрь"],
  ["11", "Ноябрь"],
  ["12", "Декабрь"],
];

const currentYear = new Date().getFullYear();
const yearOptions = Array.from(
  { length: Math.max(currentYear, 2026) - 2026 + 6 },
  (_, index) => String(2026 + index)
);

const defaultTariffs = {
  cold_water: "65.77",
  hot_water: "312.50",
  wastewater: "51.62",
  electricity_t1: "10.23",
  electricity_t2: "3.71",
  electricity_t3: "7.16",
};

const state = {
  tariffsEditable: false,
  tariffsCollapsed: true,
  selectedYear: String(Math.max(currentYear, 2026)),
  selectedMonth: currentYear >= 2026 ? String(new Date().getMonth() + 1).padStart(2, "0") : "01",
};

const elements = {
  form: document.getElementById("calculator-form"),
  year: document.getElementById("calculation-year"),
  month: document.getElementById("calculation-month"),
  coldWater: document.getElementById("cold-water"),
  hotWater: document.getElementById("hot-water"),
  t1: document.getElementById("electricity-t1"),
  t2: document.getElementById("electricity-t2"),
  t3: document.getElementById("electricity-t3"),
  coldWaterTariff: document.getElementById("cold-water-tariff"),
  hotWaterTariff: document.getElementById("hot-water-tariff"),
  wastewaterTariff: document.getElementById("wastewater-tariff"),
  t1Tariff: document.getElementById("electricity-t1-tariff"),
  t2Tariff: document.getElementById("electricity-t2-tariff"),
  t3Tariff: document.getElementById("electricity-t3-tariff"),
  messageBox: document.getElementById("message-box"),
  resultContent: document.getElementById("result-content"),
  deltaContent: document.getElementById("delta-content"),
  userEmail: document.getElementById("user-email"),
  signOutButton: document.getElementById("sign-out-button"),
  toggleCollapse: document.getElementById("toggle-collapse"),
  toggleEdit: document.getElementById("toggle-edit"),
  tariffFields: Array.from(document.querySelectorAll(".tariff-field")),
  tariffInputs: Array.from(document.querySelectorAll(".tariff-input")),
};

function formatMoney(value) {
  return `${Number(value).toFixed(2)} руб.`;
}

function formatNumber(value) {
  return Number(value).toFixed(2);
}

function renderYearOptions() {
  elements.year.innerHTML = yearOptions
    .map((year) => `<option value="${year}">${year}</option>`)
    .join("");
}

function renderMonthOptions() {
  elements.month.innerHTML = monthOptions
    .map(([value, label]) => `<option value="${value}">${label}</option>`)
    .join("");
}

function applyTariffs(tariffs = defaultTariffs) {
  elements.coldWaterTariff.value = tariffs.cold_water;
  elements.hotWaterTariff.value = tariffs.hot_water;
  elements.wastewaterTariff.value = tariffs.wastewater;
  elements.t1Tariff.value = tariffs.electricity_t1;
  elements.t2Tariff.value = tariffs.electricity_t2;
  elements.t3Tariff.value = tariffs.electricity_t3;
}

function setTariffsEditable(isEditable) {
  state.tariffsEditable = isEditable;
  for (const input of elements.tariffInputs) {
    input.readOnly = !isEditable;
  }
  elements.toggleEdit.textContent = isEditable ? "Заблокировать тарифы" : "Изменить тарифы";
}

function setTariffsCollapsed(isCollapsed) {
  state.tariffsCollapsed = isCollapsed;
  for (const field of elements.tariffFields) {
    field.classList.toggle("collapsed", isCollapsed);
  }
  elements.toggleCollapse.textContent = isCollapsed ? "Развернуть тарифы" : "Свернуть тарифы";
}

function setMessage(type, text) {
  if (!text) {
    elements.messageBox.innerHTML = "";
    return;
  }

  elements.messageBox.innerHTML = `<div class="message ${type}">${text}</div>`;
}

function setUserEmail(user) {
  elements.userEmail.textContent = user?.email || "";
}

function renderEmptyResults() {
  elements.resultContent.innerHTML = "Выберите период и заполните показания.";
  elements.deltaContent.innerHTML = "Расход за месяц появится после расчёта.";
}

function renderResults(payload) {
  if (!payload?.result) {
    renderEmptyResults();
    return;
  }

  elements.resultContent.innerHTML = `
    <p class="muted">Сравнение с месяцем: <strong>${payload.previous_month_key}</strong></p>
    <div class="result-row"><span>Счёт за воду</span><strong>${formatMoney(payload.result.water_bill)}</strong></div>
    <div class="result-row"><span>Счёт за электричество</span><strong>${formatMoney(payload.result.electricity_bill)}</strong></div>
    <div class="result-row total"><span>Счёт суммарный</span><strong>${formatMoney(payload.result.total_bill)}</strong></div>
  `;

  elements.deltaContent.innerHTML = `
    <div class="delta-row"><span>Холодная вода</span><strong>${formatNumber(payload.result.delta.cold_water)}</strong></div>
    <div class="delta-row"><span>Горячая вода</span><strong>${formatNumber(payload.result.delta.hot_water)}</strong></div>
    <div class="delta-row"><span>Т1</span><strong>${formatNumber(payload.result.delta.electricity_t1)}</strong></div>
    <div class="delta-row"><span>Т2</span><strong>${formatNumber(payload.result.delta.electricity_t2)}</strong></div>
    <div class="delta-row"><span>Т3</span><strong>${formatNumber(payload.result.delta.electricity_t3)}</strong></div>
  `;
}

function fillReadings(readings) {
  elements.coldWater.value = readings?.cold_water ?? "";
  elements.hotWater.value = readings?.hot_water ?? "";
  elements.t1.value = readings?.electricity_t1 ?? "";
  elements.t2.value = readings?.electricity_t2 ?? "";
  elements.t3.value = readings?.electricity_t3 ?? "";
}

async function loadMonthData() {
  const params = new URLSearchParams({
    year: state.selectedYear,
    month: state.selectedMonth,
  });

  const response = await authFetch(`/api/month?${params.toString()}`);
  const payload = await response.json();

  if (!response.ok) {
    setMessage("error", payload.error || "Не удалось загрузить данные месяца.");
    fillReadings(null);
    renderEmptyResults();
    return;
  }

  applyTariffs(payload.tariffs || defaultTariffs);
  fillReadings(payload.readings);
  renderEmptyResults();

  if (payload.readings) {
    setMessage("info", `Загружены сохранённые показания за ${payload.month_key}.`);
  } else if (payload.previous_exists) {
    setMessage(
      "info",
      `Для ${payload.month_key} ещё нет сохранённых показаний. Предыдущий месяц для расчёта: ${payload.previous_month_key}.`
    );
  } else {
    setMessage("info", `Для ${payload.month_key} ещё нет сохранённых показаний.`);
  }
}

async function submitCalculation(event) {
  event.preventDefault();

  const payload = {
    year: state.selectedYear,
    month: state.selectedMonth,
    readings: {
      cold_water: elements.coldWater.value,
      hot_water: elements.hotWater.value,
      electricity_t1: elements.t1.value,
      electricity_t2: elements.t2.value,
      electricity_t3: elements.t3.value,
    },
    tariffs: {
      cold_water: elements.coldWaterTariff.value,
      hot_water: elements.hotWaterTariff.value,
      wastewater: elements.wastewaterTariff.value,
      electricity_t1: elements.t1Tariff.value,
      electricity_t2: elements.t2Tariff.value,
      electricity_t3: elements.t3Tariff.value,
    },
  };

  const response = await authFetch("/api/calculate", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const result = await response.json();

  if (!response.ok) {
    setMessage("error", result.error || "Не удалось выполнить расчёт.");
    return;
  }

  setMessage("info", result.message || "Показания сохранены.");
  renderResults(result);
}

function syncSelectedPeriod() {
  state.selectedYear = elements.year.value;
  state.selectedMonth = elements.month.value;
}

function attachEvents() {
  elements.year.addEventListener("change", async () => {
    syncSelectedPeriod();
    await loadMonthData();
  });

  elements.month.addEventListener("change", async () => {
    syncSelectedPeriod();
    await loadMonthData();
  });

  elements.toggleEdit.addEventListener("click", () => {
    setTariffsEditable(!state.tariffsEditable);
  });

  elements.toggleCollapse.addEventListener("click", () => {
    setTariffsCollapsed(!state.tariffsCollapsed);
  });

  elements.form.addEventListener("submit", submitCalculation);

  elements.signOutButton.addEventListener("click", async () => {
    try {
      await signOutUser();
      window.location.replace("/login");
    } catch (error) {
      setMessage("error", error instanceof Error ? error.message : "Не удалось выйти из системы.");
    }
  });
}

async function init() {
  const session = await requireAuth();
  if (!session) {
    return;
  }

  setUserEmail(await getCurrentUser());

  await onAuthStateChange((nextSession) => {
    if (!nextSession) {
      window.location.replace("/login");
      return;
    }

    setUserEmail(nextSession.user);
  });

  renderYearOptions();
  renderMonthOptions();
  elements.year.value = state.selectedYear;
  elements.month.value = state.selectedMonth;
  applyTariffs(defaultTariffs);
  setTariffsEditable(false);
  setTariffsCollapsed(true);
  renderEmptyResults();
  attachEvents();
  await loadMonthData();
}

init().catch((error) => {
  setMessage("error", error instanceof Error ? error.message : "Ошибка инициализации.");
});
