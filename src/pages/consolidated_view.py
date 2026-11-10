"""Consolidated operational overview section."""

import pandas as pd
import streamlit as st

from src.analytics.kpis import calculate_overall_kpis
from src.analytics.segments import (
    age_group_distribution,
    department_referral_distribution,
    gender_distribution,
    missing_referral_summary,
    race_distribution,
)
from src.analytics.trends import monthly_patient_visits, waiting_time_distribution
from src.components.charts import bar_chart, donut_chart, line_chart, render_chart, stacked_bar_chart
from src.components.kpi_cards import (
    format_count,
    format_number,
    format_percentage,
    render_kpi_cards,
)


def render_consolidated_view(dataframe: pd.DataFrame) -> None:
    if dataframe.empty:
        st.info("No visits match the selected filters.")
        return

    kpis = calculate_overall_kpis(dataframe)
    render_kpi_cards(
        [
            ("Total Patient Visits", format_count(kpis["total_patient_visits"])),
            ("Admitted Patients", format_count(kpis["admitted_patients"])),
            ("Non-admitted Patients", format_count(kpis["non_admitted_patients"])),
            ("Admission Rate", format_percentage(kpis["admission_rate_percent"])),
            (
                "Average Waiting Time",
                f"{format_number(kpis['average_wait_time_minutes'])} min"
                if kpis["average_wait_time_minutes"] is not None
                else "Not available",
            ),
            (
                "Patients Waiting <=30 Minutes",
                format_percentage(kpis["waiting_30_minutes_or_less_percent"]),
            ),
            ("Average Patient Age", format_number(kpis["average_patient_age"])),
            (
                "Average Satisfaction Score",
                format_number(kpis["average_satisfaction_score"]),
            ),
        ]
    )

    referrals_missing = missing_referral_summary(dataframe)
    satisfaction_missing = kpis["missing_satisfaction_percent"]
    st.info(
        f"Satisfaction responses: {format_count(kpis['satisfaction_response_count'])} "
        f"of {format_count(kpis['total_patient_visits'])} visits; "
        f"{format_percentage(satisfaction_missing)} have no recorded score. "
        "Missing scores are excluded from the average."
    )
    st.info(
        f"Department referral is Not Recorded for "
        f"{format_count(referrals_missing['missing_referral_count'])} visits "
        f"({format_percentage(referrals_missing['missing_referral_percentage'])})."
    )

    st.subheader("Patient flow")
    flow_left, flow_right = st.columns(2)
    with flow_left:
        admission_data = pd.DataFrame(
            {
                "Admission Status": ["Admitted", "Non-admitted"],
                "Patients": [
                    kpis["admitted_patients"],
                    kpis["non_admitted_patients"],
                ],
            }
        )
        render_chart(
            donut_chart(
                admission_data,
                names="Admission Status",
                values="Patients",
                title="Admission Status (Known Outcomes)",
            ),
            "admission-status",
        )
    monthly = monthly_patient_visits(dataframe)
    with flow_right:
        if monthly.empty:
            st.info("No valid admission dates are available for monthly trends.")
        else:
            figure = line_chart(
                monthly,
                x="Month",
                y="Patient Visits",
                title="Monthly Patient Visits",
                x_title="Admission month",
                y_title="Visits",
            )
            figure.update_xaxes(tickformat="%b %Y")
            render_chart(figure, "consolidated-monthly-visits")

    if not monthly.empty:
        admission_columns, rate_column = st.columns(2)
        with admission_columns:
            render_chart(
                stacked_bar_chart(
                    monthly,
                    x="Month",
                    y=["Admitted Patients", "Non-admitted Patients"],
                    title="Monthly Admission Trends",
                    x_title="Admission month",
                    y_title="Visits",
                ),
                "consolidated-monthly-admissions",
            )
        with rate_column:
            rate_data = monthly.dropna(subset=["Admission Rate (%)"])
            if not rate_data.empty:
                figure = line_chart(
                    rate_data,
                    x="Month",
                    y="Admission Rate (%)",
                    title="Monthly Admission Rate",
                    x_title="Admission month",
                    y_title="Admission rate (%)",
                    color="#4E7C59",
                )
                figure.update_yaxes(ticksuffix="%")
                figure.update_xaxes(tickformat="%b %Y")
                render_chart(figure, "consolidated-monthly-rate")
            else:
                st.info("Admission outcomes are not recorded for monthly trends.")

    st.subheader("Patient profile")
    gender = gender_distribution(dataframe)
    age = age_group_distribution(dataframe)
    race = race_distribution(dataframe)
    gender_column, age_column = st.columns(2)
    with gender_column:
        render_chart(
            donut_chart(gender, names="Gender", values="Patients", title="Gender Distribution"),
            "gender-distribution",
        )
    with age_column:
        render_chart(
            bar_chart(
                age,
                x="Age Group",
                y="Patients",
                title="Age Group Distribution",
                x_title="Age group",
                y_title="Visits",
                color="#6E9FC5",
            ),
            "age-distribution",
        )
    render_chart(
        bar_chart(
            race,
            x="Race",
            y="Patients",
            title="Race Distribution",
            x_title="Visits",
            y_title="Race category",
            horizontal=True,
        ),
        "race-distribution",
    )

    st.subheader("Department and waiting time")
    department_data = department_referral_distribution(dataframe)
    referral_column, wait_column = st.columns(2)
    with referral_column:
        render_chart(
            bar_chart(
                department_data,
                x="Department Referral",
                y="Patients",
                title="Department Referral Distribution",
                x_title="Patient visits",
                y_title="Department referral",
                horizontal=True,
                color="#4E7C59",
            ),
            "referral-distribution",
        )
    with wait_column:
        waits = waiting_time_distribution(dataframe)
        if waits.empty:
            st.info("No recorded waiting times for this selection.")
        else:
            render_chart(
                bar_chart(
                    waits,
                    x="Wait Time (minutes)",
                    y="Patient Visits",
                    title="Waiting-time Distribution",
                    x_title="Wait time (minutes)",
                    y_title="Visits",
                ),
                "waiting-time-distribution",
            )