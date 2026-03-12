"""Minimal web interface for коммунальные платежи MVP (without external web frameworks)."""

from __future__ import annotations

from html import escape
from typing import Dict, Optional
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from sheets_service import (
    MeterReadings,
    SheetsConnectionError,
    SheetsReadError,
    SheetsService,
    SheetsWriteError,
    readings_to_dict,
)

HOST = "0.0.0.0"
PORT = 8501
ENCODING = "utf-8"


def _to_float(form_data: Dict[str, str], field_name: str) -> float:
    raw_value = form_data.get(field_name, "0").strip()
    if not raw_value:
        return 0.0

    try:
        value = float(raw_value)
    except ValueError as error:
        raise ValueError(f"Поле '{field_name}' должно быть числом") from error

    if value < 0:
        raise ValueError(f"Поле '{field_name}' не может быть отрицательным")

    return value


def _parse_readings(form_data: Dict[str, str]) -> MeterReadings:
    return MeterReadings(
        cold_water=_to_float(form_data, "cold_water"),
        hot_water=_to_float(form_data, "hot_water"),
        electricity_day=_to_float(form_data, "electricity_day"),
        electricity_night=_to_float(form_data, "electricity_night"),
    )


def _render_html(
    readings: Optional[MeterReadings] = None,
    water_total: str = "",
    electricity_total: str = "",
    grand_total: str = "",
    success_message: str = "",
    error_message: str = "",
) -> str:
    readings_map = readings_to_dict(readings) if readings else {}
    default_values = {
        "cold_water": readings.cold_water if readings else 0.0,
        "hot_water": readings.hot_water if readings else 0.0,
        "electricity_day": readings.electricity_day if readings else 0.0,
        "electricity_night": readings.electricity_night if readings else 0.0,
    }

    readings_block = "".join(
        f"<li>{escape(name)}: {value:.2f}</li>" for name, value in readings_map.items()
    )

    return f"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Расчет коммунальных платежей</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem auto; max-width: 720px; padding: 0 1rem; }}
    h1 {{ margin-bottom: 1rem; }}
    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }}
    label {{ display: block; margin-top: 0.8rem; font-weight: 600; }}
    input {{ width: 100%; box-sizing: border-box; padding: 0.5rem; margin-top: 0.35rem; }}
    button {{ margin-top: 1rem; padding: 0.7rem 1rem; background: #2563eb; color: white; border: 0; border-radius: 6px; cursor: pointer; }}
    button:disabled {{ background: #9ca3af; cursor: wait; }}
    .spinner {{ display: none; margin-top: 0.75rem; color: #374151; }}
    .ok {{ color: #166534; background: #dcfce7; padding: 0.75rem; border-radius: 6px; }}
    .error {{ color: #991b1b; background: #fee2e2; padding: 0.75rem; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Расчет коммунальных платежей</h1>

  <div class="card">
    <h2>Ввод показаний</h2>
    <form method="post" id="calc-form">
      <label for="cold_water">Холодная вода</label>
      <input type="number" step="0.01" min="0" id="cold_water" name="cold_water" value="{default_values['cold_water']:.2f}" />

      <label for="hot_water">Горячая вода</label>
      <input type="number" step="0.01" min="0" id="hot_water" name="hot_water" value="{default_values['hot_water']:.2f}" />

      <label for="electricity_day">Электроэнергия (день)</label>
      <input type="number" step="0.01" min="0" id="electricity_day" name="electricity_day" value="{default_values['electricity_day']:.2f}" />

      <label for="electricity_night">Электроэнергия (ночь)</label>
      <input type="number" step="0.01" min="0" id="electricity_night" name="electricity_night" value="{default_values['electricity_night']:.2f}" />

      <button type="submit" id="submit-btn">Рассчитать</button>
      <div id="spinner" class="spinner">Расчет...</div>
    </form>
  </div>

  {f'<div class="ok">{escape(success_message)}</div>' if success_message else ''}
  {f'<div class="error">{escape(error_message)}</div>' if error_message else ''}

  <div class="card">
    <h2>Результаты</h2>
    <h3>Показания</h3>
    <ul>{readings_block}</ul>
    <p><strong>Вода:</strong> {escape(water_total)}</p>
    <p><strong>Электричество:</strong> {escape(electricity_total)}</p>
    <p><strong>Итого:</strong> {escape(grand_total)}</p>
  </div>

  <script>
    const form = document.getElementById('calc-form');
    const button = document.getElementById('submit-btn');
    const spinner = document.getElementById('spinner');
    form.addEventListener('submit', function() {{
      button.disabled = true;
      spinner.style.display = 'block';
    }});
  </script>
</body>
</html>
"""


def application(environ, start_response):
    readings = None
    water_total = ""
    electricity_total = ""
    grand_total = ""
    success_message = ""
    error_message = ""

    if environ["REQUEST_METHOD"] == "POST":
        content_length = int(environ.get("CONTENT_LENGTH", "0") or "0")
        raw_body = environ["wsgi.input"].read(content_length).decode(ENCODING)
        parsed = parse_qs(raw_body)
        form_data = {key: values[0] for key, values in parsed.items()}

        try:
            readings = _parse_readings(form_data)
            service = SheetsService()
            result = service.calculate(readings)

            water_total = result.water_total
            electricity_total = result.electricity_total
            grand_total = result.grand_total
            success_message = "Расчет успешно выполнен"
        except (SheetsConnectionError, SheetsWriteError, SheetsReadError, ValueError) as error:
            error_message = f"Ошибка: {error}"
        except Exception as error:  # noqa: BLE001
            error_message = f"Неожиданная ошибка: {error}"

    html = _render_html(
        readings=readings,
        water_total=water_total,
        electricity_total=electricity_total,
        grand_total=grand_total,
        success_message=success_message,
        error_message=error_message,
    )

    response_headers = [("Content-Type", f"text/html; charset={ENCODING}")]
    start_response("200 OK", response_headers)
    return [html.encode(ENCODING)]


def main() -> None:
    print(f"Запуск приложения: http://{HOST}:{PORT}")
    with make_server(HOST, PORT, application) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
