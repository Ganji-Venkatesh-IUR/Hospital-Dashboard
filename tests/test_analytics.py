"""Tests for the reusable, privacy-conscious analytics layer."""

import pandas as pd
import pytest

from src.analytics.filters import AGE_GROUPS, filter_patients
from src.analytics.kpis import (
    admitted_patients,
    admission_rate,
    average_patient_age,
    average_patient_satisfaction,
    average_patient_wait_time,
    calculate_overall_kpis,
    missing_satisfaction_percentage,
    non_admitted_patients,
    satisfaction_response_count,
    total_patient_visits,
    waiting_30_minutes_or_less_percentage,
)
from src.analytics.segments import (
    age_group_distribution,
    department_performance,
    department_referral_distribution,
    department_satisfaction,
    gender_distribution,
    missing_referral_summary,
    race_distribution,
    satisfaction_distribution,
)
from src.analytics.trends import (
    daily_patient_visits,
    hourly_arrival_distribution,
    monthly_patient_visits,
    weekday_arrival_distribution,
    waiting_time_distribution,
)


@pytest.fixture
def analytics_data():
    return pd.DataFrame(
        {
            "Patient Id": [f"private-id-{index}" for index in range(7)],
            "Patient First Inital": ["private-first"] * 7,
            "Patient Last Name": ["private-last"] * 7,
            "Patient Admission Date": pd.to_datetime(
                [
                    "2024-01-01 08:15",
                    "2024-01-01 08:40",
                    "2024-01-02 09:00",
                    "2024-02-01 10:00",
                    "2024-02-01 15:00",
                    "2024-02-02 23:59",
                    "2024-03-03 11:00",
                ]
            ),
            "Patient Gender": ["F", "M", "NC", "F", "M", "F", "NC"],
            "Patient Age": [17, 18, 29, 30, 59, 60, 45],
            "Patient Race": ["White", "Asian", "White", "Asian", "White", "White", "Other"],
            "Department Referral": [
                "Cardiology",
                pd.NA,
                "Cardiology",
                "Renal",
                "Renal",
                pd.NA,
                "Cardiology",
            ],
            "Patient Admission Flag": pd.Series(
                [True, False, True, False, True, True, pd.NA], dtype="boolean"
            ),
            "Patient Satisfaction Score": [10, pd.NA, 8, pd.NA, 6, 0, 9],
            "Patient Waittime": [30, 31, 20, 45, pd.NA, 30, 10],
            "Patients CM": [0, 1, 0, 1, 0, 1, 0],
        }
    )


def test_overall_kpis_use_correct_counts_and_denominators(analytics_data):
    kpis = calculate_overall_kpis(analytics_data)

    assert kpis["total_patient_visits"] == 7
    assert kpis["admitted_patients"] == 4
    assert kpis["non_admitted_patients"] == 2
    assert kpis["admission_rate_percent"] == pytest.approx(4 / 6 * 100)
    assert kpis["average_wait_time_minutes"] == pytest.approx(166 / 6)
    assert kpis["waiting_30_minutes_or_less_percent"] == pytest.approx(4 / 6 * 100)
    assert kpis["average_patient_age"] == pytest.approx(258 / 7)
    assert total_patient_visits(analytics_data) == 7
    assert admitted_patients(analytics_data) == 4
    assert non_admitted_patients(analytics_data) == 2
    assert admission_rate(analytics_data) == pytest.approx(4 / 6 * 100)
    assert average_patient_wait_time(analytics_data) == pytest.approx(166 / 6)
    assert waiting_30_minutes_or_less_percentage(analytics_data) == pytest.approx(
        4 / 6 * 100
    )
    assert average_patient_age(analytics_data) == pytest.approx(258 / 7)


def test_missing_satisfaction_is_excluded_and_missing_rate_uses_visits(analytics_data):
    kpis = calculate_overall_kpis(analytics_data)

    assert kpis["average_satisfaction_score"] == pytest.approx(6.6)
    assert kpis["satisfaction_response_count"] == 5
    assert kpis["missing_satisfaction_percent"] == pytest.approx(2 / 7 * 100)
    assert satisfaction_distribution(analytics_data)["Responses"].sum() == 5
    assert average_patient_satisfaction(analytics_data) == pytest.approx(6.6)
    assert satisfaction_response_count(analytics_data) == 5
    assert missing_satisfaction_percentage(analytics_data) == pytest.approx(2 / 7 * 100)


def test_monthly_daily_hourly_and_weekday_trends(analytics_data):
    monthly = monthly_patient_visits(analytics_data).set_index("Month")

    assert monthly.loc[pd.Timestamp("2024-01-01"), "Patient Visits"] == 3
    assert monthly.loc[pd.Timestamp("2024-01-01"), "Admitted Patients"] == 2
    assert monthly.loc[pd.Timestamp("2024-01-01"), "Non-admitted Patients"] == 1
    assert monthly.loc[pd.Timestamp("2024-01-01"), "Admission Rate (%)"] == pytest.approx(200 / 3)
    assert pd.isna(monthly.loc[pd.Timestamp("2024-03-01"), "Admission Rate (%)"])

    daily = daily_patient_visits(analytics_data)
    assert daily["Patient Visits"].sum() == 7
    assert daily.loc[daily["Date"] == pd.Timestamp("2024-01-01"), "Patient Visits"].iloc[0] == 2

    hourly = hourly_arrival_distribution(analytics_data)
    assert len(hourly) == 24
    assert hourly.loc[hourly["Hour"] == 8, "Patient Visits"].iloc[0] == 2
    assert hourly["Patient Visits"].sum() == 7

    weekdays = weekday_arrival_distribution(analytics_data).set_index("Weekday")
    assert weekdays.loc["Monday", "Patient Visits"] == 2
    assert weekdays.loc["Sunday", "Patient Visits"] == 1
    assert weekdays["Patient Visits"].sum() == 7

    waits = waiting_time_distribution(analytics_data)
    assert waits["Patient Visits"].sum() == 6
    assert waits.loc[waits["Wait Time (minutes)"] == 30, "Patient Visits"].iloc[0] == 2


def test_demographic_distributions_preserve_nc_and_age_boundaries(analytics_data):
    genders = gender_distribution(analytics_data).set_index("Gender")
    assert genders.loc["NC", "Patients"] == 2

    ages = age_group_distribution(analytics_data).set_index("Age Group")
    assert tuple(ages.index) == AGE_GROUPS
    assert ages["Patients"].to_dict() == {
        "0-17": 1,
        "18-29": 2,
        "30-39": 1,
        "40-49": 1,
        "50-59": 1,
        "60+": 1,
    }

    races = race_distribution(analytics_data)
    assert races["Patients"].sum() == 7
    assert "Other" in races["Race"].values


def test_department_summaries_label_missing_referrals(analytics_data):
    referral_summary = missing_referral_summary(analytics_data)
    assert referral_summary["missing_referral_count"] == 2
    assert referral_summary["missing_referral_percentage"] == pytest.approx(2 / 7 * 100)

    distribution = department_referral_distribution(analytics_data).set_index(
        "Department Referral"
    )
    assert distribution.loc["Not Recorded", "Patients"] == 2

    departments = department_performance(analytics_data).set_index("Department Referral")
    assert departments.loc["Cardiology", "Patient Visits"] == 3
    assert departments.loc["Cardiology", "Admission Rate (%)"] == 100
    assert departments.loc["Renal", "Admission Rate (%)"] == 50
    assert departments.loc["Renal", "Average Wait Time (minutes)"] == 45
    assert departments.loc["Not Recorded", "Patient Visits"] == 2

    satisfaction = department_satisfaction(analytics_data, min_responses=2).set_index(
        "Department Referral"
    )
    assert satisfaction.loc["Cardiology", "Satisfaction Responses"] == 3
    assert satisfaction.loc["Cardiology", "Average Satisfaction"] == 9
    assert "Renal" not in satisfaction.index


def test_filters_compose_consistently_and_hide_identifiers(analytics_data):
    selected = filter_patients(
        analytics_data,
        admission_date_range=("2024-01-01", "2024-01-01"),
        gender="F",
        age_group="0-17",
        race="White",
        department_referral="Cardiology",
        admission_status="Admitted",
    )
    assert len(selected) == 1
    assert not {"Patient Id", "Patient First Inital", "Patient Last Name"}.intersection(
        selected.columns
    )
    assert calculate_overall_kpis(
        analytics_data, admission_status=True, gender="F"
    )["total_patient_visits"] == 2

    not_recorded = filter_patients(analytics_data, department_referral="Not Recorded")
    assert len(not_recorded) == 2


def test_empty_filter_results_are_safe_and_do_not_invent_rates(analytics_data):
    empty = calculate_overall_kpis(analytics_data, gender="unobserved")
    assert empty["total_patient_visits"] == 0
    assert empty["admitted_patients"] == 0
    assert empty["admission_rate_percent"] is None
    assert empty["average_wait_time_minutes"] is None
    assert empty["average_satisfaction_score"] is None
    assert empty["missing_satisfaction_percent"] is None
    assert missing_satisfaction_percentage(analytics_data, gender="unobserved") is None
    assert missing_referral_summary(analytics_data, gender="unobserved") == {
        "missing_referral_count": 0,
        "missing_referral_percentage": None,
    }
    assert monthly_patient_visits(analytics_data, gender="unobserved").empty
    assert department_performance(analytics_data, gender="unobserved").empty


def test_missing_metric_columns_return_undefined_percentages():
    dataframe = pd.DataFrame({"Patient Gender": ["F"]})

    assert missing_satisfaction_percentage(dataframe) is None
    assert missing_referral_summary(dataframe) == {
        "missing_referral_count": None,
        "missing_referral_percentage": None,
    }


def test_analytics_outputs_never_expose_patient_names_or_ids(analytics_data):
    outputs = [
        gender_distribution(analytics_data),
        age_group_distribution(analytics_data),
        race_distribution(analytics_data),
        department_referral_distribution(analytics_data),
        department_performance(analytics_data),
        satisfaction_distribution(analytics_data),
        department_satisfaction(analytics_data, min_responses=1),
        monthly_patient_visits(analytics_data),
        daily_patient_visits(analytics_data),
        hourly_arrival_distribution(analytics_data),
        weekday_arrival_distribution(analytics_data),
        waiting_time_distribution(analytics_data),
    ]
    for output in outputs:
        assert not any("patient id" in column.casefold() for column in output.columns)
        assert not any("name" in column.casefold() for column in output.columns)
        rendered = output.to_string()
        assert "private-id-" not in rendered
        assert "private-first" not in rendered
        assert "private-last" not in rendered