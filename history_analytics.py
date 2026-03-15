"""History analytics helpers for the local application."""

from __future__ import annotations

from storage import MonthlyRecord


MONTH_NAMES = {
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
}


def round_value(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 2)


def format_month_label(month_key: str) -> str:
    year, month = month_key.split("-")
    return f"{MONTH_NAMES.get(month, month)} {year}"


def get_previous_month_key(month_key: str) -> str:
    year_text, month_text = month_key.split("-")
    year = int(year_text)
    month = int(month_text)
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"


def get_previous_year_month_key(month_key: str) -> str:
    year_text, month_text = month_key.split("-")
    return f"{int(year_text) - 1}-{month_text}"


def _safe_average(values: list[float]) -> float | None:
    if not values:
        return None
    return round_value(sum(values) / len(values))


def _map_chart(records: list[MonthlyRecord], pick_value) -> list[dict[str, object]]:
    chart: list[dict[str, object]] = []
    for record in records:
        value = pick_value(record)
        if value is None:
            continue
        chart.append(
            {
                "month_key": record.month_key,
                "label": format_month_label(record.month_key),
                "value": round_value(value),
            }
        )
    return chart


def _compare_delta(current: MonthlyRecord, other: MonthlyRecord | None) -> dict[str, float | None] | None:
    if current.delta is None or other is None or other.delta is None:
        return None

    return {
        "cold_water": round_value(current.delta.cold_water - other.delta.cold_water),
        "hot_water": round_value(current.delta.hot_water - other.delta.hot_water),
        "electricity_t1": round_value(current.delta.electricity_t1 - other.delta.electricity_t1),
        "electricity_t2": round_value(current.delta.electricity_t2 - other.delta.electricity_t2),
        "electricity_t3": round_value(current.delta.electricity_t3 - other.delta.electricity_t3),
    }


def build_history_analytics(records: list[MonthlyRecord]) -> dict[str, object]:
    complete_records = [record for record in records if record.total_bill is not None and record.delta is not None]
    most_expensive = None
    if complete_records:
        expensive_record = max(complete_records, key=lambda record: record.total_bill or 0)
        most_expensive = {
            "month_key": expensive_record.month_key,
            "label": format_month_label(expensive_record.month_key),
            "total_bill": round_value(expensive_record.total_bill),
        }

    return {
        "total_payment_chart": _map_chart(records, lambda record: record.total_bill),
        "water_consumption_chart": _map_chart(
            records,
            lambda record: None
            if record.delta is None
            else record.delta.cold_water + record.delta.hot_water,
        ),
        "electricity_consumption_chart": _map_chart(
            records,
            lambda record: None
            if record.delta is None
            else record.delta.electricity_t1 + record.delta.electricity_t2 + record.delta.electricity_t3,
        ),
        "averages": {
            "total_bill": _safe_average([record.total_bill for record in complete_records if record.total_bill is not None]),
            "water_bill": _safe_average([record.water_bill for record in complete_records if record.water_bill is not None]),
            "electricity_bill": _safe_average(
                [record.electricity_bill for record in complete_records if record.electricity_bill is not None]
            ),
            "cold_water": _safe_average([record.delta.cold_water for record in complete_records if record.delta is not None]),
            "hot_water": _safe_average([record.delta.hot_water for record in complete_records if record.delta is not None]),
            "electricity_total": _safe_average(
                [
                    record.delta.electricity_t1 + record.delta.electricity_t2 + record.delta.electricity_t3
                    for record in complete_records
                    if record.delta is not None
                ]
            ),
        },
        "most_expensive_month": most_expensive,
    }


def build_month_comparisons(records: list[MonthlyRecord], month_key: str) -> dict[str, object] | None:
    record_map = {record.month_key: record for record in records}
    current = record_map.get(month_key)
    if current is None:
        return None

    previous_month = record_map.get(get_previous_month_key(month_key))
    previous_year = record_map.get(get_previous_year_month_key(month_key))

    return {
        "previous_month": (
            {
                "month_key": previous_month.month_key,
                "label": format_month_label(previous_month.month_key),
                "total_bill": round_value(previous_month.total_bill),
            }
            if previous_month is not None
            else None
        ),
        "previous_year": (
            {
                "month_key": previous_year.month_key,
                "label": format_month_label(previous_year.month_key),
                "total_bill": round_value(previous_year.total_bill),
            }
            if previous_year is not None
            else None
        ),
        "previous_month_total_diff": (
            round_value(current.total_bill - previous_month.total_bill)
            if current.total_bill is not None and previous_month is not None and previous_month.total_bill is not None
            else None
        ),
        "previous_year_total_diff": (
            round_value(current.total_bill - previous_year.total_bill)
            if current.total_bill is not None and previous_year is not None and previous_year.total_bill is not None
            else None
        ),
        "previous_month_delta_diff": _compare_delta(current, previous_month),
        "previous_year_delta_diff": _compare_delta(current, previous_year),
    }


def build_month_formulas(record: MonthlyRecord) -> dict[str, object] | None:
    if record.delta is None:
        return None

    return {
        "water": {
            "formula": "Холодная вода x тариф + Горячая вода x тариф + (Холодная + Горячая) x водоотведение",
            "parts": [
                {
                    "label": "Холодная вода",
                    "expression": f"{record.delta.cold_water:.2f} x {record.tariffs.cold_water:.2f}",
                    "value": round_value(record.delta.cold_water * record.tariffs.cold_water),
                },
                {
                    "label": "Горячая вода",
                    "expression": f"{record.delta.hot_water:.2f} x {record.tariffs.hot_water:.2f}",
                    "value": round_value(record.delta.hot_water * record.tariffs.hot_water),
                },
                {
                    "label": "Водоотведение",
                    "expression": (
                        f"{(record.delta.cold_water + record.delta.hot_water):.2f} x {record.tariffs.wastewater:.2f}"
                    ),
                    "value": round_value((record.delta.cold_water + record.delta.hot_water) * record.tariffs.wastewater),
                },
            ],
            "total": round_value(record.water_bill),
        },
        "electricity": {
            "formula": "T1 x тариф T1 + T2 x тариф T2 + T3 x тариф T3",
            "parts": [
                {
                    "label": "T1",
                    "expression": f"{record.delta.electricity_t1:.2f} x {record.tariffs.electricity_t1:.2f}",
                    "value": round_value(record.delta.electricity_t1 * record.tariffs.electricity_t1),
                },
                {
                    "label": "T2",
                    "expression": f"{record.delta.electricity_t2:.2f} x {record.tariffs.electricity_t2:.2f}",
                    "value": round_value(record.delta.electricity_t2 * record.tariffs.electricity_t2),
                },
                {
                    "label": "T3",
                    "expression": f"{record.delta.electricity_t3:.2f} x {record.tariffs.electricity_t3:.2f}",
                    "value": round_value(record.delta.electricity_t3 * record.tariffs.electricity_t3),
                },
            ],
            "total": round_value(record.electricity_bill),
        },
    }
