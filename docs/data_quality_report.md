# Data Quality Report

Source: `Hospital ER_Data.csv`

## Dataset Dimensions

- Rows: 9,216
- Columns: 12

## Schema and Missing Values

| Column | Raw inferred type | Pipeline type | Missing | Missing % |
| --- | --- | --- | ---: | ---: |
| `Patient Id` | `string` | `string` | 0 | 0.00% |
| `Patient Admission Date` | `str` | `datetime64[us]` | 0 | 0.00% |
| `Patient First Inital` | `str` | `str` | 0 | 0.00% |
| `Patient Last Name` | `str` | `str` | 0 | 0.00% |
| `Patient Gender` | `str` | `string` | 0 | 0.00% |
| `Patient Age` | `int64` | `Int64` | 0 | 0.00% |
| `Patient Race` | `str` | `string` | 0 | 0.00% |
| `Department Referral` | `str` | `string` | 5,400 | 58.59% |
| `Patient Admission Flag` | `bool` | `bool` | 0 | 0.00% |
| `Patient Satisfaction Score` | `float64` | `Float64` | 6,699 | 72.69% |
| `Patient Waittime` | `int64` | `Int64` | 0 | 0.00% |
| `Patients CM` | `int64` | `Int64` | 0 | 0.00% |

## Duplicate Records

- Exact duplicate rows after the first occurrence: 0.
- Repeated patient ID occurrences after the first: 0.
- Rows with a duplicated patient ID: 0.
- Patient ID values are intentionally excluded from this report.

## Admission Date

- Source format: `DD-MM-YYYY HH:MM` (9,216/9,216 non-missing values match).
- `Patient Admission Date` range: 2023-04-01 01:13:00 to 2024-10-30 23:44:00.
- Invalid non-missing dates: 0.

## Categorical Fields

| Column | Unique non-missing categories | Observed categories |
| --- | ---: | --- |
| `Patient Gender` | 3 | `F`, `M`, `NC` |
| `Patient Race` | 7 | `African American`, `Asian`, `Declined to Identify`, `Native American/Alaska Native`, `Pacific Islander`, `Two or More Races`, `White` |
| `Department Referral` | 7 | `Cardiology`, `Gastroenterology`, `General Practice`, `Neurology`, `Orthopedics`, `Physiotherapy`, `Renal` |
| `Patient Admission Flag` | 2 | `False`, `True` |

## Numeric Summaries

Continuous numeric fields are screened with IQR; binary numeric fields are excluded.

| Column | Count | Min | Q1 | Median | Q3 | Max | Outlier screening |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Patient Age` | 9,216 | 1 | 20 | 39 | 60 | 79 | 0 IQR-flagged rows |
| `Patient Waittime` | 9,216 | 10 | 23 | 35 | 48 | 60 | 0 IQR-flagged rows |
| `Patients CM` | 9,216 | 0 | 0 | 0 | 0 | 1 | Excluded (binary) |
| `Patient Satisfaction Score` | 2,517 | 0 | 2 | 5 | 8 | 10 | 0 IQR-flagged rows |

## Validation Warnings and Limitations

- Missing values occur in: Department Referral, Patient Satisfaction Score.
- No authoritative category codebook was supplied, so category values cannot be classified as unexpected from the CSV alone.
- The meaning of `Patients CM` is undocumented; no semantic interpretation is assigned.
- Patient names and ID values are omitted from this report.