"""Evidence-based operational observations for the active filter selection."""

import pandas as pd
import streamlit as st

from src.analytics.kpis import calculate_overall_kpis
from src.analytics.segments import (
    age_group_distribution,
    department_referral_distribution,
    gender_distribution,
    missing_referral_summary,
)
from src.analytics.trends import monthly_patient_visits
from src.components.kpi_cards import format_count, format_number, format_percentage


def render_key_takeaways(dataframe: pd.DataFrame) -> None:
    if dataframe.empty:
        st.info("No visits match the selected filters.")
        return

    kpis = calculate_overall_kpis(dataframe)
    monthly = monthly_patient_visits(dataframe)
    age = age_group_distribution(dataframe)
    gender = gender_distribution(dataframe)
    referrals = department_referral_distribution(dataframe)
    missing_referrals = missing_referral_summary(dataframe)

    st.subheader("Admission and waiting time")
    st.markdown(
        f"- **Admission:** {format_count(kpis['admitted_patients'])} of "
        f"{format_count(kpis['known_admission_outcomes'])} "
        f"visits with a known outcome were admitted "
        f"({format_percentage(kpis['admission_rate_percent'])})."
    )
    st.markdown(
        f"- **Waiting:** average recorded wait was "
        f"{format_number(kpis['average_wait_time_minutes'])} minutes; "
        f"{format_percentage(kpis['waiting_30_minutes_or_less_percent'])} "
        "of recorded waits were 30 minutes or less."
    )

    st.subheader("Patient volume")
    if monthly.empty:
        st.write("No valid admission dates are available in this selection.")
    else:
        busiest = monthly.loc[monthly["Patient Visits"].idxmax()]
        quietest = monthly.loc[monthly["Patient Visits"].idxmin()]
        st.markdown(
            f"- **Monthly volume:** highest observed month was "
            f"{busiest['Month']:%B %Y} ({int(busiest['Patient Visits']):,} visits); "
            f"lowest was {quietest['Month']:%B %Y} "
            f"({int(quietest['Patient Visits']):,} visits)."
        )

    st.subheader("Demographic profile")
    if not age.empty:
        largest_age_group = age.loc[age["Patients"].idxmax()]
        st.markdown(
            f"- **Age:** the largest configured age group was "
            f"{largest_age_group['Age Group']} "
            f"({int(largest_age_group['Patients']):,} visits)."
        )
    if not gender.empty:
        largest_gender = gender.loc[gender["Patients"].idxmax()]
        st.markdown(
            f"- **Gender:** the most frequent recorded category was "
            f"{largest_gender['Gender']} ({int(largest_gender['Patients']):,} visits); "
            "categories such as NC remain distinct."
        )

    st.subheader("Department referrals")
    recorded = referrals.loc[referrals["Department Referral"] != "Not Recorded"]
    if recorded.empty:
        st.write("No department referral categories are recorded for this selection.")
    else:
        top_referral = recorded.loc[recorded["Patients"].idxmax()]
        st.markdown(
            f"- **Recorded referrals:** {top_referral['Department Referral']} was "
            f"the most frequent recorded category ({int(top_referral['Patients']):,} visits)."
        )
    st.markdown(
        f"- **Referral completeness:** {format_count(missing_referrals['missing_referral_count'])} "
        f"visits ({format_percentage(missing_referrals['missing_referral_percentage'])}) "
        "have no recorded department referral; this is not interpreted as not referred."
    )

    st.subheader("Satisfaction coverage")
    st.markdown(
        f"- **Responses:** {format_count(kpis['satisfaction_response_count'])} of "
        f"{format_count(kpis['total_patient_visits'])} visits have a recorded score. "
        f"The observed average is {format_number(kpis['average_satisfaction_score'])}; "
        f"{format_percentage(kpis['missing_satisfaction_percent'])} are missing."
    )

    st.subheader("Operational review opportunities")
    st.markdown(
        "- Review referral and satisfaction capture completeness using the missingness rates above.\n"
        "- Compare arrival volume by month, weekday, and hour when reviewing operational coverage; these summaries show timing, not its causes.\n"
        "- Track the recorded wait-time average and 30-minute threshold over time before drawing conclusions about performance changes."
    )