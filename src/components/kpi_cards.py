"""Consistent formatting and rendering for KPI cards."""

from collections.abc import Sequence

import streamlit as st


def format_count(value: int | float | None) -> str:
    return "Not available" if value is None else f"{value:,.0f}"


def format_number(value: int | float | None, decimals: int = 1) -> str:
    return "Not available" if value is None else f"{value:,.{decimals}f}"


def format_percentage(value: int | float | None, decimals: int = 1) -> str:
    return "Not available" if value is None else f"{value:.{decimals}f}%"


def render_kpi_cards(
    metrics: Sequence[tuple[str, str]], columns_per_row: int = 4
) -> None:
    with st.container(key="dashboard-kpi-grid"):
        for offset in range(0, len(metrics), columns_per_row):
            row = metrics[offset : offset + columns_per_row]
            columns = st.columns(columns_per_row)
            for column, (label, value) in zip(columns, row):
                with column:
                    with st.container(border=True):
                        st.metric(label=label, value=value)