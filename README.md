# Hospital Emergency Room Analytics Dashboard

## Project Overview

The Hospital Emergency Room Analytics Dashboard is a portfolio project for exploring real emergency room patient data and supporting operational analysis with clear, interactive visualizations. The application currently provides a typed data-loading foundation and dataset status; analytics and dashboard modules are not implemented yet.

## Business Problem

Emergency departments need reliable ways to understand patient flow and operational performance. This project will provide a structured place to examine those questions using an approved, real dataset, without assuming its fields or presenting unsupported results.

## Project Objectives

- Establish a maintainable Python and Streamlit application structure.
- Load a locally supplied CSV dataset without modifying the source file.
- Develop evidence-based operational insights after the dataset schema has been reviewed.
- Present future findings through a clear, interactive dashboard.

## Technology Stack

- Python
- Streamlit
- Pandas and NumPy
- Plotly
- Git and GitHub
- pytest

## Project Structure

```text
.
├── app.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── __init__.py
│   ├── analytics/
│   ├── components/
│   ├── data/
│   │   └── loader.py
│   └── utils/
├── assets/
├── docs/
├── tests/
├── .streamlit/
│   └── config.toml
├── .gitignore
├── requirements.txt
└── .python-version
```

## Installation

Use Python 3.11 or a compatible version supported by the installed dependencies. In GitHub Codespaces, open a terminal at the repository root and run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the Application

```bash
streamlit run app.py
```

The application starts without a dataset. When the configured CSV is present, it checks that the file can be loaded; it does not display patient-level records or analytics.

## Dataset and Verified Schema

The supplied source file is `data/raw/Hospital ER_Data.csv`. It contains 9,216 rows and 12 columns, matching the expected field names:

- `Patient Id` (identifier field; values are not published).
- `Patient Admission Date`.
- `Patient First Inital` and `Patient Last Name` (name fields; values are not published).
- `Patient Gender`, `Patient Age`, and `Patient Race`.
- `Department Referral` and `Patient Admission Flag`.
- `Patient Satisfaction Score`, `Patient Waittime`, and `Patients CM`.

The loader uses the observed filename from `config/settings.py`, parses admission dates using the verified `DD-MM-YYYY HH:MM` source format, converts known numeric fields, trims category whitespace, preserves categories such as `NC`, and retains all source columns. Invalid numeric/date values become missing in the loaded frame and are reported by the data-quality helper. The original CSV is not modified.

## Data Quality and Limitations

- 5,400 `Department Referral` values are missing (58.59%). They are not imputed.
- 6,699 `Patient Satisfaction Score` values are missing (72.69%). They are not replaced with zero.
- All 9,216 non-missing admission dates match `DD-MM-YYYY HH:MM`; parsing with that explicit format yields a range from 2023-04-01 01:13:00 to 2024-10-30 23:44:00, with no invalid dates.
- No exact duplicate rows or repeated patient ID values were found in this file. The report publishes counts only, never identifier values.
- Observed gender categories include `F`, `M`, and `NC`. No authoritative category codebook was supplied, so category values cannot be formally classified as unexpected.
- `Patients CM` contains numeric 0/1 values, but its meaning is undocumented and is not interpreted.
- `Patients CM` contains only 0 and 1 and is identified as binary, so it is excluded from continuous numeric IQR outlier detection.

The generated, privacy-conscious profile is in [`docs/data_quality_report.md`](docs/data_quality_report.md). It excludes patient name and ID values. Raw and processed data files are excluded from Git by default. Confirm the dataset's permissions and de-identification before use, and never publish sensitive patient information.

## Dataset Placement

Keep the original file at `data/raw/Hospital ER_Data.csv`, matching `SUPPORTED_DATASET_FILENAME` in `config/settings.py`. Do not replace or edit the original CSV as part of application processing.

## Planned Dashboard Modules

- Dataset profile and data-quality review.
- Emergency department operations overview.
- Patient arrival and throughput analysis.
- Wait-time and length-of-stay analysis, if supported by the dataset.
- Filters and drill-down views based on verified source fields.

These are planned modules, not implemented features. Their scope and definitions will be finalized after reviewing dataset documentation and obtaining authoritative definitions for ambiguous fields.

## Future Improvements

- Document the source, licensing, and authoritative definitions of the selected dataset.
- Implement analysis only for fields and operational definitions present in the real data.
- Add dashboard pages, accessibility checks, and deployment guidance.