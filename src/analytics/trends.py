"""Time-based patient visit and admission summaries."""

from typing import Any

import pandas as pd

from src.analytics.filters import filter_patients
from src.analytics.kpis import _admitted_count, _non_admitted_count
from src.data.loader import ADMISSION_DATE_FORMAT

DATE_COLUMN = "Patient Admission Date"
WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def _select(dataframe: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    return filter_patients(dataframe, **filters)


def _dates(dataframe: pd.DataFrame) -> pd.Series:
    if DATE_COLUMN not in dataframe:
        return pd.Series(pd.NaT, index=dataframe.index, dtype="datetime64[ns]")
    dates = dataframe[DATE_COLUMN]
    if not pd.api.types.is_datetime64_any_dtype(dates):
        return pd.to_datetime(dates, format=ADMISSION_DATE_FORMAT, errors="coerce")
    return dates


def _empty_monthly() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Month",
            "Patient Visits",
            "Admitted Patients",
            "Non-admitted Patients",
            "Admission Rate (%)",
        ]
    )


def monthly_patient_visits(dataframe: pd.DataFrame, **filters: Any) -> pd.DataFrame:
    """Summarize monthly visits, known admission outcomes, and admission rate."""
    selected = _select(dataframe, filters)
    dates = _dates(selected)
    valid = selected.loc[dates.notna()].copy()
    if valid.empty:
        return _empty_monthly()

    valid["_Month"] = dates.loc[dates.notna()].dt.to_period("M")
    rows = []
    for month, group in valid.groupby("_Month", sort=True):
        admitted = _admitted_count(group)
        non_admitted = _non_admitted_count(group)
        known = admitted + non_admitted
        rows.append(
            {
                "Month": month.to_timestamp(),
                "Patient Visits": len(group),
                "Admitted Patients": admitted,
                "Non-admitted Patients": non_admitted,
                "Admission Rate (%)": admitted / known * 100 if known else None,
            }
        )
    return pd.DataFrame(rows, columns=_empty_monthly().columns)


def daily_patient_visits(dataframe: pd.DataFrame, **filters: Any) -> pd.DataFrame:
    selected = _select(dataframe, filters)
    counts = _dates(selected).dropna().dt.normalize().value_counts().sort_index()
    return pd.DataFrame(
        {"Date": counts.index, "Patient Visits": counts.to_numpy(dtype="int64")}
    ).reset_index(drop=True)


def _distribution(values: pd.Series, labels: pd.Index, label_name: str) -> pd.DataFrame:
    counts = values.value_counts().reindex(labels, fill_value=0)
    denominator = int(counts.sum())
    percentages = (
        counts / denominator * 100
        if denominator
        else pd.Series(float("nan"), index=counts.index)
    )
    return pd.DataFrame(
        {
            label_name: counts.index,
            "Patient Visits": counts.to_numpy(dtype="int64"),
            "Percentage": percentages.to_numpy(dtype="float64"),
        }
    )


def hourly_arrival_distribution(
    dataframe: pd.DataFrame, **filters: Any
) -> pd.DataFrame:
    selected = _select(dataframe, filters)
    dates = _dates(selected).dropna()
    hours = pd.Index(range(24), name="Hour")
    return _distribution(dates.dt.hour, hours, "Hour")


def weekday_arrival_distribution(
    dataframe: pd.DataFrame, **filters: Any
) -> pd.DataFrame:
    selected = _select(dataframe, filters)
    dates = _dates(selected).dropna()
    weekdays = pd.Index(WEEKDAYS, name="Weekday")
    return _distribution(dates.dt.day_name(), weekdays, "Weekday")


def waiting_time_distribution(
    dataframe: pd.DataFrame, **filters: Any
) -> pd.DataFrame:
    """Count observed wait times by exact minute; missing times are excluded."""
    selected = _select(dataframe, filters)
    columns = ["Wait Time (minutes)", "Patient Visits", "Percentage"]
    if "Patient Waittime" not in selected:
        return pd.DataFrame(columns=columns)
    waits = pd.to_numeric(selected["Patient Waittime"], errors="coerce").dropna()
    counts = waits.value_counts().sort_index()
    total = int(counts.sum())
    percentages = counts / total * 100 if total else pd.Series(dtype="float64")
    return pd.DataFrame(
        {
            "Wait Time (minutes)": counts.index,
            "Patient Visits": counts.to_numpy(dtype="int64"),
            "Percentage": percentages.to_numpy(dtype="float64"),
        }
    )