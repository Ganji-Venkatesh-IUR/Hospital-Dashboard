"""Demographic, department, and satisfaction summaries."""

from typing import Any

import pandas as pd

from src.analytics.filters import (
    AGE_GROUPS,
    NOT_RECORDED,
    age_group_series,
    filter_patients,
)
from src.analytics.kpis import (
    SATISFACTION_COLUMN,
    _admitted_count,
    _non_admitted_count,
)

DEPARTMENT_COLUMN = "Department Referral"


def _selected(dataframe: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    return filter_patients(dataframe, **filters)


def _distribution(
    dataframe: pd.DataFrame,
    column: str,
    output_name: str,
    *,
    filters: dict[str, Any],
    categories: tuple[str, ...] | None = None,
    missing_label: str | None = None,
) -> pd.DataFrame:
    selected = _selected(dataframe, filters)
    if column == "Age Group":
        values = age_group_series(selected)
    elif column in selected:
        values = selected[column].copy()
    elif missing_label is not None:
        values = pd.Series(missing_label, index=selected.index, dtype="string")
    else:
        values = pd.Series(dtype="object")

    if missing_label is not None:
        values = values.astype("string").fillna(missing_label)
    else:
        values = values.dropna()
    counts = values.value_counts(sort=False)
    if categories is not None:
        counts = counts.reindex(categories, fill_value=0)
    counts = counts[counts.index.notna()]
    total = int(counts.sum())
    percentages = (
        counts / total * 100
        if total
        else pd.Series(float("nan"), index=counts.index)
    )
    return pd.DataFrame(
        {
            output_name: counts.index.astype(str),
            "Patients": counts.to_numpy(dtype="int64"),
            "Percentage": percentages.to_numpy(dtype="float64"),
        }
    )


def gender_distribution(dataframe: pd.DataFrame, **filters: Any) -> pd.DataFrame:
    return _distribution(dataframe, "Patient Gender", "Gender", filters=filters)


def age_group_distribution(dataframe: pd.DataFrame, **filters: Any) -> pd.DataFrame:
    return _distribution(
        dataframe,
        "Age Group",
        "Age Group",
        filters=filters,
        categories=AGE_GROUPS,
    )


def race_distribution(dataframe: pd.DataFrame, **filters: Any) -> pd.DataFrame:
    return _distribution(dataframe, "Patient Race", "Race", filters=filters)


def department_referral_distribution(
    dataframe: pd.DataFrame, **filters: Any
) -> pd.DataFrame:
    return _distribution(
        dataframe,
        DEPARTMENT_COLUMN,
        "Department Referral",
        filters=filters,
        missing_label=NOT_RECORDED,
    )


def missing_referral_summary(
    dataframe: pd.DataFrame, **filters: Any
) -> dict[str, int | float | None]:
    selected = _selected(dataframe, filters)
    if DEPARTMENT_COLUMN not in selected:
        return {
            "missing_referral_count": None,
            "missing_referral_percentage": None,
        }
    missing = int(selected[DEPARTMENT_COLUMN].isna().sum())
    total = len(selected)
    return {
        "missing_referral_count": missing,
        "missing_referral_percentage": missing / total * 100 if total else None,
    }


def department_performance(dataframe: pd.DataFrame, **filters: Any) -> pd.DataFrame:
    """Return department counts, admission rates, and mean waiting times."""
    selected = _selected(dataframe, filters)
    columns = [
        "Department Referral",
        "Patient Visits",
        "Admitted Patients",
        "Non-admitted Patients",
        "Admission Rate (%)",
        "Average Wait Time (minutes)",
    ]
    if selected.empty:
        return pd.DataFrame(columns=columns)
    departments = (
        pd.Series(NOT_RECORDED, index=selected.index)
        if DEPARTMENT_COLUMN not in selected
        else selected[DEPARTMENT_COLUMN].astype("string").fillna(NOT_RECORDED)
    )
    waiting = (
        pd.to_numeric(selected["Patient Waittime"], errors="coerce")
        if "Patient Waittime" in selected
        else pd.Series(float("nan"), index=selected.index)
    )
    work = selected.assign(_Department=departments, _Waiting=waiting)
    rows = []
    for department, group in work.groupby("_Department", dropna=False, sort=True):
        admitted = _admitted_count(group)
        not_admitted = _non_admitted_count(group)
        known = admitted + not_admitted
        wait_values = group["_Waiting"].dropna()
        rows.append(
            {
                "Department Referral": str(department),
                "Patient Visits": len(group),
                "Admitted Patients": admitted,
                "Non-admitted Patients": not_admitted,
                "Admission Rate (%)": admitted / known * 100 if known else None,
                "Average Wait Time (minutes)": (
                    float(wait_values.mean()) if not wait_values.empty else None
                ),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def satisfaction_distribution(dataframe: pd.DataFrame, **filters: Any) -> pd.DataFrame:
    """Summarize only observed satisfaction scores; missing values are excluded."""
    selected = _selected(dataframe, filters)
    columns = ["Satisfaction Score", "Responses", "Percentage"]
    if SATISFACTION_COLUMN not in selected:
        return pd.DataFrame(columns=columns)
    scores = pd.to_numeric(selected[SATISFACTION_COLUMN], errors="coerce").dropna()
    counts = scores.value_counts().sort_index()
    total = int(counts.sum())
    percentages = (
        counts / total * 100
        if total
        else pd.Series(dtype="float64", index=counts.index)
    )
    return pd.DataFrame(
        {
            "Satisfaction Score": counts.index,
            "Responses": counts.to_numpy(dtype="int64"),
            "Percentage": percentages.to_numpy(dtype="float64"),
        }
    )


def department_satisfaction(
    dataframe: pd.DataFrame, *, min_responses: int = 5, **filters: Any
) -> pd.DataFrame:
    """Return department means only where observed responses meet the threshold."""
    columns = ["Department Referral", "Satisfaction Responses", "Average Satisfaction"]
    if min_responses < 1:
        raise ValueError("min_responses must be at least 1")
    selected = _selected(dataframe, filters)
    if SATISFACTION_COLUMN not in selected:
        return pd.DataFrame(columns=columns)
    departments = (
        pd.Series(NOT_RECORDED, index=selected.index)
        if DEPARTMENT_COLUMN not in selected
        else selected[DEPARTMENT_COLUMN].astype("string").fillna(NOT_RECORDED)
    )
    scores = pd.to_numeric(selected[SATISFACTION_COLUMN], errors="coerce")
    work = pd.DataFrame({"_Department": departments, "_Score": scores})
    rows = []
    for department, group in work.groupby("_Department", sort=True):
        observed = group["_Score"].dropna()
        if len(observed) >= min_responses:
            rows.append(
                {
                    "Department Referral": str(department),
                    "Satisfaction Responses": len(observed),
                    "Average Satisfaction": float(observed.mean()),
                }
            )
    return pd.DataFrame(rows, columns=columns)