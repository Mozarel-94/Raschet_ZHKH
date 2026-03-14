import { getCurrentUser, onAuthStateChange, requireAuth, signOutUser } from "../lib/auth.js";
import { fetchHistory } from "../lib/history-api.js";

const state = {
  selectedMonth: new URLSearchParams(window.location.search).get("month") || "",
};

const elements = {
  userEmail: document.getElementById("history-user-email"),
  signOutButton: document.getElementById("history-sign-out-button"),
  messageBox: document.getElementById("history-message-box"),
  months: document.getElementById("history-months"),
  overview: document.getElementById("history-overview"),
  totalPaymentChart: document.getElementById("total-payment-chart"),
  waterChart: document.getElementById("water-chart"),
  electricityChart: document.getElementById("electricity-chart"),
  detail: document.getElementById("history-month-detail"),
};

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

function formatMoney(value) {
  return value === null || value === undefined ? "—" : `${Number(value).toFixed(2)} руб.`;
}

function formatValue(value) {
  return value === null || value === undefined ? "—" : Number(value).toFixed(2);
}

function renderMonthList(months) {
  if (!months.length) {
    elements.months.innerHTML = `<div class="result-empty">История пока пуста.</div>`;
    return;
  }

  elements.months.innerHTML = months
    .map(
      (month) => `
        <button
          class="history-month-item ${month.month_key === state.selectedMonth ? "active" : ""}"
          type="button"
          data-month-key="${month.month_key}"
        >
          <span>${month.label}</span>
          <strong>${formatMoney(month.total_bill)}</strong>
        </button>
      `
    )
    .join("");

  for (const button of elements.months.querySelectorAll("[data-month-key]")) {
    button.addEventListener("click", () => {
      state.selectedMonth = button.dataset.monthKey || "";
      const url = new URL(window.location.href);
      url.searchParams.set("month", state.selectedMonth);
      window.history.replaceState({}, "", url);
      void loadHistory();
    });
  }
}

function renderStatGrid(analytics) {
  const average = analytics.averages || {};
  const expensive = analytics.most_expensive_month;

  elements.overview.innerHTML = `
    <article class="stat-card">
      <span class="stat-label">Средний платёж</span>
      <strong>${formatMoney(average.total_bill)}</strong>
    </article>
    <article class="stat-card">
      <span class="stat-label">Средняя вода</span>
      <strong>${formatMoney(average.water_bill)}</strong>
    </article>
    <article class="stat-card">
      <span class="stat-label">Среднее электричество</span>
      <strong>${formatMoney(average.electricity_bill)}</strong>
    </article>
    <article class="stat-card">
      <span class="stat-label">Средний расход воды</span>
      <strong>${formatValue(
        average.cold_water !== null && average.hot_water !== null
          ? average.cold_water + average.hot_water
          : null
      )}</strong>
    </article>
    <article class="stat-card">
      <span class="stat-label">Средний расход электричества</span>
      <strong>${formatValue(average.electricity_total)}</strong>
    </article>
    <article class="stat-card">
      <span class="stat-label">Самый дорогой месяц</span>
      <strong>${expensive ? `${expensive.label} • ${formatMoney(expensive.total_bill)}` : "—"}</strong>
    </article>
  `;
}

function renderChart(container, series, unit) {
  if (!series.length) {
    container.innerHTML = `<div class="result-empty">Недостаточно данных для графика.</div>`;
    return;
  }

  const maxValue = Math.max(...series.map((item) => item.value), 0);

  container.innerHTML = `
    <div class="chart-bars">
      ${series
        .map((item) => {
          const height = maxValue === 0 ? 0 : Math.max((item.value / maxValue) * 100, 4);
          return `
            <div class="chart-bar-item">
              <div class="chart-bar-value">${formatValue(item.value)} ${unit}</div>
              <div class="chart-bar-track">
                <div class="chart-bar-fill" style="height: ${height}%"></div>
              </div>
              <div class="chart-bar-label">${item.label}</div>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderComparisons(comparisons) {
  if (!comparisons) {
    return `<div class="result-empty">Нет данных для сравнений.</div>`;
  }

  return `
    <div class="comparison-grid">
      <article class="comparison-card">
        <span class="stat-label">К прошлому месяцу</span>
        <strong>${formatMoney(comparisons.previous_month_total_diff)}</strong>
        <span class="muted">${comparisons.previous_month?.label || "Нет данных"}</span>
      </article>
      <article class="comparison-card">
        <span class="stat-label">К прошлому году</span>
        <strong>${formatMoney(comparisons.previous_year_total_diff)}</strong>
        <span class="muted">${comparisons.previous_year?.label || "Нет данных"}</span>
      </article>
    </div>
  `;
}

function renderFormulaSection(formulas) {
  if (!formulas) {
    return `<div class="result-empty">Для этого месяца ещё нет полного расчёта: отсутствуют данные предыдущего периода.</div>`;
  }

  return [
    { title: "Вода", group: formulas.water },
    { title: "Электричество", group: formulas.electricity },
  ]
    .map(
      ({ title, group }) => `
        <section class="formula-block">
          <h3>${title}</h3>
          <p class="muted">${group.formula}</p>
          <div class="formula-parts">
            ${group.parts
              .map(
                (part) => `
                  <div class="formula-part">
                    <span>${part.label}</span>
                    <span>${part.expression}</span>
                    <strong>${formatMoney(part.value)}</strong>
                  </div>
                `
              )
              .join("")}
          </div>
          <div class="result-row total">
            <span>Итого</span>
            <strong>${formatMoney(group.total)}</strong>
          </div>
        </section>
      `
    )
    .join("");
}

function renderMonthDetail(selectedMonth) {
  if (!selectedMonth) {
    elements.detail.innerHTML = `<div class="result-empty">Выберите месяц из списка слева.</div>`;
    return;
  }

  const { readings, tariffs, delta, formulas, comparisons } = selectedMonth;

  elements.detail.innerHTML = `
    <section class="detail-header-card">
      <div>
        <div class="eyebrow">Период</div>
        <h3>${selectedMonth.label}</h3>
      </div>
      <strong class="detail-total">${formatMoney(selectedMonth.total_bill)}</strong>
    </section>

    ${renderComparisons(comparisons)}

    <section class="detail-grid">
      <article class="detail-card">
        <h3>Показания</h3>
        <div class="detail-list">
          <div><span>Холодная вода</span><strong>${formatValue(readings.cold_water)}</strong></div>
          <div><span>Горячая вода</span><strong>${formatValue(readings.hot_water)}</strong></div>
          <div><span>Т1</span><strong>${formatValue(readings.electricity_t1)}</strong></div>
          <div><span>Т2</span><strong>${formatValue(readings.electricity_t2)}</strong></div>
          <div><span>Т3</span><strong>${formatValue(readings.electricity_t3)}</strong></div>
        </div>
      </article>

      <article class="detail-card">
        <h3>Использованные тарифы</h3>
        <div class="detail-list">
          <div><span>Холодная вода</span><strong>${formatMoney(tariffs.cold_water)}</strong></div>
          <div><span>Горячая вода</span><strong>${formatMoney(tariffs.hot_water)}</strong></div>
          <div><span>Водоотведение</span><strong>${formatMoney(tariffs.wastewater)}</strong></div>
          <div><span>Т1</span><strong>${formatMoney(tariffs.electricity_t1)}</strong></div>
          <div><span>Т2</span><strong>${formatMoney(tariffs.electricity_t2)}</strong></div>
          <div><span>Т3</span><strong>${formatMoney(tariffs.electricity_t3)}</strong></div>
        </div>
      </article>

      <article class="detail-card">
        <h3>Расход</h3>
        <div class="detail-list">
          <div><span>Холодная вода</span><strong>${formatValue(delta?.cold_water)}</strong></div>
          <div><span>Горячая вода</span><strong>${formatValue(delta?.hot_water)}</strong></div>
          <div><span>Т1</span><strong>${formatValue(delta?.electricity_t1)}</strong></div>
          <div><span>Т2</span><strong>${formatValue(delta?.electricity_t2)}</strong></div>
          <div><span>Т3</span><strong>${formatValue(delta?.electricity_t3)}</strong></div>
        </div>
      </article>
    </section>

    ${renderFormulaSection(formulas)}
  `;
}

async function loadHistory() {
  setMessage("", "");

  try {
    const payload = await fetchHistory(state.selectedMonth);

    if (payload.empty) {
      renderMonthList([]);
      renderStatGrid({ averages: {}, most_expensive_month: null });
      renderChart(elements.totalPaymentChart, [], "руб.");
      renderChart(elements.waterChart, [], "м3");
      renderChart(elements.electricityChart, [], "кВт");
      renderMonthDetail(null);
      setMessage("info", "История пока пуста. Сохраните хотя бы один месяц на главной странице.");
      return;
    }

    state.selectedMonth = payload.selected_month?.month_key || state.selectedMonth;
    renderMonthList(payload.months);
    renderStatGrid(payload.analytics);
    renderChart(elements.totalPaymentChart, payload.analytics.total_payment_chart, "руб.");
    renderChart(elements.waterChart, payload.analytics.water_consumption_chart, "м3");
    renderChart(elements.electricityChart, payload.analytics.electricity_consumption_chart, "кВт");
    renderMonthDetail(payload.selected_month);
  } catch (error) {
    renderMonthList([]);
    renderStatGrid({ averages: {}, most_expensive_month: null });
    renderChart(elements.totalPaymentChart, [], "руб.");
    renderChart(elements.waterChart, [], "м3");
    renderChart(elements.electricityChart, [], "кВт");
    renderMonthDetail(null);
    setMessage("error", error instanceof Error ? error.message : "Не удалось загрузить историю.");
  }
}

function attachEvents() {
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

  attachEvents();
  await loadHistory();
}

init().catch((error) => {
  setMessage("error", error instanceof Error ? error.message : "Ошибка инициализации истории.");
});
