"""Google Sheets integration for коммунальные платежи MVP."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound

from config import APP_CONFIG, SHEET_CONFIG


class SheetsServiceError(Exception):
    """Base exception for sheets service errors."""


class SheetsConnectionError(SheetsServiceError):
    """Raised when connection to Google Sheets fails."""


class SheetsWriteError(SheetsServiceError):
    """Raised when writing values fails."""


class SheetsReadError(SheetsServiceError):
    """Raised when reading calculated values fails."""


@dataclass(frozen=True)
class MeterReadings:
    cold_water: float
    hot_water: float
    electricity_day: float
    electricity_night: float


@dataclass(frozen=True)
class CalculationResult:
    water_total: str
    electricity_total: str
    grand_total: str


class SheetsService:
    """Service for writing readings and fetching totals from Google Sheets."""

    def __init__(
        self,
        spreadsheet_id: str,
        service_account_file: Optional[str] = APP_CONFIG.service_account_file,
        service_account_info: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self._spreadsheet_id = spreadsheet_id
        self._service_account_file = service_account_file
        self._service_account_info = dict(service_account_info) if service_account_info else None

    @classmethod
    def from_streamlit_secrets(cls, spreadsheet_id_default: str) -> "SheetsService":
        """Build service using Streamlit secrets when available."""

        try:
            import streamlit as st

            secret_data = st.secrets.get("gcp_service_account")
            spreadsheet_id = st.secrets.get("SPREADSHEET_ID", spreadsheet_id_default)
            if secret_data:
                return cls(spreadsheet_id=spreadsheet_id, service_account_info=secret_data)
            return cls(spreadsheet_id=spreadsheet_id)
        except Exception:
            return cls(spreadsheet_id=spreadsheet_id_default)

    def _create_client(self) -> gspread.Client:
        try:
            if self._service_account_info:
                return gspread.service_account_from_dict(self._service_account_info)
            return gspread.service_account(filename=self._service_account_file)
        except FileNotFoundError as error:
            raise SheetsConnectionError(
                f"Файл ключа service account не найден: {self._service_account_file}"
            ) from error
        except Exception as error:  # noqa: BLE001
            raise SheetsConnectionError(f"Ошибка авторизации в Google Sheets: {error}") from error

    def _get_worksheet(self):
        client = self._create_client()
        try:
            spreadsheet = client.open_by_key(self._spreadsheet_id)
            return spreadsheet.worksheet(SHEET_CONFIG.worksheet_name)
        except SpreadsheetNotFound as error:
            raise SheetsConnectionError(
                "Таблица не найдена. Проверьте SPREADSHEET_ID и доступ service account."
            ) from error
        except WorksheetNotFound as error:
            raise SheetsConnectionError(
                f"Лист '{SHEET_CONFIG.worksheet_name}' не найден."
            ) from error
        except APIError as error:
            raise SheetsConnectionError(
                f"Ошибка API при подключении к Google Sheets: {error}"
            ) from error

    def write_readings(self, readings: MeterReadings) -> None:
        worksheet = self._get_worksheet()
        updates = [
            {"range": SHEET_CONFIG.cold_water_cell, "values": [[readings.cold_water]]},
            {"range": SHEET_CONFIG.hot_water_cell, "values": [[readings.hot_water]]},
            {
                "range": SHEET_CONFIG.electricity_day_cell,
                "values": [[readings.electricity_day]],
            },
            {
                "range": SHEET_CONFIG.electricity_night_cell,
                "values": [[readings.electricity_night]],
            },
        ]

        try:
            worksheet.batch_update(updates)
        except APIError as error:
            raise SheetsWriteError(f"Не удалось записать показания: {error}") from error

    def read_totals(self) -> CalculationResult:
        worksheet = self._get_worksheet()

        try:
            water_total = worksheet.acell(SHEET_CONFIG.water_total_cell).value
            electricity_total = worksheet.acell(SHEET_CONFIG.electricity_total_cell).value
            grand_total = worksheet.acell(SHEET_CONFIG.grand_total_cell).value
        except APIError as error:
            raise SheetsReadError(f"Не удалось прочитать результаты: {error}") from error

        return CalculationResult(
            water_total=water_total or "0",
            electricity_total=electricity_total or "0",
            grand_total=grand_total or "0",
        )

    def calculate(self, readings: MeterReadings) -> CalculationResult:
        self.write_readings(readings)
        time.sleep(SHEET_CONFIG.formulas_update_wait_seconds)
        return self.read_totals()


def readings_to_dict(readings: MeterReadings) -> Dict[str, float]:
    return {
        "Холодная вода": readings.cold_water,
        "Горячая вода": readings.hot_water,
        "Электроэнергия (день)": readings.electricity_day,
        "Электроэнергия (ночь)": readings.electricity_night,
    }
