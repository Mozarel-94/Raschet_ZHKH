import * as React from "react";

type ChartPoint = {
  month_key: string;
  label: string;
  value: number;
};

type MonthSummary = {
  month_key: string;
  label: string;
  total_bill: number | null;
  water_bill: number | null;
  electricity_bill: number | null;
  has_complete_calculation: boolean;
};

type SelectedMonth = {
  month_key: string;
  label: string;
  total_bill: number | null;
  readings: {
    cold_water: number;
    hot_water: number;
    electricity_t1: number;
    electricity_t2: number;
    electricity_t3: number;
  };
  tariffs: {
    cold_water: number;
    hot_water: number;
    wastewater: number;
    electricity_t1: number;
    electricity_t2: number;
    electricity_t3: number;
  };
  delta: {
    cold_water: number;
    hot_water: number;
    electricity_t1: number;
    electricity_t2: number;
    electricity_t3: number;
  } | null;
  formulas: {
    water: {
      formula: string;
      parts: Array<{ label: string; expression: string; value: number }>;
      total: number | null;
    };
    electricity: {
      formula: string;
      parts: Array<{ label: string; expression: string; value: number }>;
      total: number | null;
    };
  } | null;
};

type HistoryPayload = {
  months: MonthSummary[];
  analytics: {
    total_payment_chart: ChartPoint[];
    water_consumption_chart: ChartPoint[];
    electricity_consumption_chart: ChartPoint[];
    averages: {
      total_bill: number | null;
      water_bill: number | null;
      electricity_bill: number | null;
    };
    most_expensive_month: { month_key: string; label: string; total_bill: number } | null;
  };
  selected_month: SelectedMonth | null;
  empty: boolean;
};

function formatMoney(value: number | null) {
  return value === null ? "—" : `${value.toFixed(2)} руб.`;
}

function HistoryMonthList(props: {
  months: MonthSummary[];
  selectedMonth: string | null;
  onSelect: (monthKey: string) => void;
}) {
  return (
    <div className="history-list">
      {props.months.map((month) => (
        <button
          key={month.month_key}
          className={month.month_key === props.selectedMonth ? "history-month-item active" : "history-month-item"}
          onClick={() => props.onSelect(month.month_key)}
          type="button"
        >
          <span>{month.label}</span>
          <strong>{formatMoney(month.total_bill)}</strong>
        </button>
      ))}
    </div>
  );
}

function MiniBarChart(props: { title: string; data: ChartPoint[]; unit: string }) {
  const max = props.data.reduce((current, item) => Math.max(current, item.value), 0);

  return (
    <section className="chart-card">
      <h3>{props.title}</h3>
      <div className="chart-bars">
        {props.data.map((item) => (
          <div key={item.month_key} className="chart-bar-item">
            <div className="chart-bar-value">{item.value.toFixed(2)} {props.unit}</div>
            <div className="chart-bar-track">
              <div
                className="chart-bar-fill"
                style={{ height: `${max === 0 ? 0 : Math.max((item.value / max) * 100, 4)}%` }}
              />
            </div>
            <div className="chart-bar-label">{item.label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function HistoryAnalyticsPage(props: {
  data: HistoryPayload;
  selectedMonth: string | null;
  onSelectMonth: (monthKey: string) => void;
}) {
  return (
    <div className="history-layout">
      <aside className="md-card history-sidebar-card">
        <div className="eyebrow">Месяцы</div>
        <h2>История</h2>
        <HistoryMonthList
          months={props.data.months}
          selectedMonth={props.selectedMonth}
          onSelect={props.onSelectMonth}
        />
      </aside>

      <section className="history-content">
        <section className="md-card">
          <div className="eyebrow">Аналитика</div>
          <h2>Сводка</h2>
          <div className="stat-grid">
            <article className="stat-card">
              <span className="stat-label">Средний платёж</span>
              <strong>{formatMoney(props.data.analytics.averages.total_bill)}</strong>
            </article>
            <article className="stat-card">
              <span className="stat-label">Самый дорогой месяц</span>
              <strong>
                {props.data.analytics.most_expensive_month
                  ? `${props.data.analytics.most_expensive_month.label} • ${formatMoney(props.data.analytics.most_expensive_month.total_bill)}`
                  : "—"}
              </strong>
            </article>
          </div>
        </section>

        <section className="md-card">
          <div className="eyebrow">Тренды</div>
          <h2>Графики</h2>
          <div className="chart-stack">
            <MiniBarChart title="Общий платёж" data={props.data.analytics.total_payment_chart} unit="руб." />
            <MiniBarChart title="Расход воды" data={props.data.analytics.water_consumption_chart} unit="м3" />
            <MiniBarChart
              title="Расход электричества"
              data={props.data.analytics.electricity_consumption_chart}
              unit="кВт"
            />
          </div>
        </section>
      </section>
    </div>
  );
}
