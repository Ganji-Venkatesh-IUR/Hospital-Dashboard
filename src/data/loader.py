"""Read source CSV files without modifying them."""

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

EXPECTED_COLUMNS = (
    "Patient Id",
    "Patient Admission Date",
    "Patient First Inital",
    "Patient Last Name",
    "Patient Gender",
    "Patient Age",
    "Patient Race",
    "Department Referral",
    "Patient Admission Flag",
    "Patient Satisfaction Score",
    "Patient Waittime",
    "Patients CM",
)

DATE_COLUMNS = ("Patient Admission Date",)
ADMISSION_DATE_FORMAT = "%d-%m-%Y %H:%M"
INTEGER_COLUMNS = ("Patient Age", "Patient Waittime", "Patients CM")
NUMERIC_COLUMNS = (*INTEGER_COLUMNS, "Patient Satisfaction Score")
CATEGORY_COLUMNS = (
    "Patient Gender",
    "Patient Race",
    "Department Referral",
    "Patient Admission Flag",
)


def validate_schema(columns: Iterable[str]) -> list[str]:
    """Describe expected and unexpected fields without discarding any columns."""
    observed = list(columns)
    observed_set = set(observed)
    expected_set = set(EXPECTED_COLUMNS)
    warnings = []

    missing = [column for column in EXPECTED_COLUMNS if column not in observed_set]
    unexpected = [column for column in observed if column not in expected_set]
    if missing:
        warnings.append(f"Missing expected columns: {', '.join(missing)}.")
    if unexpected:
        warnings.append(f"Unexpected columns retained: {', '.join(unexpected)}.")
    return warnings


def load_csv(file_path: str | Path) -> pd.DataFrame:
    """Load and type known ER fields while retaining all source columns.

    Raises:
        FileNotFoundError: If the requested file does not exist.
        ValueError: If the file is empty or is not a valid, decodable CSV.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    try:
        dataframe = pd.read_csv(path, dtype={"Patient Id": "string"})
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"Dataset file is empty: {path}") from exc
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ValueError(f"Dataset is not a valid CSV file: {path}") from exc

    if dataframe.empty:
        raise ValueError(f"Dataset contains no data rows: {path}")

    for column in CATEGORY_COLUMNS:
        if column not in dataframe:
            continue
        if pd.api.types.is_bool_dtype(dataframe[column]):
            continue
        normalized = dataframe[column].astype("string").str.strip()
        dataframe[column] = normalized.mask(normalized.eq(""), pd.NA)

    for column in DATE_COLUMNS:
        if column in dataframe:
            dataframe[column] = pd.to_datetime(
                dataframe[column], format=ADMISSION_DATE_FORMAT, errors="coerce"
            )

    for column in NUMERIC_COLUMNS:
        if column not in dataframe:
            continue
        numeric = pd.to_numeric(dataframe[column], errors="coerce")
        if column in INTEGER_COLUMNS and not numeric.dropna().mod(1).ne(0).any():
            dataframe[column] = numeric.astype("Int64")
        else:
            dataframe[column] = numeric.astype("Float64")

    return dataframe