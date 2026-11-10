"""Shared filtering and age-group helpers for analytics outputs."""

from collections.abc import Iterable
from datetime import date, datetime

import pandas as pd

from src.data.loader import ADMISSION_DATE_FORMAT

AGE_GROUPS = ("0-17", "18-29", "30-39", "40-49", "50-59", "60+")
NOT_RECORDED = "Not Recorded"
PRIVATE_COLUMNS = {"patient id", "patient first inital", "patient last name"}


def _is_private_column(column: str) -> bool:
    normalized = " ".join(column.casefold().split())
    return normalized in PRIVATE_COLUMNS or any(
        token in normalized.split() for token in ("name", "identifier")
    ) or normalized.endswith(" id")


def age_group_series(dataframe: pd.DataFrame) -> pd.Series:
    """Return ordered age groups without modifying the input frame."""
    if "Patient Age" not in dataframe:
        return pd.Series(pd.NA, index=dataframe.index, dtype="string")
    ages = pd.to_numeric(dataframe["Patient Age"], errors="coerce")
    return pd.cut(
        ages,
        bins=[0, 18, 30, 40, 50, 60, float("inf")],
        labels=AGE_GROUPS,
        right=False,
        ordered=True,
    )


def _as_values(value: object) -> list[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        return [value]
    return list(value)


def _date_bound(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()


def _admission_status_mask(status: pd.Series, requested: object) -> pd.Series:
    aliases = {
        "admitted": True,
        "true": True,
        "yes": True,
        "1": True,
        "non-admitted": False,
        "not admitted": False,
        "not_admitted": False,
        "false": False,
        "no": False,
        "0": False,
    }
    normalized = set()
    for value in _as_values(requested):
        if isinstance(value, bool):
            normalized.add(value)
            continue
        key = str(value).strip().casefold()
        if key not in aliases:
            raise ValueError(f"Unsupported admission status filter: {value}")
        normalized.add(aliases[key])
    return status.isin(normalized)


def filter_patients(
    dataframe: pd.DataFrame,
    *,
    admission_date_range: tuple[object | None, object | None] | None = None,
    gender: object = None,
    age_group: object = None,
    race: object = None,
    department_referral: object = None,
    admission_status: object = None,
) -> pd.DataFrame:
    """Filter rows consistently and remove patient identifiers and names.

    Date-range endpoints are inclusive calendar dates. Missing departments can
    be selected through the ``Not Recorded`` label without reclassifying them.
    """
    mask = pd.Series(True, index=dataframe.index, dtype=bool)

    if admission_date_range is not None:
        if len(admission_date_range) != 2:
            raise ValueError("admission_date_range must contain start and end values")
        if "Patient Admission Date" not in dataframe:
            empty = dataframe.iloc[0:0]
            return empty.drop(
                columns=[column for column in empty if _is_private_column(column)],
                errors="ignore",
            ).copy()
        dates = dataframe["Patient Admission Date"]
        if not pd.api.types.is_datetime64_any_dtype(dates):
            dates = pd.to_datetime(
                dates, format=ADMISSION_DATE_FORMAT, errors="coerce"
            )
        calendar_dates = dates.dt.date
        start, end = admission_date_range
        if start is not None:
            mask &= calendar_dates >= _date_bound(start)
        if end is not None:
            mask &= calendar_dates <= _date_bound(end)

    for column, selected in (
        ("Patient Gender", gender),
        ("Patient Race", race),
        ("Department Referral", department_referral),
    ):
        if selected is None:
            continue
        if column not in dataframe:
            mask &= False
            continue
        values = _as_values(selected)
        include_missing = column == "Department Referral" and NOT_RECORDED in values
        explicit_values = [value for value in values if value != NOT_RECORDED]
        column_mask = dataframe[column].isin(explicit_values)
        if include_missing:
            column_mask |= dataframe[column].isna()
        mask &= column_mask

    if age_group is not None:
        mask &= age_group_series(dataframe).isin(_as_values(age_group))

    if admission_status is not None:
        if "Patient Admission Flag" not in dataframe:
            mask &= False
        else:
            mask &= _admission_status_mask(
                dataframe["Patient Admission Flag"], admission_status
            )

    filtered = dataframe.loc[mask].copy()
    private_columns = [column for column in filtered if _is_private_column(column)]
    return filtered.drop(columns=private_columns)