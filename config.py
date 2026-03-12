"""Configuration for коммунальные платежи MVP."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SheetConfig:
    """Google Sheets structure configuration."""

    spreadsheet_id: str = "PASTE_YOUR_SPREADSHEET_ID"
    worksheet_name: str = "Расчет"

    cold_water_cell: str = "B2"
    hot_water_cell: str = "B3"
    electricity_day_cell: str = "B4"
    electricity_night_cell: str = "B5"

    water_total_cell: str = "E2"
    electricity_total_cell: str = "E3"
    grand_total_cell: str = "E4"

    formulas_update_wait_seconds: float = 1.5


@dataclass(frozen=True)
class AppConfig:
    """Application-level settings."""

    service_account_file: str = "service_account.json"


SHEET_CONFIG = SheetConfig()
APP_CONFIG = AppConfig()
