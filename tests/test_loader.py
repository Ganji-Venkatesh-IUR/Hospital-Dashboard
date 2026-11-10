"""Unit tests for CSV loading and data-quality reporting."""

import pandas as pd
import pytest

from src.data.loader import load_csv, validate_schema
from src.data.quality import build_data_quality_report

CSV_HEADER = (
    "Patient Id,Patient Admission Date,Patient First Inital,Patient Last Name,"
    "Patient Gender,Patient Age,Patient Race,Department Referral,"
    "Patient Admission Flag,Patient Satisfaction Score,Patient Waittime,Patients CM"
)


def _write_csv(path, body):
    path.write_text(f"{CSV_HEADER}\n{body}", encoding="utf-8")
    return path


def test_load_csv_converts_fields_and_preserves_categories_and_missing_values(tmp_path):
    path = _write_csv(
        tmp_path / "fixture.csv",
        "ID-001,02-01-2024 08:15,X,Example, NC ,34,Asian,,True,,25,0\n"
        "ID-002,03-01-2024 09:30,Y,Example,M,41,White,Cardiology,False,8.5,30,1\n",
    )

    dataframe = load_csv(path)

    assert pd.api.types.is_datetime64_any_dtype(dataframe["Patient Admission Date"])
    assert dataframe.loc[0, "Patient Admission Date"] == pd.Timestamp("2024-01-02 08:15")
    assert str(dataframe["Patient Age"].dtype) == "Int64"
    assert str(dataframe["Patient Satisfaction Score"].dtype) == "Float64"
    assert dataframe.loc[0, "Patient Gender"] == "NC"
    assert pd.isna(dataframe.loc[0, "Department Referral"])
    assert pd.isna(dataframe.loc[0, "Patient Satisfaction Score"])
    assert len(dataframe.columns) == len(CSV_HEADER.split(","))


def test_missing_dataset_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="Dataset file not found"):
        load_csv(tmp_path / "missing.csv")


def test_invalid_dates_and_numeric_values_become_missing(tmp_path):
    path = _write_csv(
        tmp_path / "invalid-values.csv",
        "ID-001,not-a-date,X,Example,F,not-a-number,Asian,,True,7,25,0\n",
    )

    dataframe = load_csv(path)

    assert pd.isna(dataframe.loc[0, "Patient Admission Date"])
    assert pd.isna(dataframe.loc[0, "Patient Age"])


def test_quality_report_detects_duplicates_without_exposing_identifiers(tmp_path):
    path = _write_csv(
        tmp_path / "duplicates.csv",
        "ID-SENSITIVE,02-01-2024 08:15,X,NAME-SENSITIVE,F,34,Asian,,True,,25,0\n"
        "ID-SENSITIVE,03-01-2024 09:30,Y,OTHER-NAME,F,35,Asian,,False,,26,1\n",
    )
    raw_dataframe = pd.read_csv(path, dtype={"Patient Id": "string"})
    processed_dataframe = load_csv(path)

    report = build_data_quality_report(raw_dataframe, processed_dataframe)

    assert "Repeated patient ID occurrences after the first: 1" in report
    assert "DD-MM-YYYY HH:MM` (2/2 non-missing values match)" in report
    assert "ID-SENSITIVE" not in report
    assert "NAME-SENSITIVE" not in report
    assert "OTHER-NAME" not in report


def test_schema_warnings_retain_unexpected_columns(tmp_path):
    path = tmp_path / "extra-column.csv"
    columns = [column for column in CSV_HEADER.split(",") if column != "Patient Id"]
    path.write_text(
        f"{','.join(columns)},Unverified Field\n"
        "02-01-2024 08:15,X,Example,F,34,Asian,,True,,25,0,kept\n",
        encoding="utf-8",
    )

    dataframe = load_csv(path)
    warnings = validate_schema(dataframe.columns)

    assert "Unverified Field" in dataframe.columns
    assert any("Missing expected columns: Patient Id" in item for item in warnings)
    assert any("Unexpected columns retained: Unverified Field" in item for item in warnings)


def test_quality_report_counts_duplicate_records():
    dataframe = pd.DataFrame(
        {
            "Patient Id": pd.Series(["ID-001", "ID-001"], dtype="string"),
            "Patient Admission Date": ["02-01-2024 08:15", "02-01-2024 08:15"],
        }
    )

    report = build_data_quality_report(dataframe)

    assert "Exact duplicate rows after the first occurrence: 1" in report
    assert "Rows with a duplicated patient ID: 2" in report


def test_quality_report_excludes_binary_numeric_columns_from_iqr():
    dataframe = pd.DataFrame(
        {
            "Patient Age": [1, 2, 3, 1000],
            "Patients CM": [0, 0, 1, 1],
        }
    )

    report = build_data_quality_report(dataframe)

    assert "`Patients CM` | 4 | 0 | 0 | 0.5 | 1 | 1 | Excluded (binary)" in report
    assert "`Patient Age` has 1 IQR-flagged row(s)" in report
    assert "`Patients CM` has" not in report