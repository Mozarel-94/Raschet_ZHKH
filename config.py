"""Configuration for коммунальные платежи MVP."""

from dataclasses import dataclass
import os


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError:
        return default


@dataclass(frozen=True)
class SheetConfig:
    """Google Sheets structure configuration."""

    spreadsheet_id: str = os.getenv("SPREADSHEET_ID", "PASTE_YOUR_SPREADSHEET_ID")
    worksheet_name: str = os.getenv("WORKSHEET_NAME", "Расчет")

    cold_water_cell: str = os.getenv("COLD_WATER_CELL", "B2")
    hot_water_cell: str = os.getenv("HOT_WATER_CELL", "B3")
    electricity_day_cell: str = os.getenv("ELECTRICITY_DAY_CELL", "B4")
    electricity_night_cell: str = os.getenv("ELECTRICITY_NIGHT_CELL", "B5")

    water_total_cell: str = os.getenv("WATER_TOTAL_CELL", "E2")
    electricity_total_cell: str = os.getenv("ELECTRICITY_TOTAL_CELL", "E3")
    grand_total_cell: str = os.getenv("GRAND_TOTAL_CELL", "E4")

    formulas_update_wait_seconds: float = _env_float("FORMULAS_WAIT_SECONDS", 1.5)


@dataclass(frozen=True)
class AppConfig:
    """Application-level settings."""

    service_account_file: str = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")
<<<<<<< codex/deploy-web-service-to-github-server-dxqw8h
    service_account_json: str = os.getenv("SERVICE_ACCOUNT_JSON", "")
=======
>>>>>>> main


SHEET_CONFIG = SheetConfig()
APP_CONFIG = AppConfig()
