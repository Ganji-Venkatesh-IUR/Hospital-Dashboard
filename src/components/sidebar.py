"""Dashboard navigation and combined sidebar filters."""

from datetime import date

import pandas as pd
import streamlit as st

from src.analytics.filters import AGE_GROUPS, NOT_RECORDED
from src.components.filters import build_filter_kwargs, describe_filter_state

SECTIONS = (
    "Monthly View",
    "Consolidated View",
    "Patient Details",
    "Key Takeaways",
)


def _options(dataframe: pd.DataFrame, column: str) -> list[str]:
    if column not in dataframe:
        return []
    return sorted(dataframe[column].dropna().astype(str).unique().tolist())


def _reset_filters(default_range: tuple[date, date] | None) -> None:
    st.session_state["er_date_range"] = default_range
    st.session_state["er_genders"] = []
    st.session_state["er_age_groups"] = []
    st.session_state["er_races"] = []
    st.session_state["er_departments"] = []
    st.session_state["er_admission_status"] = "All"


def render_sidebar(dataframe: pd.DataFrame):
    dates = (
        pd.to_datetime(dataframe["Patient Admission Date"], errors="coerce").dropna()
        if "Patient Admission Date" in dataframe
        else pd.Series(dtype="datetime64[ns]")
    )
    default_range = (
        (dates.min().date(), dates.max().date()) if not dates.empty else None
    )
    defaults = {
        "er_date_range": default_range,
        "er_genders": [],
        "er_age_groups": [],
        "er_races": [],
        "er_departments": [],
        "er_admission_status": "All",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    with st.sidebar:
        st.markdown("## Hospital ER")
        st.caption("ANALYTICS DASHBOARD")
        section = st.radio("Dashboard", SECTIONS, label_visibility="collapsed")
        st.divider()
        st.markdown("### Filters")
        if default_range is not None:
            selected_dates = st.date_input(
                "Admission date range",
                min_value=default_range[0],
                max_value=default_range[1],
                format="DD/MM/YYYY",
                key="er_date_range",
            )
            if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
                date_range = (selected_dates[0], selected_dates[1])
            elif isinstance(selected_dates, date):
                date_range = (selected_dates, selected_dates)
            else:
                date_range = None
        else:
            date_range = None
            st.caption("No valid admission dates available")

        genders = st.multiselect(
            "Gender", _options(dataframe, "Patient Gender"), key="er_genders"
        )
        age_groups = st.multiselect(
            "Age group", list(AGE_GROUPS), key="er_age_groups"
        )
        races = st.multiselect("Race", _options(dataframe, "Patient Race"), key="er_races")
        department_options = _options(dataframe, "Department Referral")
        department_options = sorted(set(department_options + [NOT_RECORDED]))
        departments = st.multiselect(
            "Department referral", department_options, key="er_departments"
        )
        admission_status = st.selectbox(
            "Admission status",
            ["All", "Admitted", "Non-admitted"],
            key="er_admission_status",
        )
        st.button(
            "Reset filters",
            icon=":material/restart_alt:",
            use_container_width=True,
            on_click=_reset_filters,
            args=(default_range,),
        )

    filters = build_filter_kwargs(
        date_range=date_range,
        genders=genders,
        age_groups=age_groups,
        races=races,
        departments=departments,
        admission_status=admission_status,
    )
    labels = describe_filter_state(
        date_range=date_range,
        genders=genders,
        age_groups=age_groups,
        races=races,
        departments=departments,
        admission_status=admission_status,
    )
    return section, filters, labels