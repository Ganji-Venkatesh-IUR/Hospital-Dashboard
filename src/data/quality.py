"""Build privacy-conscious, reusable data-quality reports."""

import pandas as pd

from src.data.loader import (
    CATEGORY_COLUMNS,
    ADMISSION_DATE_FORMAT,
    DATE_COLUMNS,
    NUMERIC_COLUMNS,
    validate_schema,
)

PRIVATE_COLUMNS = {
    "patient id",
    "patient first inital",
    "patient last name",
}
SAFE_CATEGORY_VALUE_COLUMNS = {
    "Patient Gender",
    "Patient Race",
    "Department Referral",
    "Patient Admission Flag",
}


def _is_private_column(column: str) -> bool:
    normalized = " ".join(column.casefold().split())
    return normalized in PRIVATE_COLUMNS or any(
        token in normalized.split() for token in ("name", "identifier")
    ) or normalized.endswith(" id")


def _format_values(values: list[object]) -> str:
    return ", ".join(f"`{value}`" for value in values)


def build_data_quality_report(
    raw_dataframe: pd.DataFrame,
    processed_dataframe: pd.DataFrame | None = None,
    source_name: str = "source CSV",
) -> str:
    """Return a Markdown quality report without patient-level values."""
    processed = processed_dataframe if processed_dataframe is not None else raw_dataframe
    row_count, column_count = raw_dataframe.shape
    warnings = validate_schema(raw_dataframe.columns)

    lines = [
        "# Data Quality Report",
        "",
        f"Source: `{source_name}`",
        "",
        "## Dataset Dimensions",
        "",
        f"- Rows: {row_count:,}",
        f"- Columns: {column_count}",
        "",
        "## Schema and Missing Values",
        "",
        "| Column | Raw inferred type | Pipeline type | Missing | Missing % |",
        "| --- | --- | --- | ---: | ---: |",
    ]

    for column in raw_dataframe.columns:
        raw_dtype = str(raw_dataframe[column].dtype)
        processed_dtype = (
            str(processed[column].dtype) if column in processed else "not loaded"
        )
        missing_count = int(raw_dataframe[column].isna().sum())
        missing_percent = missing_count / row_count * 100 if row_count else 0.0
        lines.append(
            f"| `{column}` | `{raw_dtype}` | `{processed_dtype}` | "
            f"{missing_count:,} | {missing_percent:.2f}% |"
        )

    duplicate_rows = int(raw_dataframe.duplicated().sum())
    lines.extend(
        [
            "",
            "## Duplicate Records",
            "",
            f"- Exact duplicate rows after the first occurrence: {duplicate_rows:,}.",
        ]
    )
    if "Patient Id" in raw_dataframe:
        patient_ids = raw_dataframe["Patient Id"]
        repeated_ids = int(patient_ids.duplicated().sum())
        affected_rows = int(patient_ids.duplicated(keep=False).sum())
        lines.extend(
            [
                f"- Repeated patient ID occurrences after the first: {repeated_ids:,}.",
                f"- Rows with a duplicated patient ID: {affected_rows:,}.",
                "- Patient ID values are intentionally excluded from this report.",
            ]
        )

    lines.extend(["", "## Admission Date", ""])
    for column in DATE_COLUMNS:
        if column not in raw_dataframe:
            continue
        original_dates = raw_dataframe[column]
        parsed_dates = pd.to_datetime(
            original_dates, format=ADMISSION_DATE_FORMAT, errors="coerce"
        )
        format_matches = int(
            original_dates.astype("string")
            .str.fullmatch(r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}", na=False)
            .sum()
        )
        non_missing_dates = int(original_dates.notna().sum())
        invalid_dates = int((original_dates.notna() & parsed_dates.isna()).sum())
        valid_dates = parsed_dates.dropna()
        if valid_dates.empty:
            date_range = "No valid dates found"
        else:
            date_range = (
                f"{valid_dates.min().isoformat(sep=' ')} to "
                f"{valid_dates.max().isoformat(sep=' ')}"
            )
        lines.extend(
            [
                f"- Source format: `DD-MM-YYYY HH:MM` "
                f"({format_matches:,}/{non_missing_dates:,} non-missing values match).",
                f"- `{column}` range: {date_range}.",
                f"- Invalid non-missing dates: {invalid_dates:,}.",
            ]
        )
        if invalid_dates:
            warnings.append(f"{invalid_dates:,} invalid admission date value(s).")

    lines.extend(
        [
            "",
            "## Categorical Fields",
            "",
            "| Column | Unique non-missing categories | Observed categories |",
            "| --- | ---: | --- |",
        ]
    )
    for column in raw_dataframe.columns:
        if _is_private_column(column):
            continue
        if column in NUMERIC_COLUMNS or column in DATE_COLUMNS:
            continue
        raw_series = raw_dataframe[column]
        if not (
            pd.api.types.is_object_dtype(raw_series)
            or pd.api.types.is_string_dtype(raw_series)
            or pd.api.types.is_bool_dtype(raw_series)
            or column in CATEGORY_COLUMNS
        ):
            continue
        value_series = processed[column] if column in processed else raw_series
        unique_count = int(value_series.nunique(dropna=True))
        observed_values = "Not listed"
        if column in SAFE_CATEGORY_VALUE_COLUMNS:
            normalized_values = value_series.dropna().astype(str).str.strip()
            values = sorted(normalized_values.unique().tolist())
            observed_values = _format_values(values) if values else "None"
        lines.append(f"| `{column}` | {unique_count:,} | {observed_values} |")

    lines.extend(
        [
            "",
            "## Numeric Summaries",
            "",
            "Continuous numeric fields are screened with IQR; binary numeric fields are excluded.",
            "",
            "| Column | Count | Min | Q1 | Median | Q3 | Max | Outlier screening |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for column in NUMERIC_COLUMNS:
        if column not in processed or _is_private_column(column):
            continue
        numeric = pd.to_numeric(processed[column], errors="coerce").dropna()
        if numeric.empty:
            lines.append(f"| `{column}` | 0 | - | - | - | - | - | 0 |")
            continue
        q1 = numeric.quantile(0.25)
        median = numeric.median()
        q3 = numeric.quantile(0.75)
        if numeric.nunique() == 2:
            screening = "Excluded (binary)"
            outlier_count = 0
        else:
            iqr = q3 - q1
            outlier_count = int(
                ((numeric < q1 - 1.5 * iqr) | (numeric > q3 + 1.5 * iqr)).sum()
            )
            screening = f"{outlier_count:,} IQR-flagged rows"
        lines.append(
            f"| `{column}` | {numeric.count():,} | {numeric.min():g} | {q1:g} | "
            f"{median:g} | {q3:g} | {numeric.max():g} | {screening} |"
        )
        if outlier_count and numeric.nunique() > 2:
            warnings.append(
                f"`{column}` has {outlier_count:,} IQR-flagged row(s); review against "
                "field-specific definitions before treating them as anomalous."
            )

    for column in NUMERIC_COLUMNS:
        if column not in raw_dataframe or column not in processed:
            continue
        raw_values = raw_dataframe[column]
        converted_values = pd.to_numeric(raw_values, errors="coerce")
        invalid_numeric = int(
            (raw_values.notna() & converted_values.isna()).sum()
        )
        if invalid_numeric:
            warnings.append(
                f"`{column}` contains {invalid_numeric:,} non-missing value(s) that "
                "could not be converted to numeric."
            )

    if duplicate_rows:
        warnings.append(f"{duplicate_rows:,} exact duplicate row(s) were found.")
    if "Patient Id" in raw_dataframe and raw_dataframe["Patient Id"].duplicated().any():
        warnings.append("Repeated patient ID values were found; values are not reported.")
    missing_columns = [
        column for column in raw_dataframe.columns if raw_dataframe[column].isna().any()
    ]
    if missing_columns:
        warnings.append(
            "Missing values occur in: " + ", ".join(missing_columns) + "."
        )

    warnings.extend(
        [
            "No authoritative category codebook was supplied, so category values "
            "cannot be classified as unexpected from the CSV alone.",
            "The meaning of `Patients CM` is undocumented; no semantic interpretation "
            "is assigned.",
            "Patient names and ID values are omitted from this report.",
        ]
    )
    lines.extend(["", "## Validation Warnings and Limitations", ""])
    lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines) + "\n"