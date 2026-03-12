"""Streamlit UI for коммунальные платежи MVP."""

from __future__ import annotations

import streamlit as st

from config import SHEET_CONFIG
from sheets_service import (
    MeterReadings,
    SheetsConnectionError,
    SheetsReadError,
    SheetsService,
    SheetsWriteError,
    readings_to_dict,
)


def main() -> None:
    st.set_page_config(page_title="Расчет коммунальных платежей", page_icon="🏠")
    st.title("Расчет коммунальных платежей")

    st.subheader("Ввод показаний")
    cold_water = st.number_input("Холодная вода", min_value=0.0, step=0.1, format="%.2f")
    hot_water = st.number_input("Горячая вода", min_value=0.0, step=0.1, format="%.2f")
    electricity_day = st.number_input(
        "Электроэнергия (день)", min_value=0.0, step=0.1, format="%.2f"
    )
    electricity_night = st.number_input(
        "Электроэнергия (ночь)", min_value=0.0, step=0.1, format="%.2f"
    )

    if st.button("Рассчитать", type="primary"):
        readings = MeterReadings(
            cold_water=cold_water,
            hot_water=hot_water,
            electricity_day=electricity_day,
            electricity_night=electricity_night,
        )

        try:
            with st.spinner("Расчет..."):
                service = SheetsService.from_streamlit_secrets(
                    spreadsheet_id_default=SHEET_CONFIG.spreadsheet_id
                )
                result = service.calculate(readings)
        except (SheetsConnectionError, SheetsWriteError, SheetsReadError) as error:
            st.error(f"Ошибка: {error}")
            return
        except Exception as error:  # noqa: BLE001
            st.error(f"Неожиданная ошибка: {error}")
            return

        st.success("Расчет успешно выполнен")
        st.subheader("Результаты")

        st.write("**Показания:**")
        for key, value in readings_to_dict(readings).items():
            st.write(f"- {key}: {value}")

        st.write(f"**Вода:** {result.water_total}")
        st.write(f"**Электричество:** {result.electricity_total}")
        st.write(f"**Итого:** {result.grand_total}")


if __name__ == "__main__":
    main()
