"""Local storage for monthly meter readings and analytics."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from calculator import CalculationResult, ConsumptionDelta, MeterReadings, Tariffs

DATA_FILE = Path(__file__).with_name("meter_history.json")


@dataclass(frozen=True)
class MonthlyRecord:
    month_key: str
    readings: MeterReadings
    tariffs: Tariffs
    delta: ConsumptionDelta | None
    water_bill: float | None
    electricity_bill: float | None
    total_bill: float | None
    updated_at: str


DEFAULT_TARIFFS = Tariffs(
    cold_water=65.77,
    hot_water=312.50,
    wastewater=51.62,
    electricity_t1=10.23,
    electricity_t2=3.71,
    electricity_t3=7.16,
)


def _month_to_date(month_key: str) -> date:
    year, month = month_key.split("-")
    return date(int(year), int(month), 1)


def _previous_month_key(month_key: str) -> str:
    month_date = _month_to_date(month_key)
    if month_date.month == 1:
        return f"{month_date.year - 1}-12"
    return f"{month_date.year}-{month_date.month - 1:02d}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_readings(data: dict[str, object]) -> MeterReadings:
    return MeterReadings(
        cold_water=float(data["cold_water"]),
        hot_water=float(data["hot_water"]),
        electricity_t1=float(data["electricity_t1"]),
        electricity_t2=float(data["electricity_t2"]),
        electricity_t3=float(data["electricity_t3"]),
    )


def _parse_tariffs(data: dict[str, object] | None) -> Tariffs:
    if not data:
        return DEFAULT_TARIFFS

    return Tariffs(
        cold_water=float(data.get("cold_water", DEFAULT_TARIFFS.cold_water)),
        hot_water=float(data.get("hot_water", DEFAULT_TARIFFS.hot_water)),
        wastewater=float(data.get("wastewater", DEFAULT_TARIFFS.wastewater)),
        electricity_t1=float(data.get("electricity_t1", DEFAULT_TARIFFS.electricity_t1)),
        electricity_t2=float(data.get("electricity_t2", DEFAULT_TARIFFS.electricity_t2)),
        electricity_t3=float(data.get("electricity_t3", DEFAULT_TARIFFS.electricity_t3)),
    )


def _parse_delta(data: dict[str, object] | None) -> ConsumptionDelta | None:
    if not data:
        return None

    return ConsumptionDelta(
        cold_water=float(data["cold_water"]),
        hot_water=float(data["hot_water"]),
        electricity_t1=float(data["electricity_t1"]),
        electricity_t2=float(data["electricity_t2"]),
        electricity_t3=float(data["electricity_t3"]),
    )


def _normalize_record(month_key: str, data: dict[str, object]) -> MonthlyRecord:
    if "readings" in data:
        readings_source = data["readings"]
        if not isinstance(readings_source, dict):
            raise ValueError(f"Некорректные показания в записи {month_key}.")

        tariffs_source = data.get("tariffs")
        delta_source = data.get("delta")
        return MonthlyRecord(
            month_key=month_key,
            readings=_parse_readings(readings_source),
            tariffs=_parse_tariffs(tariffs_source if isinstance(tariffs_source, dict) else None),
            delta=_parse_delta(delta_source if isinstance(delta_source, dict) else None),
            water_bill=float(data["water_bill"]) if data.get("water_bill") is not None else None,
            electricity_bill=float(data["electricity_bill"]) if data.get("electricity_bill") is not None else None,
            total_bill=float(data["total_bill"]) if data.get("total_bill") is not None else None,
            updated_at=str(data.get("updated_at") or _now_iso()),
        )

    return MonthlyRecord(
        month_key=month_key,
        readings=_parse_readings(data),
        tariffs=DEFAULT_TARIFFS,
        delta=None,
        water_bill=None,
        electricity_bill=None,
        total_bill=None,
        updated_at=_now_iso(),
    )


def _record_to_json(record: MonthlyRecord) -> dict[str, object]:
    payload: dict[str, object] = {
        "readings": asdict(record.readings),
        "tariffs": asdict(record.tariffs),
        "delta": asdict(record.delta) if record.delta is not None else None,
        "water_bill": record.water_bill,
        "electricity_bill": record.electricity_bill,
        "total_bill": record.total_bill,
        "updated_at": record.updated_at,
    }
    return payload


def load_history() -> dict[str, dict[str, object]]:
    if not DATA_FILE.exists():
        return {}

    with DATA_FILE.open("r", encoding="utf-8") as file:
        loaded = json.load(file)

    if not isinstance(loaded, dict):
        return {}

    return loaded


def save_month_record(
    month_key: str,
    readings: MeterReadings,
    tariffs: Tariffs = DEFAULT_TARIFFS,
    result: CalculationResult | None = None,
) -> MonthlyRecord:
    record = MonthlyRecord(
        month_key=month_key,
        readings=readings,
        tariffs=tariffs,
        delta=result.delta if result is not None else None,
        water_bill=result.water_bill if result is not None else None,
        electricity_bill=result.electricity_bill if result is not None else None,
        total_bill=result.total_bill if result is not None else None,
        updated_at=_now_iso(),
    )

    history = load_history()
    history[month_key] = _record_to_json(record)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)

    return record


def save_month_readings(month_key: str, readings: MeterReadings) -> None:
    save_month_record(month_key, readings)


def get_month_record(month_key: str) -> MonthlyRecord | None:
    month_data = load_history().get(month_key)
    if month_data is None:
        return None
    if not isinstance(month_data, dict):
        return None

    return _normalize_record(month_key, month_data)


def get_month_readings(month_key: str) -> MeterReadings | None:
    record = get_month_record(month_key)
    return record.readings if record is not None else None


def get_previous_month_readings(month_key: str) -> tuple[str, MeterReadings | None]:
    previous_key = _previous_month_key(month_key)
    record = get_month_record(previous_key)
    return previous_key, (record.readings if record is not None else None)


def list_history_records() -> list[MonthlyRecord]:
    records: list[MonthlyRecord] = []
    for month_key, raw_record in load_history().items():
        if isinstance(raw_record, dict):
            records.append(_normalize_record(month_key, raw_record))

    return sorted(records, key=lambda record: record.month_key, reverse=True)


def get_effective_tariffs_for_month(month_key: str) -> Tariffs:
    current_record = get_month_record(month_key)
    if current_record is not None:
        return current_record.tariffs

    older_records = [record for record in list_history_records() if record.month_key < month_key]
    if older_records:
        return older_records[0].tariffs

    return DEFAULT_TARIFFS
