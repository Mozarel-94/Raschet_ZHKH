"""Local storage for monthly meter readings."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from calculator import MeterReadings

DATA_FILE = Path(__file__).with_name("meter_history.json")


def _month_to_date(month_key: str) -> date:
    year, month = month_key.split("-")
    return date(int(year), int(month), 1)


def _previous_month_key(month_key: str) -> str:
    month_date = _month_to_date(month_key)
    if month_date.month == 1:
        return f"{month_date.year - 1}-12"
    return f"{month_date.year}-{month_date.month - 1:02d}"


def load_history() -> dict[str, dict[str, float]]:
    if not DATA_FILE.exists():
        return {}

    with DATA_FILE.open("r", encoding="utf-8") as file:
        loaded = json.load(file)

    if not isinstance(loaded, dict):
        return {}

    return loaded


def save_month_readings(month_key: str, readings: MeterReadings) -> None:
    history = load_history()
    history[month_key] = asdict(readings)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)


def get_month_readings(month_key: str) -> MeterReadings | None:
    month_data = load_history().get(month_key)
    if month_data is None:
        return None

    return MeterReadings(
        cold_water=float(month_data["cold_water"]),
        hot_water=float(month_data["hot_water"]),
        electricity_t1=float(month_data["electricity_t1"]),
        electricity_t2=float(month_data["electricity_t2"]),
        electricity_t3=float(month_data["electricity_t3"]),
    )


def get_previous_month_readings(month_key: str) -> tuple[str, MeterReadings | None]:
    previous_key = _previous_month_key(month_key)
    return previous_key, get_month_readings(previous_key)
