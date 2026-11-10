"""Reusable, privacy-conscious emergency room analytics."""

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

__all__ = [
	"AGE_GROUPS",
	"admitted_patients",
	"admission_rate",
	"age_group_distribution",
	"average_patient_age",
	"average_patient_satisfaction",
	"average_patient_wait_time",
	"calculate_overall_kpis",
	"daily_patient_visits",
	"department_performance",
	"department_referral_distribution",
	"department_satisfaction",
	"filter_patients",
	"gender_distribution",
	"hourly_arrival_distribution",
	"missing_referral_summary",
	"missing_satisfaction_percentage",
	"monthly_patient_visits",
	"non_admitted_patients",
	"race_distribution",
	"satisfaction_distribution",
	"satisfaction_response_count",
	"total_patient_visits",
	"waiting_30_minutes_or_less_percentage",
	"waiting_time_distribution",
	"weekday_arrival_distribution",
]