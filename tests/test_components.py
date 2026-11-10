"""Tests for reusable dashboard component helpers."""

import pandas as pd

from src.analytics.filters import filter_patients
from src.components.filters import build_filter_kwargs, describe_filter_state
from src.components.tables import prepare_patient_details


def test_filter_builder_maps_all_sidebar_controls_consistently():
    filters = build_filter_kwargs(
        date_range=(pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-01-31").date()),
        genders=["NC"],
        age_groups=["60+"],
        races=["Asian"],
        departments=["Not Recorded"],
        admission_status="Non-admitted",
    )

    assert filters == {
        "admission_date_range": (
            pd.Timestamp("2024-01-01").date(),
            pd.Timestamp("2024-01-31").date(),
        ),
        "gender": ["NC"],
        "age_group": ["60+"],
        "race": ["Asian"],
        "department_referral": ["Not Recorded"],
        "admission_status": False,
    }
    state = describe_filter_state(
        date_range=filters["admission_date_range"],
        genders=["NC"],
        age_groups=["60+"],
        races=["Asian"],
        departments=["Not Recorded"],
        admission_status="Non-admitted",
    )
    assert any("Gender: NC" in label for label in state)


def test_patient_details_are_non_identifying_and_label_missing_values():
    dataframe = pd.DataFrame(
        {
            "Patient Id": ["private-id"],
            "Patient First Inital": ["private-first"],
            "Patient Last Name": ["private-last"],
            "Patient Admission Date": pd.to_datetime(["2024-01-02 08:15"]),
            "Patient Gender": ["NC"],
            "Patient Age": [61],
            "Patient Race": ["White"],
            "Department Referral": [pd.NA],
            "Patient Admission Flag": [True],
            "Patient Satisfaction Score": [pd.NA],
            "Patient Waittime": [pd.NA],
            "Patients CM": [1],
        }
    )

    details = prepare_patient_details(dataframe)

    assert "Patient Id" not in details.columns
    assert "Patient First Inital" not in details.columns
    assert "Patient Last Name" not in details.columns
    assert "Patients CM" not in details.columns
    assert details.loc[0, "Age Group"] == "60+"
    assert details.loc[0, "Admission Date"] == "02-01-2024"
    assert details.loc[0, "Department Referral"] == "Not Recorded"
    assert details.loc[0, "Satisfaction Score"] == "No response"
    assert details.loc[0, "Wait Time (minutes)"] == "Not Recorded"
    assert "private-id" not in details.to_string()
    assert "private-first" not in details.to_string()
    assert "private-last" not in details.to_string()

    filtered = filter_patients(dataframe, gender="NC")
    assert len(filtered) == 1