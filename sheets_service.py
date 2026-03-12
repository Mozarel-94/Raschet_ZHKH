"""Google Sheets integration for коммунальные платежи MVP."""

from __future__ import annotations

import atexit
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Dict

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
        service_account_file: str = APP_CONFIG.service_account_file,
        service_account_json: str = APP_CONFIG.service_account_json,
    ) -> None:
        self._service_account_file = service_account_file
        self._service_account_json = service_account_json
        self._temp_credentials_file: str | None = None

    def _cleanup_temp_credentials(self) -> None:
        if self._temp_credentials_file and os.path.exists(self._temp_credentials_file):
            os.remove(self._temp_credentials_file)

    def _resolve_service_account_file(self) -> str:
        if self._service_account_json.strip():
            temp_file = tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".json", delete=False
            )
            temp_file.write(self._service_account_json)
            temp_file.flush()
            temp_file.close()
            self._temp_credentials_file = temp_file.name
            atexit.register(self._cleanup_temp_credentials)
            return temp_file.name

        return self._service_account_file

    def _get_worksheet(self):
        try:
            import gspread
            from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
        except ModuleNotFoundError as error:
            raise SheetsConnectionError(
                "Пакет gspread не установлен. Установите зависимости из requirements.txt."
            ) from error

        service_account_file = self._resolve_service_account_file()

        try:
            client = gspread.service_account(filename=service_account_file)
            spreadsheet = client.open_by_key(SHEET_CONFIG.spreadsheet_id)
            return spreadsheet.worksheet(SHEET_CONFIG.worksheet_name)
        except FileNotFoundError as error:
            raise SheetsConnectionError(
                f"Файл ключа service account не найден: {service_account_file}"
            ) from error
        except SpreadsheetNotFound as error:
            raise SheetsConnectionError(
                "Таблица не найдена. Проверьте spreadsheet_id и доступ service account."
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
        except Exception as error:  # noqa: BLE001
            raise SheetsWriteError(f"Не удалось записать показания: {error}") from error

    def read_totals(self) -> CalculationResult:
        worksheet = self._get_worksheet()

        try:
            water_total = worksheet.acell(SHEET_CONFIG.water_total_cell).value
            electricity_total = worksheet.acell(SHEET_CONFIG.electricity_total_cell).value
            grand_total = worksheet.acell(SHEET_CONFIG.grand_total_cell).value
        except Exception as error:  # noqa: BLE001
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
