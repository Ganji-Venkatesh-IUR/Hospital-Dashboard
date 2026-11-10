"""Overall emergency room KPI calculations."""

from typing import Any

import pandas as pd

from src.analytics.filters import filter_patients

ADMISSION_COLUMN = "Patient Admission Flag"
WAIT_COLUMN = "Patient Waittime"
AGE_COLUMN = "Patient Age"
SATISFACTION_COLUMN = "Patient Satisfaction Score"


def _filtered(dataframe: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    return filter_patients(dataframe, **filters)


def _admitted_count(dataframe: pd.DataFrame) -> int:
    if ADMISSION_COLUMN not in dataframe:
        return 0
    return int(dataframe[ADMISSION_COLUMN].eq(True).sum())


def _non_admitted_count(dataframe: pd.DataFrame) -> int:
    if ADMISSION_COLUMN not in dataframe:
        return 0
    return int(dataframe[ADMISSION_COLUMN].eq(False).sum())


def _numeric_column(dataframe: pd.DataFrame, column: str) -> pd.Series:
    if column not in dataframe:
        return pd.Series(dtype="float64")
    return pd.to_numeric(dataframe[column], errors="coerce").dropna()


def total_patient_visits(dataframe: pd.DataFrame, **filters: Any) -> int:
    """Count visits remaining after the requested filters."""
    return len(_filtered(dataframe, filters))


def admitted_patients(dataframe: pd.DataFrame, **filters: Any) -> int:
    """Count rows with a true admission flag."""
    return _admitted_count(_filtered(dataframe, filters))


def non_admitted_patients(dataframe: pd.DataFrame, **filters: Any) -> int:
    """Count rows with a false admission flag."""
    return _non_admitted_count(_filtered(dataframe, filters))


def admission_rate(dataframe: pd.DataFrame, **filters: Any) -> float | None:
    """Return admitted / known admission outcomes as a percentage."""
    selected = _filtered(dataframe, filters)
    admitted = _admitted_count(selected)
    known_outcomes = admitted + _non_admitted_count(selected)
    return admitted / known_outcomes * 100 if known_outcomes else None


def average_patient_wait_time(
    dataframe: pd.DataFrame, **filters: Any
) -> float | None:
    values = _numeric_column(_filtered(dataframe, filters), WAIT_COLUMN)
    return float(values.mean()) if not values.empty else None


def waiting_30_minutes_or_less_percentage(
    dataframe: pd.DataFrame, **filters: Any
) -> float | None:
    values = _numeric_column(_filtered(dataframe, filters), WAIT_COLUMN)
    if values.empty:
        return None
    return float(values.le(30).sum() / len(values) * 100)


def average_patient_age(dataframe: pd.DataFrame, **filters: Any) -> float | None:
    values = _numeric_column(_filtered(dataframe, filters), AGE_COLUMN)
    return float(values.mean()) if not values.empty else None


def average_patient_satisfaction(
    dataframe: pd.DataFrame, **filters: Any
) -> float | None:
    values = _numeric_column(_filtered(dataframe, filters), SATISFACTION_COLUMN)
    return float(values.mean()) if not values.empty else None


def satisfaction_response_count(dataframe: pd.DataFrame, **filters: Any) -> int:
    values = _numeric_column(_filtered(dataframe, filters), SATISFACTION_COLUMN)
    return len(values)


def missing_satisfaction_percentage(
    dataframe: pd.DataFrame, **filters: Any
) -> float | None:
    selected = _filtered(dataframe, filters)
    if selected.empty or SATISFACTION_COLUMN not in selected:
        return None
    return float(selected[SATISFACTION_COLUMN].isna().sum() / len(selected) * 100)


def calculate_overall_kpis(dataframe: pd.DataFrame, **filters: Any) -> dict[str, Any]:
    """Calculate all requested KPIs using one consistent filtered population."""
    selected = _filtered(dataframe, filters)
    admitted = _admitted_count(selected)
    non_admitted = _non_admitted_count(selected)
    known_outcomes = admitted + non_admitted
    wait_values = _numeric_column(selected, WAIT_COLUMN)
    age_values = _numeric_column(selected, AGE_COLUMN)
    satisfaction_values = _numeric_column(selected, SATISFACTION_COLUMN)
    total_visits = len(selected)
    missing_satisfaction = (
        int(selected[SATISFACTION_COLUMN].isna().sum())
        if SATISFACTION_COLUMN in selected
        else None
    )

    return {
        "total_patient_visits": total_visits,
        "admitted_patients": admitted,
        "non_admitted_patients": non_admitted,
        "known_admission_outcomes": known_outcomes,
        "admission_rate_percent": (
            admitted / known_outcomes * 100 if known_outcomes else None
        ),
        "average_wait_time_minutes": (
            float(wait_values.mean()) if not wait_values.empty else None
        ),
        "waiting_30_minutes_or_less_percent": (
            float(wait_values.le(30).sum() / len(wait_values) * 100)
            if not wait_values.empty
            else None
        ),
        "average_patient_age": float(age_values.mean()) if not age_values.empty else None,
        "average_satisfaction_score": (
            float(satisfaction_values.mean())
            if not satisfaction_values.empty
            else None
        ),
        "satisfaction_response_count": len(satisfaction_values),
        "missing_satisfaction_percent": (
            missing_satisfaction / total_visits * 100
            if missing_satisfaction is not None and total_visits
            else None
        ),
    }