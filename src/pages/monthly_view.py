"""Monthly and time-of-arrival dashboard section."""

import pandas as pd
import streamlit as st

from src.analytics.trends import (
    daily_patient_visits,
    hourly_arrival_distribution,
    monthly_patient_visits,
    weekday_arrival_distribution,
)
from src.components.charts import bar_chart, line_chart, render_chart, stacked_bar_chart


def render_monthly_view(dataframe: pd.DataFrame) -> None:
    st.subheader("Patient volume and admissions")
    if dataframe.empty:
        st.info("No visits match the selected filters.")
        return

    monthly = monthly_patient_visits(dataframe)
    if monthly.empty:
        st.info("No valid admission dates are available for this selection.")
        return

    volume_column, admission_column = st.columns(2)
    with volume_column:
        figure = line_chart(
            monthly,
            x="Month",
            y="Patient Visits",
            title="Monthly Patient Visits",
            x_title="Admission month",
            y_title="Visits",
        )
        figure.update_xaxes(tickformat="%b %Y")
        render_chart(figure, "monthly-visits")
    with admission_column:
        render_chart(
            stacked_bar_chart(
                monthly,
                x="Month",
                y=["Admitted Patients", "Non-admitted Patients"],
                title="Monthly Admitted vs Non-admitted Patients",
                x_title="Admission month",
                y_title="Visits",
            ),
            "monthly-admissions",
        )

    rate = monthly.dropna(subset=["Admission Rate (%)"])
    st.subheader("Admission rate")
    if rate.empty:
        st.info("Admission status is not recorded for the selected visits.")
    else:
        figure = line_chart(
            rate,
            x="Month",
            y="Admission Rate (%)",
            title="Monthly Admission Rate",
            x_title="Admission month",
            y_title="Admission rate (%)",
            color="#4E7C59",
        )
        figure.update_yaxes(ticksuffix="%")
        figure.update_xaxes(tickformat="%b %Y")
        render_chart(figure, "monthly-admission-rate")

    st.subheader("Arrival patterns")
    daily = daily_patient_visits(dataframe)
    hourly = hourly_arrival_distribution(dataframe)
    weekdays = weekday_arrival_distribution(dataframe)
    daily_column, hourly_column = st.columns(2)
    with daily_column:
        render_chart(
            line_chart(
                daily,
                x="Date",
                y="Patient Visits",
                title="Daily Patient Visits",
                x_title="Admission date",
                y_title="Visits",
                color="#6E9FC5",
            ),
            "daily-visits",
        )
    with hourly_column:
        render_chart(
            bar_chart(
                hourly,
                x="Hour",
                y="Patient Visits",
                title="Patient Arrivals by Hour",
                x_title="Hour of day",
                y_title="Visits",
            ),
            "hourly-arrivals",
        )
    render_chart(
        bar_chart(
            weekdays,
            x="Weekday",
            y="Patient Visits",
            title="Patient Arrivals by Weekday",
            x_title="Day of week",
            y_title="Visits",
            color="#4E7C59",
        ),
        "weekday-arrivals",
    )