"""Simple web interface for utility payment calculation."""

from __future__ import annotations

from datetime import date
from html import escape
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from calculator import (
    CalculationInputs,
    CalculationResult,
    MeterReadings,
    Tariffs,
    calculate_totals,
)
from storage import get_month_readings, get_previous_month_readings, save_month_readings

HOST = "127.0.0.1"
PORT = 8000
ENCODING = "utf-8"

FIELD_LABELS = {
    "calculation_year": "Год расчёта",
    "calculation_month": "Месяц расчёта",
    "cold_water": "Холодная вода",
    "hot_water": "Горячая вода",
    "electricity_t1": "Т1",
    "electricity_t2": "Т2",
    "electricity_t3": "Т3",
    "cold_water_tariff": "Тариф холодной воды",
    "hot_water_tariff": "Тариф горячей воды",
    "wastewater_tariff": "Тариф водоотведения",
    "electricity_t1_tariff": "Тариф электроэнергии 1",
    "electricity_t2_tariff": "Тариф электроэнергии 2",
    "electricity_t3_tariff": "Тариф электроэнергии 3",
}

DEFAULT_FORM_VALUES = {
    "calculation_year": str(max(date.today().year, 2026)),
    "calculation_month": f"{date.today().month:02d}" if date.today().year >= 2026 else "01",
    "cold_water": "",
    "hot_water": "",
    "electricity_t1": "",
    "electricity_t2": "",
    "electricity_t3": "",
    "cold_water_tariff": "65.77",
    "hot_water_tariff": "312.50",
    "wastewater_tariff": "51.62",
    "electricity_t1_tariff": "10.23",
    "electricity_t2_tariff": "3.71",
    "electricity_t3_tariff": "7.16",
}

MONTH_OPTIONS = [
    ("01", "Январь"),
    ("02", "Февраль"),
    ("03", "Март"),
    ("04", "Апрель"),
    ("05", "Май"),
    ("06", "Июнь"),
    ("07", "Июль"),
    ("08", "Август"),
    ("09", "Сентябрь"),
    ("10", "Октябрь"),
    ("11", "Ноябрь"),
    ("12", "Декабрь"),
]

YEAR_OPTIONS = [str(year) for year in range(2026, max(date.today().year, 2026) + 6)]


def _parse_float(form_data: dict[str, str], field_name: str) -> float:
    raw_value = form_data.get(field_name, "").strip().replace(",", ".")
    if not raw_value:
        raise ValueError(f"Поле '{FIELD_LABELS[field_name]}' не может быть пустым.")

    try:
        value = float(raw_value)
    except ValueError as error:
        raise ValueError(f"Поле '{FIELD_LABELS[field_name]}' должно быть числом.") from error

    if value < 0:
        raise ValueError(
            f"Поле '{FIELD_LABELS[field_name]}' не может быть отрицательным."
        )

    return value


def _parse_month_key(form_data: dict[str, str]) -> str:
    year_value = form_data.get("calculation_year", "").strip()
    month_value = form_data.get("calculation_month", "").strip()

    if year_value not in YEAR_OPTIONS:
        raise ValueError("Поле 'Год расчёта' должно содержать корректный год.")

    valid_month_values = {value for value, _label in MONTH_OPTIONS}
    if month_value not in valid_month_values:
        raise ValueError("Поле 'Месяц расчёта' должно содержать корректный месяц.")

    return f"{year_value}-{month_value}"


def _build_readings(form_data: dict[str, str]) -> MeterReadings:
    return MeterReadings(
        cold_water=_parse_float(form_data, "cold_water"),
        hot_water=_parse_float(form_data, "hot_water"),
        electricity_t1=_parse_float(form_data, "electricity_t1"),
        electricity_t2=_parse_float(form_data, "electricity_t2"),
        electricity_t3=_parse_float(form_data, "electricity_t3"),
    )


def _build_tariffs(form_data: dict[str, str]) -> Tariffs:
    return Tariffs(
        cold_water=_parse_float(form_data, "cold_water_tariff"),
        hot_water=_parse_float(form_data, "hot_water_tariff"),
        wastewater=_parse_float(form_data, "wastewater_tariff"),
        electricity_t1=_parse_float(form_data, "electricity_t1_tariff"),
        electricity_t2=_parse_float(form_data, "electricity_t2_tariff"),
        electricity_t3=_parse_float(form_data, "electricity_t3_tariff"),
    )


def _value(form_data: dict[str, str] | None, field_name: str) -> str:
    if not form_data:
        return escape(DEFAULT_FORM_VALUES[field_name])
    return escape(form_data.get(field_name, DEFAULT_FORM_VALUES[field_name]))


def _money(value: float) -> str:
    return f"{value:.2f} руб."


def _build_form_data_for_month(
    month_key: str,
    existing_form_data: dict[str, str] | None = None,
) -> dict[str, str]:
    year_value, month_value = month_key.split("-")
    form_data = dict(DEFAULT_FORM_VALUES)
    form_data["calculation_year"] = year_value
    form_data["calculation_month"] = month_value

    if existing_form_data:
        for key, value in existing_form_data.items():
            if key in form_data and key.endswith("_tariff"):
                form_data[key] = value

    saved_readings = get_month_readings(month_key)
    if saved_readings is not None:
        form_data["cold_water"] = f"{saved_readings.cold_water:.2f}"
        form_data["hot_water"] = f"{saved_readings.hot_water:.2f}"
        form_data["electricity_t1"] = f"{saved_readings.electricity_t1:.2f}"
        form_data["electricity_t2"] = f"{saved_readings.electricity_t2:.2f}"
        form_data["electricity_t3"] = f"{saved_readings.electricity_t3:.2f}"

    return form_data


def _render_select_options(
    options: list[tuple[str, str]],
    selected_value: str,
) -> str:
    rendered = []
    for value, label in options:
        selected_attr = " selected" if value == selected_value else ""
        rendered.append(
            f'<option value="{escape(value)}"{selected_attr}>{escape(label)}</option>'
        )
    return "".join(rendered)


def _render_year_options(selected_value: str) -> str:
    rendered = []
    for year in YEAR_OPTIONS:
        selected_attr = " selected" if year == selected_value else ""
        rendered.append(f'<option value="{escape(year)}"{selected_attr}>{escape(year)}</option>')
    return "".join(rendered)


def _render_summary(result: CalculationResult | None, previous_month: str | None) -> str:
    if result is None:
        return """
        <div class="result-card empty">
          <div class="eyebrow">Итог</div>
          <h2>Результаты расчёта</h2>
          <p>Выберите период, введите текущие показания и сохраните расчёт.</p>
        </div>
        """

    previous_text = (
        f"<p class=\"muted\">Сравнение с месяцем: <strong>{escape(previous_month)}</strong></p>"
        if previous_month
        else ""
    )

    return f"""
    <div class="result-card">
      <div class="eyebrow">Итог</div>
      <h2>Результаты</h2>
      {previous_text}
      <div class="result-row">
        <span>Счёт за воду</span>
        <strong>{escape(_money(result.water_bill))}</strong>
      </div>
      <div class="result-row">
        <span>Счёт за электричество</span>
        <strong>{escape(_money(result.electricity_bill))}</strong>
      </div>
      <div class="result-row total">
        <span>Счёт суммарный</span>
        <strong>{escape(_money(result.total_bill))}</strong>
      </div>
    </div>
    """


def _render_delta(result: CalculationResult | None) -> str:
    if result is None:
        return ""

    return f"""
    <div class="support-card">
      <div class="eyebrow">Расход</div>
      <div class="delta-list">
        <div class="delta-item"><span>Холодная вода</span><strong>{escape(f"{result.delta.cold_water:.2f}")}</strong></div>
        <div class="delta-item"><span>Горячая вода</span><strong>{escape(f"{result.delta.hot_water:.2f}")}</strong></div>
        <div class="delta-item"><span>Т1</span><strong>{escape(f"{result.delta.electricity_t1:.2f}")}</strong></div>
        <div class="delta-item"><span>Т2</span><strong>{escape(f"{result.delta.electricity_t2:.2f}")}</strong></div>
        <div class="delta-item"><span>Т3</span><strong>{escape(f"{result.delta.electricity_t3:.2f}")}</strong></div>
      </div>
    </div>
    """


def _render_html(
    form_data: dict[str, str] | None = None,
    result: CalculationResult | None = None,
    error_message: str = "",
    info_message: str = "",
    previous_month: str | None = None,
) -> str:
    error_block = (
        f'<div class="message error">{escape(error_message)}</div>' if error_message else ""
    )
    info_block = (
        f'<div class="message info">{escape(info_message)}</div>' if info_message else ""
    )

    return f"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Расчёт коммунальных платежей</title>
  <style>
    :root {{
      --md-sys-color-primary: #6750a4;
      --md-sys-color-on-primary: #ffffff;
      --md-sys-color-primary-container: #e9ddff;
      --md-sys-color-on-primary-container: #22005d;
      --md-sys-color-secondary: #625b71;
      --md-sys-color-secondary-container: #e8def8;
      --md-sys-color-tertiary-container: #ffd8e4;
      --md-sys-color-surface: #fffbfe;
      --md-sys-color-surface-container: #f3edf7;
      --md-sys-color-surface-container-high: #ece6f0;
      --md-sys-color-surface-container-highest: #e6e0e9;
      --md-sys-color-surface-variant: #e7e0ec;
      --md-sys-color-outline: #79747e;
      --md-sys-color-outline-variant: #cac4d0;
      --md-sys-color-error-container: #f9dedc;
      --md-sys-color-on-error-container: #410e0b;
      --md-sys-color-info-container: #d3e3fd;
      --md-sys-color-on-info-container: #041e49;
      --md-sys-color-on-surface: #1d1b20;
      --md-sys-color-on-surface-variant: #49454f;
      --md-sys-elevation-1: 0 1px 2px rgba(0, 0, 0, 0.12), 0 1px 3px 1px rgba(0, 0, 0, 0.08);
      --md-sys-elevation-2: 0 2px 6px 2px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Roboto", sans-serif;
      color: var(--md-sys-color-on-surface);
      background:
        radial-gradient(circle at top left, rgba(233, 221, 255, 0.9) 0, transparent 28%),
        radial-gradient(circle at bottom right, rgba(255, 216, 228, 0.7) 0, transparent 24%),
        var(--md-sys-color-surface);
    }}
    .page {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    .hero {{
      margin-bottom: 24px;
      padding: 32px;
      border-radius: 28px;
      background: linear-gradient(
        135deg,
        var(--md-sys-color-primary-container),
        var(--md-sys-color-tertiary-container)
      );
      box-shadow: var(--md-sys-elevation-1);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 3rem;
      line-height: 1.1;
      letter-spacing: -0.02em;
    }}
    .hero p {{
      margin: 0;
      max-width: 860px;
      font-size: 1rem;
      line-height: 1.5;
      color: var(--md-sys-color-on-surface-variant);
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.85fr);
      gap: 24px;
      align-items: start;
    }}
    .card, .result-card, .support-card {{
      background: var(--md-sys-color-surface-container);
      border: 1px solid var(--md-sys-color-outline-variant);
      border-radius: 28px;
      padding: 24px;
      box-shadow: var(--md-sys-elevation-1);
    }}
    .result-card.empty {{
      color: var(--md-sys-color-on-surface-variant);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .eyebrow {{
      margin-bottom: 8px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--md-sys-color-primary);
    }}
    .section-title {{
      margin: 0 0 16px;
      font-size: 1.75rem;
      line-height: 1.2;
    }}
    .section-note {{
      margin: 0 0 18px;
      color: var(--md-sys-color-on-surface-variant);
    }}
    label {{
      display: block;
      margin-bottom: 8px;
      font-size: 0.875rem;
      font-weight: 500;
      color: var(--md-sys-color-on-surface-variant);
    }}
    input, select {{
      width: 100%;
      border: 1px solid var(--md-sys-color-outline);
      border-radius: 16px;
      padding: 16px;
      font-size: 1rem;
      background: var(--md-sys-color-surface);
      color: var(--md-sys-color-on-surface);
      outline: none;
      transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
    }}
    input:focus, select:focus {{
      border-color: var(--md-sys-color-primary);
      box-shadow: 0 0 0 3px rgba(103, 80, 164, 0.15);
    }}
    .full {{
      grid-column: 1 / -1;
    }}
    .tariff-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      grid-column: 1 / -1;
      margin-top: 8px;
      padding-top: 8px;
    }}
    .tariff-actions {{
      display: flex;
      gap: 10px;
      align-items: center;
    }}
    .tariff-header h3 {{
      margin: 0;
      font-size: 1.125rem;
      color: var(--md-sys-color-on-surface);
    }}
    .tariff-toggle {{
      padding: 10px 18px;
      font-size: 0.875rem;
      color: var(--md-sys-color-primary);
      background: var(--md-sys-color-primary-container);
      box-shadow: none;
    }}
    .tariff-collapse-toggle {{
      color: var(--md-sys-color-on-surface-variant);
      background: var(--md-sys-color-surface-container-high);
      border: 1px solid var(--md-sys-color-outline-variant);
    }}
    .tariff-section.collapsed {{
      display: none;
    }}
    .readonly-input {{
      background: var(--md-sys-color-surface-container-high);
      color: var(--md-sys-color-on-surface-variant);
      border-color: var(--md-sys-color-outline-variant);
    }}
    .actions {{
      margin-top: 24px;
    }}
    button {{
      border: 0;
      border-radius: 999px;
      padding: 14px 24px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      color: var(--md-sys-color-on-primary);
      background: var(--md-sys-color-primary);
      box-shadow: var(--md-sys-elevation-1);
      transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
    }}
    button:hover {{
      transform: translateY(-1px);
      box-shadow: var(--md-sys-elevation-2);
    }}
    .message {{
      margin-bottom: 16px;
      padding: 14px 16px;
      border-radius: 20px;
      border: 1px solid transparent;
    }}
    .error {{
      background: var(--md-sys-color-error-container);
      color: var(--md-sys-color-on-error-container);
    }}
    .info {{
      background: var(--md-sys-color-info-container);
      color: var(--md-sys-color-on-info-container);
    }}
    .result-row {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      padding: 16px 0;
      border-bottom: 1px solid var(--md-sys-color-outline-variant);
      font-size: 1rem;
    }}
    .result-row.total {{
      border-bottom: 0;
      font-size: 1.2rem;
    }}
    .support-card {{
      margin-top: 18px;
    }}
    .formula-note {{
      margin-top: 18px;
      padding: 20px;
      border-radius: 24px;
      background: var(--md-sys-color-secondary-container);
      color: var(--md-sys-color-on-surface-variant);
      font-size: 0.9rem;
      line-height: 1.6;
    }}
    .delta-list {{
      display: grid;
      gap: 12px;
    }}
    .delta-item {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid var(--md-sys-color-outline-variant);
      color: var(--md-sys-color-on-surface-variant);
    }}
    .delta-item:last-child {{
      border-bottom: 0;
      padding-bottom: 0;
    }}
    .muted {{
      margin: 0 0 10px;
      color: var(--md-sys-color-on-surface-variant);
      font-size: 0.875rem;
    }}
    @media (max-width: 860px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
      .grid {{
        grid-template-columns: 1fr;
      }}
      h1 {{
        font-size: 2.25rem;
      }}
      .tariff-header {{
        align-items: start;
        flex-direction: column;
      }}
      .tariff-actions {{
        width: 100%;
        flex-wrap: wrap;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <div class="eyebrow">Material Design 3</div>
      <h1>Расчёт коммунальных платежей</h1>
      <p>Выберите месяц, введите текущие показания счётчиков. Приложение сохранит их локально, найдёт предыдущий месяц и посчитает расход как разницу между текущими и предыдущими показаниями.</p>
    </section>

    <div class="layout">
      <section class="card">
        <div class="eyebrow">Ввод данных</div>
        <h2 class="section-title">Параметры расчёта</h2>
        <p class="section-note">Сначала выберите месяц, затем введите текущие показания счётчиков. Тарифы предзаполнены и заблокированы.</p>
        {error_block}
        {info_block}
        <form method="post" id="calc-form">
          <div class="grid">
            <div>
              <label for="calculation_year">Год расчёта</label>
              <select id="calculation_year" name="calculation_year">
                {_render_year_options(_value(form_data, "calculation_year"))}
              </select>
            </div>
            <div>
              <label for="calculation_month">Месяц расчёта</label>
              <select id="calculation_month" name="calculation_month">
                {_render_select_options(MONTH_OPTIONS, _value(form_data, "calculation_month"))}
              </select>
            </div>
            <div>
              <label for="cold_water">Холодная вода</label>
              <input id="cold_water" name="cold_water" type="number" step="0.01" min="0" value="{_value(form_data, "cold_water")}" />
            </div>
            <div>
              <label for="hot_water">Горячая вода</label>
              <input id="hot_water" name="hot_water" type="number" step="0.01" min="0" value="{_value(form_data, "hot_water")}" />
            </div>
            <div>
              <label for="electricity_t1">Т1</label>
              <input id="electricity_t1" name="electricity_t1" type="number" step="0.01" min="0" value="{_value(form_data, "electricity_t1")}" />
            </div>
            <div>
              <label for="electricity_t2">Т2</label>
              <input id="electricity_t2" name="electricity_t2" type="number" step="0.01" min="0" value="{_value(form_data, "electricity_t2")}" />
            </div>
            <div>
              <label for="electricity_t3">Т3</label>
              <input id="electricity_t3" name="electricity_t3" type="number" step="0.01" min="0" value="{_value(form_data, "electricity_t3")}" />
            </div>
            <div class="tariff-header">
              <h3>Тарифы</h3>
              <div class="tariff-actions">
                <button type="button" id="collapse-tariffs" class="tariff-toggle tariff-collapse-toggle">Развернуть тарифы</button>
                <button type="button" id="toggle-tariffs" class="tariff-toggle">Изменить тарифы</button>
              </div>
            </div>
            <div class="tariff-section collapsed">
              <label for="cold_water_tariff">Тариф холодной воды</label>
              <input id="cold_water_tariff" class="tariff-input readonly-input" name="cold_water_tariff" type="number" step="0.01" min="0" readonly value="{_value(form_data, "cold_water_tariff")}" />
            </div>
            <div class="tariff-section collapsed">
              <label for="hot_water_tariff">Тариф горячей воды</label>
              <input id="hot_water_tariff" class="tariff-input readonly-input" name="hot_water_tariff" type="number" step="0.01" min="0" readonly value="{_value(form_data, "hot_water_tariff")}" />
            </div>
            <div class="tariff-section collapsed">
              <label for="wastewater_tariff">Тариф водоотведения</label>
              <input id="wastewater_tariff" class="tariff-input readonly-input" name="wastewater_tariff" type="number" step="0.01" min="0" readonly value="{_value(form_data, "wastewater_tariff")}" />
            </div>
            <div class="tariff-section collapsed">
              <label for="electricity_t1_tariff">Тариф электроэнергии 1</label>
              <input id="electricity_t1_tariff" class="tariff-input readonly-input" name="electricity_t1_tariff" type="number" step="0.01" min="0" readonly value="{_value(form_data, "electricity_t1_tariff")}" />
            </div>
            <div class="tariff-section collapsed">
              <label for="electricity_t2_tariff">Тариф электроэнергии 2</label>
              <input id="electricity_t2_tariff" class="tariff-input readonly-input" name="electricity_t2_tariff" type="number" step="0.01" min="0" readonly value="{_value(form_data, "electricity_t2_tariff")}" />
            </div>
            <div class="full tariff-section collapsed">
              <label for="electricity_t3_tariff">Тариф электроэнергии 3</label>
              <input id="electricity_t3_tariff" class="tariff-input readonly-input" name="electricity_t3_tariff" type="number" step="0.01" min="0" readonly value="{_value(form_data, "electricity_t3_tariff")}" />
            </div>
          </div>
          <div class="actions">
            <button type="submit">Сохранить и рассчитать</button>
          </div>
        </form>
      </section>

      <aside>
        {_render_summary(result, previous_month)}
        {_render_delta(result)}
        <div class="formula-note">
          Формулы сейчас такие:<br />
          Вода = расход холодной воды * тариф холодной воды + расход горячей воды * тариф горячей воды + (расход холодной воды + расход горячей воды) * тариф водоотведения.<br />
          Электричество = сумма по трём тарифным зонам.<br />
          Расход = текущий месяц - предыдущий месяц.
        </div>
      </aside>
    </div>
  </div>
  <script>
    const toggleButton = document.getElementById("toggle-tariffs");
    const collapseButton = document.getElementById("collapse-tariffs");
    const tariffInputs = document.querySelectorAll(".tariff-input");
    const tariffSections = document.querySelectorAll(".tariff-section");
    const calculationYear = document.getElementById("calculation_year");
    const calculationMonth = document.getElementById("calculation_month");
    let tariffsEditable = false;
    let tariffsCollapsed = true;

    toggleButton.addEventListener("click", function () {{
      tariffsEditable = !tariffsEditable;
      tariffInputs.forEach(function (input) {{
        input.readOnly = !tariffsEditable;
        input.classList.toggle("readonly-input", !tariffsEditable);
      }});
      toggleButton.textContent = tariffsEditable ? "Заблокировать тарифы" : "Изменить тарифы";
    }});

    collapseButton.addEventListener("click", function () {{
      tariffsCollapsed = !tariffsCollapsed;
      tariffSections.forEach(function (section) {{
        section.classList.toggle("collapsed", tariffsCollapsed);
      }});
      collapseButton.textContent = tariffsCollapsed ? "Развернуть тарифы" : "Свернуть тарифы";
    }});

    function reloadMonthData() {{
      const params = new URLSearchParams();
      params.set("calculation_year", calculationYear.value);
      params.set("calculation_month", calculationMonth.value);
      window.location.search = params.toString();
    }}

    calculationYear.addEventListener("change", reloadMonthData);
    calculationMonth.addEventListener("change", reloadMonthData);
  </script>
</body>
</html>
"""


def application(environ, start_response):
    form_data: dict[str, str] | None = dict(DEFAULT_FORM_VALUES)
    result: CalculationResult | None = None
    error_message = ""
    info_message = ""
    previous_month: str | None = None

    if environ.get("REQUEST_METHOD") == "GET":
        query_string = environ.get("QUERY_STRING", "")
        parsed_query = parse_qs(query_string)
        query_data = {key: values[0] for key, values in parsed_query.items()}

        if "calculation_year" in query_data and "calculation_month" in query_data:
            try:
                month_key = _parse_month_key(query_data)
                form_data = _build_form_data_for_month(month_key)
                if get_month_readings(month_key) is not None:
                    info_message = f"Загружены сохранённые показания за {month_key}."
            except ValueError as error:
                error_message = str(error)

    if environ.get("REQUEST_METHOD") == "POST":
        content_length = int(environ.get("CONTENT_LENGTH", "0") or "0")
        raw_body = environ["wsgi.input"].read(content_length).decode(ENCODING)
        parsed = parse_qs(raw_body)
        form_data = {key: values[0] for key, values in parsed.items()}

        try:
            month_key = _parse_month_key(form_data)
            readings = _build_readings(form_data)
            tariffs = _build_tariffs(form_data)
            previous_month, previous_readings = get_previous_month_readings(month_key)

            save_month_readings(month_key, readings)

            if previous_readings is None:
                form_data = _build_form_data_for_month(month_key, form_data)
                info_message = (
                    f"Показания за {month_key} сохранены. Для расчёта нужны данные за "
                    f"предыдущий месяц: {previous_month}."
                )
            else:
                result = calculate_totals(
                    CalculationInputs(
                        current_readings=readings,
                        previous_readings=previous_readings,
                        tariffs=tariffs,
                    )
                )
                form_data = _build_form_data_for_month(month_key, form_data)
                info_message = f"Показания за {month_key} сохранены."
        except ValueError as error:
            error_message = str(error)

    html = _render_html(
        form_data=form_data,
        result=result,
        error_message=error_message,
        info_message=info_message,
        previous_month=previous_month,
    )
    start_response("200 OK", [("Content-Type", f"text/html; charset={ENCODING}")])
    return [html.encode(ENCODING)]


def main() -> None:
    print(f"Откройте в браузере: http://{HOST}:{PORT}")
    with make_server(HOST, PORT, application) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
