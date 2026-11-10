"""Privacy-conscious, bounded tables for patient detail views."""

import pandas as pd
import streamlit as st

from src.analytics.filters import age_group_series, filter_patients

DISPLAY_COLUMNS = [
    "Admission Date",
    "Gender",
    "Age Group",
    "Race",
    "Department Referral",
    "Admission Status",
    "Satisfaction Score",
    "Wait Time (minutes)",
]


def prepare_patient_details(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return display-safe fields only; omit direct identifiers and Patients CM."""
    selected = filter_patients(dataframe)
    display = pd.DataFrame(index=selected.index)

    if "Patient Admission Date" in selected:
        dates = pd.to_datetime(selected["Patient Admission Date"], errors="coerce")
        display["Admission Date"] = dates.dt.strftime("%d-%m-%Y").fillna(
            "Not Recorded"
        )
    if "Patient Gender" in selected:
        display["Gender"] = selected["Patient Gender"].astype("string").fillna(
            "Not Recorded"
        )
    if "Patient Age" in selected:
        display["Age Group"] = age_group_series(selected).astype("string").fillna(
            "Not Recorded"
        )
    if "Patient Race" in selected:
        display["Race"] = selected["Patient Race"].astype("string").fillna(
            "Not Recorded"
        )
    if "Department Referral" in selected:
        display["Department Referral"] = selected["Department Referral"].astype(
            "string"
        ).fillna("Not Recorded")
    if "Patient Admission Flag" in selected:
        display["Admission Status"] = selected["Patient Admission Flag"].map(
            {True: "Admitted", False: "Non-admitted"}
        ).astype("string").fillna("Not Recorded")
    if "Patient Satisfaction Score" in selected:
        display["Satisfaction Score"] = selected[
            "Patient Satisfaction Score"
        ].astype("string").fillna("No response")
    if "Patient Waittime" in selected:
        display["Wait Time (minutes)"] = selected["Patient Waittime"].astype(
            "string"
        ).fillna("Not Recorded")

    return display.reindex(columns=DISPLAY_COLUMNS)


def render_bounded_table(dataframe: pd.DataFrame, row_limit: int) -> None:
    st.dataframe(
        dataframe.head(row_limit),
        width="stretch",
        height=560,
        hide_index=True,
    )