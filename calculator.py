"""Calculation formulas for utility bills based on meter deltas."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeterReadings:
    cold_water: float
    hot_water: float
    electricity_t1: float
    electricity_t2: float
    electricity_t3: float


@dataclass(frozen=True)
class Tariffs:
    cold_water: float
    hot_water: float
    wastewater: float
    electricity_t1: float
    electricity_t2: float
    electricity_t3: float


@dataclass(frozen=True)
class CalculationInputs:
    current_readings: MeterReadings
    previous_readings: MeterReadings
    tariffs: Tariffs


@dataclass(frozen=True)
class ConsumptionDelta:
    cold_water: float
    hot_water: float
    electricity_t1: float
    electricity_t2: float
    electricity_t3: float


@dataclass(frozen=True)
class CalculationResult:
    water_bill: float
    electricity_bill: float
    total_bill: float
    delta: ConsumptionDelta


def calculate_delta(current: MeterReadings, previous: MeterReadings) -> ConsumptionDelta:
    return ConsumptionDelta(
        cold_water=current.cold_water - previous.cold_water,
        hot_water=current.hot_water - previous.hot_water,
        electricity_t1=current.electricity_t1 - previous.electricity_t1,
        electricity_t2=current.electricity_t2 - previous.electricity_t2,
        electricity_t3=current.electricity_t3 - previous.electricity_t3,
    )


def _validate_delta(delta: ConsumptionDelta) -> None:
    negative_fields = []
    for field_name, value in delta.__dict__.items():
        if value < 0:
            negative_fields.append(field_name)

    if negative_fields:
        raise ValueError(
            "Показания за выбранный месяц меньше предыдущего месяца: "
            + ", ".join(negative_fields)
            + "."
        )


def calculate_water_bill(delta: ConsumptionDelta, tariffs: Tariffs) -> float:
    wastewater_usage = delta.cold_water + delta.hot_water
    return (
        delta.cold_water * tariffs.cold_water
        + delta.hot_water * tariffs.hot_water
        + wastewater_usage * tariffs.wastewater
    )


def calculate_electricity_bill(delta: ConsumptionDelta, tariffs: Tariffs) -> float:
    return (
        delta.electricity_t1 * tariffs.electricity_t1
        + delta.electricity_t2 * tariffs.electricity_t2
        + delta.electricity_t3 * tariffs.electricity_t3
    )


def calculate_totals(inputs: CalculationInputs) -> CalculationResult:
    delta = calculate_delta(inputs.current_readings, inputs.previous_readings)
    _validate_delta(delta)

    water_bill = calculate_water_bill(delta, inputs.tariffs)
    electricity_bill = calculate_electricity_bill(delta, inputs.tariffs)
    total_bill = water_bill + electricity_bill

    return CalculationResult(
        water_bill=water_bill,
        electricity_bill=electricity_bill,
        total_bill=total_bill,
        delta=delta,
    )
