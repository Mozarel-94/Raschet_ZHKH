"""Local web interface for utility calculation and monthly analytics."""

from __future__ import annotations

import io
import zipfile
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server
from xml.sax.saxutils import escape as xml_escape

from calculator import CalculationInputs, CalculationResult, MeterReadings, Tariffs, calculate_totals
from history_analytics import (
    build_history_analytics,
    build_month_comparisons,
    build_month_formulas,
    build_month_trends,
    format_month_label,
    month_status,
)
from storage import (
    DEFAULT_TARIFFS,
    MonthlyRecord,
    get_effective_tariffs_for_month,
    get_month_record,
    get_previous_month_readings,
    list_history_records,
    save_month_record,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HOST = "127.0.0.1"
PORT = 8000
ENCODING = "utf-8"
PDF_FONT_NAME = "ReceiptFont"
PDF_FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\arial.ttf"),
    Path(r"C:\Windows\Fonts\tahoma.ttf"),
    Path(r"C:\Windows\Fonts\verdana.ttf"),
    Path(r"C:\Windows\Fonts\times.ttf"),
]

FIELD_LABELS = {
    "calculation_year": "Год расчёта",
    "calculation_month": "Месяц расчёта",
    "cold_water": "Холодная вода",
    "hot_water": "Горячая вода",
    "electricity_t1": "T1",
    "electricity_t2": "T2",
    "electricity_t3": "T3",
    "cold_water_tariff": "Тариф холодной воды",
    "hot_water_tariff": "Тариф горячей воды",
    "wastewater_tariff": "Тариф водоотведения",
    "electricity_t1_tariff": "Тариф электроэнергии T1",
    "electricity_t2_tariff": "Тариф электроэнергии T2",
    "electricity_t3_tariff": "Тариф электроэнергии T3",
}

DEFAULT_FORM_VALUES = {
    "calculation_year": str(max(date.today().year, 2026)),
    "calculation_month": f"{date.today().month:02d}" if date.today().year >= 2026 else "01",
    "cold_water": "",
    "hot_water": "",
    "electricity_t1": "",
    "electricity_t2": "",
    "electricity_t3": "",
    "cold_water_tariff": f"{DEFAULT_TARIFFS.cold_water:.2f}",
    "hot_water_tariff": f"{DEFAULT_TARIFFS.hot_water:.2f}",
    "wastewater_tariff": f"{DEFAULT_TARIFFS.wastewater:.2f}",
    "electricity_t1_tariff": f"{DEFAULT_TARIFFS.electricity_t1:.2f}",
    "electricity_t2_tariff": f"{DEFAULT_TARIFFS.electricity_t2:.2f}",
    "electricity_t3_tariff": f"{DEFAULT_TARIFFS.electricity_t3:.2f}",
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
        raise ValueError(f"Поле '{FIELD_LABELS[field_name]}' не может быть отрицательным.")

    return value


def _parse_int(form_data: dict[str, str], field_name: str) -> int:
    raw_value = form_data.get(field_name, "").strip()
    if not raw_value:
        raise ValueError(f"Поле '{FIELD_LABELS[field_name]}' не может быть пустым.")

    if any(symbol in raw_value for symbol in (".", ",")):
        raise ValueError(f"Поле '{FIELD_LABELS[field_name]}' должно быть целым числом.")

    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"Поле '{FIELD_LABELS[field_name]}' должно быть целым числом.") from error

    if value < 0:
        raise ValueError(f"Поле '{FIELD_LABELS[field_name]}' не может быть отрицательным.")

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
        cold_water=float(_parse_int(form_data, "cold_water")),
        hot_water=float(_parse_int(form_data, "hot_water")),
        electricity_t1=float(_parse_int(form_data, "electricity_t1")),
        electricity_t2=float(_parse_int(form_data, "electricity_t2")),
        electricity_t3=float(_parse_int(form_data, "electricity_t3")),
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


def _money(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f} руб."


def _number(value: float | None, unit: str = "") -> str:
    if value is None:
        return "—"
    suffix = f" {unit}" if unit else ""
    return f"{value:.2f}{suffix}"


def _format_trend(value: float | None) -> str:
    if value is None:
        return "Сравнение недоступно"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f} руб."


def _find_pdf_font_path() -> Path | None:
    for candidate in PDF_FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _ensure_pdf_font_registered() -> str:
    font_path = _find_pdf_font_path()
    if font_path is None:
        raise RuntimeError("Не найден кириллический шрифт для генерации PDF. Проверьте папку C:\\Windows\\Fonts.")

    try:
        pdfmetrics.getFont(PDF_FONT_NAME)
    except KeyError:
        pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, str(font_path)))

    return PDF_FONT_NAME


def _status_class(status: str) -> str:
    return "status-calculated" if status == "Рассчитан" else "status-pending"


def _build_form_data_for_month(month_key: str, existing_form_data: dict[str, str] | None = None) -> dict[str, str]:
    year_value, month_value = month_key.split("-")
    form_data = dict(DEFAULT_FORM_VALUES)
    form_data["calculation_year"] = year_value
    form_data["calculation_month"] = month_value
    effective_tariffs = get_effective_tariffs_for_month(month_key)
    form_data = _apply_tariffs_to_form_data(form_data, effective_tariffs)

    if existing_form_data:
        for key, value in existing_form_data.items():
            if key in form_data:
                form_data[key] = value

    saved_record = get_month_record(month_key)
    if saved_record is not None:
        form_data["cold_water"] = str(int(saved_record.readings.cold_water))
        form_data["hot_water"] = str(int(saved_record.readings.hot_water))
        form_data["electricity_t1"] = str(int(saved_record.readings.electricity_t1))
        form_data["electricity_t2"] = str(int(saved_record.readings.electricity_t2))
        form_data["electricity_t3"] = str(int(saved_record.readings.electricity_t3))
        form_data = _apply_tariffs_to_form_data(form_data, saved_record.tariffs)

    return form_data


def _apply_tariffs_to_form_data(form_data: dict[str, str], tariffs: Tariffs) -> dict[str, str]:
    next_form_data = dict(form_data)
    next_form_data["cold_water_tariff"] = f"{tariffs.cold_water:.2f}"
    next_form_data["hot_water_tariff"] = f"{tariffs.hot_water:.2f}"
    next_form_data["wastewater_tariff"] = f"{tariffs.wastewater:.2f}"
    next_form_data["electricity_t1_tariff"] = f"{tariffs.electricity_t1:.2f}"
    next_form_data["electricity_t2_tariff"] = f"{tariffs.electricity_t2:.2f}"
    next_form_data["electricity_t3_tariff"] = f"{tariffs.electricity_t3:.2f}"
    return next_form_data


def _history_export_rows(records: list[MonthlyRecord]) -> list[list[str]]:
    rows = [
        [
            "month_key",
            "status",
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
            "updated_at",
        ]
    ]

    for record in records:
        rows.append(
            [
                record.month_key,
                month_status(record),
                str(int(record.readings.cold_water)),
                str(int(record.readings.hot_water)),
                str(int(record.readings.electricity_t1)),
                str(int(record.readings.electricity_t2)),
                str(int(record.readings.electricity_t3)),
                f"{record.tariffs.cold_water:.2f}",
                f"{record.tariffs.hot_water:.2f}",
                f"{record.tariffs.wastewater:.2f}",
                f"{record.tariffs.electricity_t1:.2f}",
                f"{record.tariffs.electricity_t2:.2f}",
                f"{record.tariffs.electricity_t3:.2f}",
                "" if record.delta is None else f"{record.delta.cold_water:.2f}",
                "" if record.delta is None else f"{record.delta.hot_water:.2f}",
                "" if record.delta is None else f"{record.delta.electricity_t1:.2f}",
                "" if record.delta is None else f"{record.delta.electricity_t2:.2f}",
                "" if record.delta is None else f"{record.delta.electricity_t3:.2f}",
                "" if record.water_bill is None else f"{record.water_bill:.2f}",
                "" if record.electricity_bill is None else f"{record.electricity_bill:.2f}",
                "" if record.total_bill is None else f"{record.total_bill:.2f}",
                record.updated_at,
            ]
        )

    return rows


def _xlsx_cell(cell_ref: str, value: str) -> str:
    return f'<c r="{cell_ref}" t="inlineStr"><is><t>{xml_escape(value)}</t></is></c>'


def _column_name(index: int) -> str:
    name = ""
    current = index
    while current >= 0:
        current, remainder = divmod(current, 26)
        name = chr(65 + remainder) + name
        current -= 1
    return name


def _build_xlsx_export(records: list[MonthlyRecord]) -> bytes:
    rows = _history_export_rows(records)
    sheet_rows: list[str] = []

    for row_index, row in enumerate(rows, start=1):
        cells = "".join(_xlsx_cell(f"{_column_name(column_index)}{row_index}", value) for column_index, value in enumerate(row))
        sheet_rows.append(f'<row r="{row_index}">{cells}</row>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        "</worksheet>"
    )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="History" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )

    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
        "</Relationships>"
    )

    root_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )

    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        "</Types>"
    )

    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        "</styleSheet>"
    )

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", root_rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        archive.writestr("xl/styles.xml", styles_xml)

    return output.getvalue()


def _receipt_value(value: float | None, unit: str = "") -> str:
    return _number(value, unit) if unit else (f"{value:.2f}" if value is not None else "—")


def _build_receipt_pdf(record: MonthlyRecord) -> bytes:
    font_name = _ensure_pdf_font_registered()
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    margin = 28
    left = margin
    right = page_width - margin
    content_width = right - left
    y = page_height - margin
    status = month_status(record)
    formulas = build_month_formulas(record)
    delta = record.delta

    def draw_paragraph(
        text: str,
        x: float,
        top_y: float,
        width: float,
        font_size: int = 10,
        color=colors.HexColor("#173042"),
        line_gap: int = 2,
    ) -> float:
        pdf.setFont(font_name, font_size)
        pdf.setFillColor(color)
        lines = simpleSplit(text, font_name, font_size, width)
        current_y = top_y
        for line in lines:
            pdf.drawString(x, current_y, line)
            current_y -= font_size + line_gap
        return current_y

    def draw_box(x: float, top_y: float, width: float, height: float, fill_color, stroke_color, radius: int = 12) -> float:
        box_bottom = top_y - height
        pdf.setFillColor(fill_color)
        pdf.setStrokeColor(stroke_color)
        pdf.roundRect(x, box_bottom, width, height, radius, fill=1, stroke=1)
        return box_bottom

    def draw_info_section(
        title: str,
        rows: list[tuple[str, str]],
        x: float,
        top_y: float,
        width: float,
        note: str | None = None,
    ) -> float:
        note_lines = len(simpleSplit(note, font_name, 8, width - 20)) if note else 0
        height = 28 + len(rows) * 14 + note_lines * 10 + 12
        box_bottom = draw_box(x, top_y, width, height, colors.white, colors.HexColor("#d5e1ea"))

        current_y = top_y - 16
        pdf.setFont(font_name, 11)
        pdf.setFillColor(colors.HexColor("#0f5f7a"))
        pdf.drawString(x + 10, current_y, title)
        current_y -= 14

        for label, value in rows:
            pdf.setFont(font_name, 8)
            pdf.setFillColor(colors.HexColor("#526474"))
            pdf.drawString(x + 10, current_y, label)
            text_width = pdf.stringWidth(value, font_name, 9)
            pdf.setFont(font_name, 9)
            pdf.setFillColor(colors.HexColor("#173042"))
            pdf.drawString(x + width - 10 - text_width, current_y, value)
            current_y -= 14

        if note:
            current_y -= 1
            draw_paragraph(
                note,
                x + 10,
                current_y,
                width - 20,
                font_size=8,
                color=colors.HexColor("#526474"),
                line_gap=1,
            )

        return box_bottom

    def draw_totals_section(rows: list[tuple[str, str]]) -> None:
        nonlocal y
        height = 92
        box_bottom = draw_box(left, y, content_width, height, colors.HexColor("#0b4256"), colors.HexColor("#0b4256"), radius=16)

        current_y = y - 18
        pdf.setFont(font_name, 13)
        pdf.setFillColor(colors.white)
        pdf.drawString(left + 14, current_y, "Итоги")
        current_y -= 18

        for index, (label, value) in enumerate(rows):
            label_font = 9 if index < len(rows) - 1 else 10
            value_font = 10 if index < len(rows) - 1 else 15
            pdf.setFont(font_name, label_font)
            pdf.drawString(left + 14, current_y, label)
            text_width = pdf.stringWidth(value, font_name, value_font)
            pdf.setFont(font_name, value_font)
            pdf.drawString(right - 14 - text_width, current_y, value)
            current_y -= 18 if index < len(rows) - 1 else 20

        y = box_bottom - 10

    def draw_formula_section(title: str, lines: list[str], top_y: float) -> float:
        height = 26 + len(lines) * 10 + 10
        box_bottom = draw_box(left, top_y, content_width, height, colors.HexColor("#f8fbfd"), colors.HexColor("#d5e1ea"))

        current_y = top_y - 15
        pdf.setFont(font_name, 11)
        pdf.setFillColor(colors.HexColor("#0f5f7a"))
        pdf.drawString(left + 10, current_y, title)
        current_y -= 13
        for line in lines:
            current_y = draw_paragraph(line, left + 10, current_y, content_width - 20, font_size=8, line_gap=1)

        return box_bottom

    pdf.setTitle(f"Квитанция {format_month_label(record.month_key)}")
    pdf.setAuthor("Raschet_ZHKH")

    pdf.setFont(font_name, 17)
    pdf.setFillColor(colors.HexColor("#0b4256"))
    pdf.drawString(left, y, "Квитанция / Отчёт за месяц")
    y -= 22
    y = draw_paragraph(format_month_label(record.month_key), left, y, content_width, font_size=12, line_gap=1)
    y -= 4
    y = draw_paragraph(
        f"Статус: {status}    Сформировано: {date.today().strftime('%d.%m.%Y')}",
        left,
        y,
        content_width,
        font_size=8,
        color=colors.HexColor("#526474"),
        line_gap=1,
    )
    y -= 8

    draw_totals_section(
        [
            ("Счёт за воду", _money(record.water_bill)),
            ("Счёт за электричество", _money(record.electricity_bill)),
            ("Общий платёж", _money(record.total_bill)),
        ],
    )

    column_gap = 10
    column_width = (content_width - column_gap) / 2
    top_columns_y = y
    left_bottom = draw_info_section(
        "Показания",
        [
            ("Холодная вода", f"{record.readings.cold_water:.0f}"),
            ("Горячая вода", f"{record.readings.hot_water:.0f}"),
            ("Электроэнергия T1", f"{record.readings.electricity_t1:.0f}"),
            ("Электроэнергия T2", f"{record.readings.electricity_t2:.0f}"),
            ("Электроэнергия T3", f"{record.readings.electricity_t3:.0f}"),
        ],
        left,
        top_columns_y,
        column_width,
    )
    right_bottom = draw_info_section(
        "Расход",
        [
            ("Холодная вода", _number(delta.cold_water if delta else None, "м3")),
            ("Горячая вода", _number(delta.hot_water if delta else None, "м3")),
            ("Электроэнергия T1", _number(delta.electricity_t1 if delta else None, "кВт")),
            ("Электроэнергия T2", _number(delta.electricity_t2 if delta else None, "кВт")),
            ("Электроэнергия T3", _number(delta.electricity_t3 if delta else None, "кВт")),
        ],
        left + column_width + column_gap,
        top_columns_y,
        column_width,
        note="Расчёт недоступен: отсутствует предыдущий месяц или полный набор данных." if delta is None else None,
    )
    y = min(left_bottom, right_bottom) - 10

    pdf.setFont(font_name, 12)
    pdf.setFillColor(colors.HexColor("#0b4256"))
    pdf.drawString(left, y, "Формулы")
    y -= 10

    if formulas is None:
        draw_paragraph(
            "Расчёт недоступен: отсутствует предыдущий месяц или полный набор данных.",
            left,
            y,
            content_width,
            font_size=9,
            color=colors.HexColor("#526474"),
            line_gap=1,
        )
    else:
        water_lines = [
            str(formulas["water"]["formula"]),
            *[
                f'{part["label"]}: {part["expression"]} = {_money(part["value"])}'
                for part in formulas["water"]["parts"]
            ],
            f'Итого: {_money(formulas["water"]["total"])}',
        ]
        electricity_lines = [
            str(formulas["electricity"]["formula"]),
            *[
                f'{part["label"]}: {part["expression"]} = {_money(part["value"])}'
                for part in formulas["electricity"]["parts"]
            ],
            f'Итого: {_money(formulas["electricity"]["total"])}',
        ]
        water_bottom = draw_formula_section("Вода", water_lines, y)
        electricity_bottom = draw_formula_section("Электричество", electricity_lines, water_bottom - 8)
        y = electricity_bottom

    pdf.save()
    return buffer.getvalue()


def _render_select_options(options: list[tuple[str, str]], selected_value: str) -> str:
    return "".join(
        f'<option value="{escape(value)}"{" selected" if value == selected_value else ""}>{escape(label)}</option>'
        for value, label in options
    )


def _render_year_options(selected_value: str) -> str:
    return "".join(
        f'<option value="{escape(year)}"{" selected" if year == selected_value else ""}>{escape(year)}</option>'
        for year in YEAR_OPTIONS
    )


def _render_summary(result: CalculationResult | None, previous_month: str | None) -> str:
    if result is None:
        return """
        <div class="card empty-card">
          <div class="eyebrow">Итог</div>
          <h2>Результат расчёта</h2>
          <p>Заполните текущие показания и сохраните расчёт. Если прошлый месяц уже есть, локальная версия сразу посчитает расход и сумму.</p>
        </div>
        """

    previous_text = (
        f'<p class="muted">Сравнение с прошлым месяцем: <strong>{escape(previous_month)}</strong></p>'
        if previous_month
        else ""
    )

    return f"""
    <div class="card">
      <div class="eyebrow">Итог</div>
      <h2>Результаты</h2>
      {previous_text}
      <div class="result-row"><span>Счёт за воду</span><strong>{escape(_money(result.water_bill))}</strong></div>
      <div class="result-row"><span>Счёт за электричество</span><strong>{escape(_money(result.electricity_bill))}</strong></div>
      <div class="result-row total"><span>Общий платёж</span><strong>{escape(_money(result.total_bill))}</strong></div>
    </div>
    """


def _render_delta(result: CalculationResult | None) -> str:
    if result is None:
        return ""

    return f"""
    <div class="card">
      <div class="eyebrow">Расход</div>
      <div class="detail-list">
        <div><span>Холодная вода</span><strong>{escape(_number(result.delta.cold_water, "м3"))}</strong></div>
        <div><span>Горячая вода</span><strong>{escape(_number(result.delta.hot_water, "м3"))}</strong></div>
        <div><span>T1</span><strong>{escape(_number(result.delta.electricity_t1, "кВт"))}</strong></div>
        <div><span>T2</span><strong>{escape(_number(result.delta.electricity_t2, "кВт"))}</strong></div>
        <div><span>T3</span><strong>{escape(_number(result.delta.electricity_t3, "кВт"))}</strong></div>
      </div>
    </div>
    """


def _render_formula_note() -> str:
    return """
    <div class="formula-note">
      Вода = холодная вода × тариф + горячая вода × тариф + (холодная + горячая) × водоотведение.<br />
      Электричество = T1 × тариф T1 + T2 × тариф T2 + T3 × тариф T3.<br />
      Расход = текущий месяц − предыдущий месяц.
    </div>
    """


def _render_chart(series: list[dict[str, object]], unit: str) -> str:
    if not series:
        return '<div class="empty-inline">Недостаточно данных для графика.</div>'

    max_value = max(float(item["value"]) for item in series if item.get("value") is not None)
    bars = []
    for item in series:
        value = float(item["value"])
        height = 8 if max_value == 0 else max((value / max_value) * 100, 8)
        bars.append(
            f"""
            <div class="chart-bar-item">
              <div class="chart-bar-value">{escape(_number(value, unit))}</div>
              <div class="chart-bar-track"><div class="chart-bar-fill" style="height: {height:.2f}%"></div></div>
              <div class="chart-bar-label">{escape(str(item["label"]))}</div>
            </div>
            """
        )
    return f'<div class="chart-bars">{"".join(bars)}</div>'


def _render_history_sidebar(records: list[MonthlyRecord], selected_month_key: str | None) -> str:
    if not records:
        return '<div class="card empty-card">История пока пустая. Сохраните хотя бы один месяц.</div>'

    trends = build_month_trends(records)
    items = []
    for record in records:
        active_class = " active" if record.month_key == selected_month_key else ""
        status = month_status(record)
        status_class = _status_class(status)
        trend = _format_trend(trends.get(record.month_key))
        items.append(
            f"""
            <a class="history-link{active_class}" href="/history?month={escape(record.month_key)}">
              <div class="history-link-main">
                <span>{escape(format_month_label(record.month_key))}</span>
                <span class="history-meta">
                  <span class="status-badge {status_class}">{escape(status)}</span>
                  <span class="trend-chip">{escape(trend)}</span>
                </span>
              </div>
              <strong>{escape(_money(record.total_bill))}</strong>
            </a>
            """
        )
    return f'<div class="card history-list">{"".join(items)}</div>'


def _render_comparison_cards(comparisons: dict[str, object] | None) -> str:
    if comparisons is None:
        return '<div class="empty-inline">Нет данных для сравнений.</div>'

    prev_month = comparisons.get("previous_month")
    prev_year = comparisons.get("previous_year")
    prev_month_label = prev_month["label"] if isinstance(prev_month, dict) else "Нет данных"
    prev_year_label = prev_year["label"] if isinstance(prev_year, dict) else "Нет данных"

    return f"""
    <div class="stat-grid">
      <article class="stat-card">
        <span class="stat-label">К прошлому месяцу</span>
        <strong>{escape(_money(comparisons.get("previous_month_total_diff")))}</strong>
        <span class="muted">{escape(str(prev_month_label))}</span>
      </article>
      <article class="stat-card">
        <span class="stat-label">К прошлому году</span>
        <strong>{escape(_money(comparisons.get("previous_year_total_diff")))}</strong>
        <span class="muted">{escape(str(prev_year_label))}</span>
      </article>
    </div>
    """


def _render_formula_sections(formulas: dict[str, object] | None) -> str:
    if formulas is None:
        return '<div class="card empty-card">Для этого месяца ещё нет полного расчёта: отсутствуют данные предыдущего периода.</div>'

    sections = []
    for title, group_key in (("Вода", "water"), ("Электричество", "electricity")):
        group = formulas[group_key]
        parts_html = "".join(
            f"""
            <div class="formula-part">
              <span>{escape(str(part["label"]))}</span>
              <span>{escape(str(part["expression"]))}</span>
              <strong>{escape(_money(part["value"]))}</strong>
            </div>
            """
            for part in group["parts"]
        )
        sections.append(
            f"""
            <section class="card">
              <h3>{title}</h3>
              <p class="muted">{escape(str(group["formula"]))}</p>
              <div class="detail-list formula-parts">{parts_html}</div>
              <div class="result-row total"><span>Итого</span><strong>{escape(_money(group["total"]))}</strong></div>
            </section>
            """
        )
    return "".join(sections)


def _render_history_detail(selected_record: MonthlyRecord | None, all_records: list[MonthlyRecord]) -> str:
    if selected_record is None:
        return '<div class="card empty-card">Выберите месяц из списка слева.</div>'

    comparisons = build_month_comparisons(all_records, selected_record.month_key)
    formulas = build_month_formulas(selected_record)
    delta = selected_record.delta
    status = month_status(selected_record)
    status_class = _status_class(status)
    trend = _format_trend(build_month_trends(all_records).get(selected_record.month_key))

    return f"""
    <section class="card">
      <div class="eyebrow">Период</div>
      <h2>{escape(format_month_label(selected_record.month_key))}</h2>
      <div class="detail-meta">
        <span class="status-badge {status_class}">{escape(status)}</span>
        <span class="trend-chip">Тренд: {escape(trend)}</span>
      </div>
      <div class="result-row total"><span>Общий платёж</span><strong>{escape(_money(selected_record.total_bill))}</strong></div>
    </section>

    {_render_comparison_cards(comparisons)}

    <section class="detail-grid">
      <article class="card">
        <h3>Показания</h3>
        <div class="detail-list">
          <div><span>Холодная вода</span><strong>{escape(_number(selected_record.readings.cold_water))}</strong></div>
          <div><span>Горячая вода</span><strong>{escape(_number(selected_record.readings.hot_water))}</strong></div>
          <div><span>T1</span><strong>{escape(_number(selected_record.readings.electricity_t1))}</strong></div>
          <div><span>T2</span><strong>{escape(_number(selected_record.readings.electricity_t2))}</strong></div>
          <div><span>T3</span><strong>{escape(_number(selected_record.readings.electricity_t3))}</strong></div>
        </div>
      </article>

      <article class="card">
        <h3>Тарифы месяца</h3>
        <div class="detail-list">
          <div><span>Холодная вода</span><strong>{escape(_money(selected_record.tariffs.cold_water))}</strong></div>
          <div><span>Горячая вода</span><strong>{escape(_money(selected_record.tariffs.hot_water))}</strong></div>
          <div><span>Водоотведение</span><strong>{escape(_money(selected_record.tariffs.wastewater))}</strong></div>
          <div><span>T1</span><strong>{escape(_money(selected_record.tariffs.electricity_t1))}</strong></div>
          <div><span>T2</span><strong>{escape(_money(selected_record.tariffs.electricity_t2))}</strong></div>
          <div><span>T3</span><strong>{escape(_money(selected_record.tariffs.electricity_t3))}</strong></div>
        </div>
      </article>

      <article class="card">
        <h3>Расход</h3>
        <div class="detail-list">
          <div><span>Холодная вода</span><strong>{escape(_number(delta.cold_water if delta else None, "м3"))}</strong></div>
          <div><span>Горячая вода</span><strong>{escape(_number(delta.hot_water if delta else None, "м3"))}</strong></div>
          <div><span>T1</span><strong>{escape(_number(delta.electricity_t1 if delta else None, "кВт"))}</strong></div>
          <div><span>T2</span><strong>{escape(_number(delta.electricity_t2 if delta else None, "кВт"))}</strong></div>
          <div><span>T3</span><strong>{escape(_number(delta.electricity_t3 if delta else None, "кВт"))}</strong></div>
        </div>
      </article>
    </section>

    {_render_formula_sections(formulas)}
    """


def _render_base(title: str, body: str, active_page: str) -> str:
    calc_active = " active" if active_page == "calculator" else ""
    history_active = " active" if active_page == "history" else ""
    return f"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #e7eef5;
      --surface: rgba(255,255,255,0.96);
      --surface-strong: #ffffff;
      --line: #b8c9d8;
      --text: #13202b;
      --muted: #42576a;
      --accent: #0f5f7a;
      --accent-soft: #d6e8f2;
      --accent-strong: #0b4256;
      --shadow: 0 18px 45px rgba(19, 32, 43, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(188, 212, 230, 0.55), transparent 24%),
        radial-gradient(circle at bottom right, rgba(171, 198, 220, 0.5), transparent 22%),
        linear-gradient(180deg, #eef4f8 0%, #dde8f1 100%);
    }}
    .page {{ max-width: 1280px; margin: 0 auto; padding: 28px 18px 56px; }}
    .hero {{
      padding: 28px;
      border-radius: 28px;
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(223, 236, 245, 0.96));
      border: 1px solid rgba(184, 201, 216, 0.9);
      box-shadow: var(--shadow);
    }}
    .hero h1 {{ margin: 8px 0 10px; font-size: clamp(2rem, 4vw, 3.3rem); }}
    .hero p {{ margin: 0; max-width: 900px; color: var(--muted); line-height: 1.6; }}
    .topbar {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }}
    .nav-link {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      padding: 11px 18px;
      text-decoration: none;
      color: var(--accent-strong);
      background: rgba(255,255,255,0.6);
      border: 1px solid var(--line);
      font-weight: 600;
    }}
    .nav-link.active {{ background: var(--accent); color: white; border-color: var(--accent); }}
    .export-link {{
      background: var(--accent);
      color: #ffffff;
      border-color: var(--accent);
      box-shadow: 0 10px 24px rgba(15, 95, 122, 0.22);
    }}
    .receipt-link {{
      background: #0b4256;
      color: #ffffff;
      border-color: #0b4256;
      box-shadow: 0 10px 24px rgba(11, 66, 86, 0.26);
    }}
    .layout, .history-layout {{ display: grid; gap: 22px; margin-top: 22px; align-items: start; }}
    .layout {{ grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr); }}
    .history-layout {{ grid-template-columns: minmax(240px, 0.34fr) minmax(0, 1fr); }}
    .card {{
      background: var(--surface);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(184, 201, 216, 0.85);
      border-radius: 24px;
      padding: 22px;
      box-shadow: var(--shadow);
    }}
    .empty-card, .empty-inline {{ color: var(--muted); }}
    .eyebrow {{ color: var(--accent); text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.76rem; font-weight: 700; }}
    .section-title {{ margin: 8px 0; font-size: 1.9rem; }}
    .section-note, .muted {{ color: var(--muted); }}
    .grid, .stat-grid, .detail-grid {{ display: grid; gap: 14px; }}
    .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .stat-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); margin-bottom: 18px; }}
    .detail-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 18px 0; }}
    label {{ display: block; margin-bottom: 8px; color: var(--muted); font-weight: 600; }}
    input, select {{
      width: 100%;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: var(--surface-strong);
      padding: 14px 15px;
      font-size: 1rem;
      color: var(--text);
    }}
    input:focus, select:focus {{ outline: 2px solid rgba(15,118,110,0.18); border-color: var(--accent); }}
    .period-field {{
      padding: 16px;
      border-radius: 20px;
      background: linear-gradient(180deg, #d9e8f2, #cfe1ee);
      border: 1px solid #aac2d3;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.65);
    }}
    .period-field label {{
      color: var(--accent-strong);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 0.78rem;
    }}
    .period-field select {{
      background: rgba(255,255,255,0.96);
      border: 1px solid #95b2c5;
      font-weight: 700;
      color: var(--accent-strong);
    }}
    .readonly-input {{ background: #f0ece6; color: #7b6d5f; }}
    .full {{ grid-column: 1 / -1; }}
    .actions {{ margin-top: 22px; display: flex; gap: 12px; flex-wrap: wrap; }}
    .inline-status {{ margin: 8px 0 14px; }}
    button {{
      border: 0;
      border-radius: 999px;
      padding: 14px 22px;
      background: var(--accent);
      color: white;
      font-weight: 700;
      cursor: pointer;
    }}
    .ghost-button {{ background: rgba(255,255,255,0.6); color: var(--accent-strong); border: 1px solid var(--line); }}
    .message {{ border-radius: 18px; padding: 14px 16px; margin-bottom: 14px; }}
    .message.error {{ background: #fce7e7; color: #8a1c1c; }}
    .message.info {{ background: #dbeaf3; color: var(--accent-strong); }}
    .result-row, .detail-list div, .formula-part, .history-link {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid rgba(106, 88, 72, 0.12);
    }}
    .result-row.total {{ border-bottom: 0; font-size: 1.08rem; }}
    .detail-list div:last-child, .formula-part:last-child {{ border-bottom: 0; }}
    .formula-note {{ margin-top: 18px; padding: 18px; border-radius: 20px; background: #dceaf2; color: #28495e; line-height: 1.7; }}
    .history-list {{ padding-top: 10px; display: grid; gap: 10px; }}
    .history-link {{
      text-decoration: none;
      color: inherit;
      padding: 16px 18px;
      border: 1px solid rgba(184, 201, 216, 0.85);
      border-radius: 20px;
      background: rgba(255,255,255,0.62);
      transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }}
    .history-link:hover {{
      background: rgba(232, 242, 248, 0.95);
      border-color: rgba(15, 95, 122, 0.28);
      transform: translateY(-1px);
    }}
    .history-link.active {{
      color: var(--accent-strong);
      background: linear-gradient(135deg, rgba(221, 238, 247, 0.98), rgba(207, 229, 241, 0.98));
      border-color: rgba(15, 95, 122, 0.55);
      box-shadow: 0 12px 24px rgba(15, 95, 122, 0.14);
    }}
    .history-link-main {{ display: grid; gap: 8px; }}
    .history-meta, .detail-meta {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
    .detail-meta {{ margin: 10px 0 8px; }}
    .status-badge, .trend-chip {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 0.8rem;
      font-weight: 700;
    }}
    .status-calculated {{ background: #d9efe2; color: #245b41; }}
    .status-pending {{ background: #e8edf2; color: #526575; }}
    .trend-chip {{ background: #e1edf5; color: #365b72; }}
    .stat-card {{
      background: var(--surface);
      border-radius: 20px;
      padding: 18px;
      border: 1px solid rgba(184, 201, 216, 0.85);
      box-shadow: var(--shadow);
    }}
    .stat-card strong {{ display: block; margin-top: 8px; font-size: 1.3rem; }}
    .stat-label {{ color: var(--muted); font-size: 0.9rem; }}
    .chart-panel {{ margin-bottom: 18px; }}
    .chart-bars {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: 14px; align-items: end; min-height: 240px; }}
    .chart-bar-item {{ display: grid; gap: 8px; align-items: end; }}
    .chart-bar-track {{
      height: 160px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(15,95,122,0.10), rgba(15,95,122,0.22));
      display: flex;
      align-items: end;
      overflow: hidden;
    }}
    .chart-bar-fill {{ width: 100%; border-radius: 18px; background: linear-gradient(180deg, #2f89aa, #0f5f7a); }}
    .chart-bar-value, .chart-bar-label {{ text-align: center; font-size: 0.86rem; color: var(--muted); }}
    .tariff-header {{
      grid-column: 1 / -1;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-top: 6px;
    }}
    .tariff-actions {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .tariff-section.collapsed {{ display: none; }}
    @media (max-width: 980px) {{
      .layout, .history-layout, .stat-grid, .detail-grid {{ grid-template-columns: 1fr; }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <div class="eyebrow">Local ZHKH</div>
      <h1>Локальный расчёт ЖКХ с историей расходов</h1>
      <p>Эта версия не зависит от Netlify: данные сохраняются в локальный JSON-файл, а экран истории и аналитики работает прямо на вашей машине.</p>
      <div class="topbar">
        <a href="/" class="nav-link{calc_active}">Калькулятор</a>
        <a href="/history" class="nav-link{history_active}">История и аналитика</a>
      </div>
    </section>
    {body}
  </div>
</body>
</html>
"""


def _render_calculator_page(
    form_data: dict[str, str] | None = None,
    result: CalculationResult | None = None,
    error_message: str = "",
    info_message: str = "",
    previous_month: str | None = None,
    selected_month_key: str | None = None,
) -> str:
    error_block = f'<div class="message error">{escape(error_message)}</div>' if error_message else ""
    info_block = f'<div class="message info">{escape(info_message)}</div>' if info_message else ""
    selected_history_link = f'/history?month={escape(selected_month_key)}' if selected_month_key else "/history"
    current_record = get_month_record(selected_month_key) if selected_month_key else None
    current_status = month_status(current_record) if current_record is not None else None
    current_status_block = (
        f'<div class="inline-status"><span class="status-badge {_status_class(current_status)}">{escape(current_status)}</span></div>'
        if current_status
        else ""
    )

    body = f"""
    <div class="layout">
      <section class="card">
        <div class="eyebrow">Ввод данных</div>
        <h2 class="section-title">Параметры расчёта</h2>
        <p class="section-note">Выберите месяц, внесите текущие показания и при необходимости скорректируйте тарифы для конкретного периода.</p>
        {current_status_block}
        {error_block}
        {info_block}
        <form method="post">
          <div class="grid">
            <div class="period-field">
              <label for="calculation_year">Год расчёта</label>
              <select id="calculation_year" name="calculation_year">{_render_year_options(_value(form_data, "calculation_year"))}</select>
            </div>
            <div class="period-field">
              <label for="calculation_month">Месяц расчёта</label>
              <select id="calculation_month" name="calculation_month">{_render_select_options(MONTH_OPTIONS, _value(form_data, "calculation_month"))}</select>
            </div>
            <div>
              <label for="cold_water">Холодная вода</label>
              <input id="cold_water" name="cold_water" type="number" step="1" min="0" inputmode="numeric" value="{_value(form_data, "cold_water")}" />
            </div>
            <div>
              <label for="hot_water">Горячая вода</label>
              <input id="hot_water" name="hot_water" type="number" step="1" min="0" inputmode="numeric" value="{_value(form_data, "hot_water")}" />
            </div>
            <div>
              <label for="electricity_t1">T1</label>
              <input id="electricity_t1" name="electricity_t1" type="number" step="1" min="0" inputmode="numeric" value="{_value(form_data, "electricity_t1")}" />
            </div>
            <div>
              <label for="electricity_t2">T2</label>
              <input id="electricity_t2" name="electricity_t2" type="number" step="1" min="0" inputmode="numeric" value="{_value(form_data, "electricity_t2")}" />
            </div>
            <div>
              <label for="electricity_t3">T3</label>
              <input id="electricity_t3" name="electricity_t3" type="number" step="1" min="0" inputmode="numeric" value="{_value(form_data, "electricity_t3")}" />
            </div>

            <div class="tariff-header">
              <h3>Тарифы месяца</h3>
              <div class="tariff-actions">
                <button type="button" class="ghost-button" id="toggle-tariffs">Редактировать тарифы</button>
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
              <label for="electricity_t1_tariff">Тариф электроэнергии T1</label>
              <input id="electricity_t1_tariff" class="tariff-input readonly-input" name="electricity_t1_tariff" type="number" step="0.01" min="0" readonly value="{_value(form_data, "electricity_t1_tariff")}" />
            </div>
            <div class="tariff-section collapsed">
              <label for="electricity_t2_tariff">Тариф электроэнергии T2</label>
              <input id="electricity_t2_tariff" class="tariff-input readonly-input" name="electricity_t2_tariff" type="number" step="0.01" min="0" readonly value="{_value(form_data, "electricity_t2_tariff")}" />
            </div>
            <div class="tariff-section collapsed">
              <label for="electricity_t3_tariff">Тариф электроэнергии T3</label>
              <input id="electricity_t3_tariff" class="tariff-input readonly-input" name="electricity_t3_tariff" type="number" step="0.01" min="0" readonly value="{_value(form_data, "electricity_t3_tariff")}" />
            </div>
          </div>
          <div class="actions">
            <button type="submit">Сохранить и рассчитать</button>
            <a href="{selected_history_link}" class="nav-link">Открыть историю</a>
          </div>
        </form>
      </section>

      <aside>
        {_render_summary(result, previous_month)}
        {_render_delta(result)}
        {_render_formula_note()}
      </aside>
    </div>
    <script>
      const toggleButton = document.getElementById("toggle-tariffs");
      const tariffInputs = document.querySelectorAll(".tariff-input");
      const tariffSections = document.querySelectorAll(".tariff-section");
      const calculationYear = document.getElementById("calculation_year");
      const calculationMonth = document.getElementById("calculation_month");
      let tariffsEditable = false;
      let tariffsCollapsed = true;

      toggleButton.addEventListener("click", function () {{
        tariffsCollapsed = !tariffsCollapsed;
        tariffsEditable = !tariffsCollapsed;
        tariffSections.forEach(function (section) {{
          section.classList.toggle("collapsed", tariffsCollapsed);
        }});
        tariffInputs.forEach(function (input) {{
          input.readOnly = !tariffsEditable;
          input.classList.toggle("readonly-input", !tariffsEditable);
        }});
        toggleButton.textContent = tariffsCollapsed ? "Редактировать тарифы" : "Скрыть тарифы";
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
    """
    return _render_base("Локальный расчёт ЖКХ", body, "calculator")


def _render_history_page(selected_month_key: str | None = None) -> str:
    records = list_history_records()
    analytics = build_history_analytics(records)

    if selected_month_key is None and records:
        selected_month_key = records[0].month_key

    selected_record = next((record for record in records if record.month_key == selected_month_key), None)
    averages = analytics["averages"]
    most_expensive = analytics["most_expensive_month"]
    avg_water_total = (
        (averages["cold_water"] or 0) + (averages["hot_water"] or 0)
        if averages["cold_water"] is not None and averages["hot_water"] is not None
        else None
    )

    body = f"""
    <div class="history-layout">
      <aside>
        {_render_history_sidebar(records, selected_month_key)}
      </aside>
      <section>
        <div class="actions">
          {'<a href="/history/receipt.pdf?month=' + escape(selected_month_key) + '" class="nav-link receipt-link">Скачать квитанцию PDF</a>' if selected_month_key else '<span class="nav-link">Выберите месяц для квитанции</span>'}
          <a href="/history/export.xlsx" class="nav-link export-link">Экспорт XLSX</a>
        </div>
        <div class="stat-grid">
          <article class="stat-card">
            <span class="stat-label">Средний платёж</span>
            <strong>{escape(_money(averages["total_bill"]))}</strong>
          </article>
          <article class="stat-card">
            <span class="stat-label">Средний счёт за воду</span>
            <strong>{escape(_money(averages["water_bill"]))}</strong>
          </article>
          <article class="stat-card">
            <span class="stat-label">Средний счёт за электричество</span>
            <strong>{escape(_money(averages["electricity_bill"]))}</strong>
          </article>
          <article class="stat-card">
            <span class="stat-label">Средний расход воды</span>
            <strong>{escape(_number(avg_water_total, "м3"))}</strong>
          </article>
          <article class="stat-card">
            <span class="stat-label">Средний расход электричества</span>
            <strong>{escape(_number(averages["electricity_total"], "кВт"))}</strong>
          </article>
          <article class="stat-card">
            <span class="stat-label">Самый дорогой месяц</span>
            <strong>{escape(f"{most_expensive['label']} • {_money(most_expensive['total_bill'])}" if most_expensive else "—")}</strong>
          </article>
        </div>

        <section class="card chart-panel">
          <div class="eyebrow">График</div>
          <h2>Общий платёж по месяцам</h2>
          {_render_chart(analytics["total_payment_chart"], "руб.")}
        </section>

        <section class="card chart-panel">
          <div class="eyebrow">График</div>
          <h2>Расход воды</h2>
          {_render_chart(analytics["water_consumption_chart"], "м3")}
        </section>

        <section class="card chart-panel">
          <div class="eyebrow">График</div>
          <h2>Расход электричества</h2>
          {_render_chart(analytics["electricity_consumption_chart"], "кВт")}
        </section>

        {_render_history_detail(selected_record, records)}
      </section>
    </div>
    """
    return _render_base("История и аналитика ЖКХ", body, "history")


def _parse_query(environ: dict[str, object]) -> dict[str, str]:
    query_string = str(environ.get("QUERY_STRING", ""))
    parsed_query = parse_qs(query_string)
    return {key: values[0] for key, values in parsed_query.items()}


def _saved_result(record: MonthlyRecord | None) -> CalculationResult | None:
    if record is None or record.delta is None or record.total_bill is None:
        return None

    return CalculationResult(
        water_bill=record.water_bill or 0.0,
        electricity_bill=record.electricity_bill or 0.0,
        total_bill=record.total_bill or 0.0,
        delta=record.delta,
    )


def _handle_calculator(environ: dict[str, object]) -> str:
    form_data: dict[str, str] | None = dict(DEFAULT_FORM_VALUES)
    result: CalculationResult | None = None
    error_message = ""
    info_message = ""
    previous_month: str | None = None
    selected_month_key: str | None = None

    if environ.get("REQUEST_METHOD") == "GET":
        query_data = _parse_query(environ)
        if "calculation_year" in query_data and "calculation_month" in query_data:
            try:
                selected_month_key = _parse_month_key(query_data)
                form_data = _build_form_data_for_month(selected_month_key)
                saved_record = get_month_record(selected_month_key)
                if saved_record is not None:
                    info_message = f"Загружены локально сохранённые данные за {selected_month_key}."
                    result = _saved_result(saved_record)
            except ValueError as error:
                error_message = str(error)

    if environ.get("REQUEST_METHOD") == "POST":
        content_length = int(str(environ.get("CONTENT_LENGTH", "0")) or "0")
        raw_body = environ["wsgi.input"].read(content_length).decode(ENCODING)
        parsed = parse_qs(raw_body)
        form_data = {key: values[0] for key, values in parsed.items()}

        try:
            selected_month_key = _parse_month_key(form_data)
            readings = _build_readings(form_data)
            tariffs = _build_tariffs(form_data)
            previous_month, previous_readings = get_previous_month_readings(selected_month_key)

            if previous_readings is None:
                save_month_record(selected_month_key, readings, tariffs, None)
                form_data = _build_form_data_for_month(selected_month_key, form_data)
                saved_record = get_month_record(selected_month_key)
                info_message = (
                    f"Показания за {selected_month_key} сохранены локально. "
                    f"Статус: {month_status(saved_record) if saved_record else 'Сохранён без расчёта'}. "
                    f"Для полного расчёта нужен предыдущий месяц: {previous_month}."
                )
            else:
                result = calculate_totals(
                    CalculationInputs(
                        current_readings=readings,
                        previous_readings=previous_readings,
                        tariffs=tariffs,
                    )
                )
                saved_record = save_month_record(selected_month_key, readings, tariffs, result)
                form_data = _build_form_data_for_month(selected_month_key, form_data)
                info_message = (
                    f"Показания и расчёт за {selected_month_key} сохранены локально. "
                    f"Статус: {month_status(saved_record)}."
                )
        except ValueError as error:
            error_message = str(error)

    return _render_calculator_page(
        form_data=form_data,
        result=result,
        error_message=error_message,
        info_message=info_message,
        previous_month=previous_month,
        selected_month_key=selected_month_key,
    )


def _handle_history_export() -> tuple[str, list[tuple[str, str]], bytes]:
    payload = _build_xlsx_export(list_history_records())
    headers = [
        (
            "Content-Type",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        ("Content-Disposition", 'attachment; filename="zhkh-history.xlsx"'),
    ]
    return "200 OK", headers, payload


def _handle_receipt_export(query: dict[str, str]) -> tuple[str, list[tuple[str, str]], bytes]:
    month_key = query.get("month", "").strip()
    if not month_key:
        return (
            "400 Bad Request",
            [("Content-Type", f"text/plain; charset={ENCODING}")],
            "Параметр month обязателен для генерации квитанции.".encode(ENCODING),
        )

    record = get_month_record(month_key)
    if record is None:
        return (
            "404 Not Found",
            [("Content-Type", f"text/plain; charset={ENCODING}")],
            f"Месяц {month_key} не найден в локальной истории.".encode(ENCODING),
        )

    try:
        payload = _build_receipt_pdf(record)
    except Exception as error:
        return (
            "500 Internal Server Error",
            [("Content-Type", f"text/plain; charset={ENCODING}")],
            f"Не удалось сформировать PDF-квитанцию: {error}".encode(ENCODING),
        )

    headers = [
        ("Content-Type", "application/pdf"),
        ("Content-Disposition", f'attachment; filename="zhkh-receipt-{month_key}.pdf"'),
    ]
    return "200 OK", headers, payload


def application(environ, start_response):
    path = str(environ.get("PATH_INFO", "/") or "/")

    if path == "/history/export.xlsx":
        status, headers, body = _handle_history_export()
        start_response(status, headers)
        return [body]

    if path == "/history/receipt.pdf":
        query = _parse_query(environ)
        status, headers, body = _handle_receipt_export(query)
        start_response(status, headers)
        return [body]

    if path == "/history":
        query = _parse_query(environ)
        html = _render_history_page(query.get("month"))
    else:
        html = _handle_calculator(environ)

    start_response("200 OK", [("Content-Type", f"text/html; charset={ENCODING}")])
    return [html.encode(ENCODING)]


def main() -> None:
    print(f"Откройте в браузере: http://{HOST}:{PORT}")
    with make_server(HOST, PORT, application) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
