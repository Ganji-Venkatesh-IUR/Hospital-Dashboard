"""Translate sidebar controls into shared analytics filter arguments."""

from datetime import date

from src.analytics.filters import AGE_GROUPS


def build_filter_kwargs(
    *,
    date_range: tuple[date, date] | None,
    genders: list[str],
    age_groups: list[str],
    races: list[str],
    departments: list[str],
    admission_status: str,
) -> dict[str, object]:
    """Build the exact keyword arguments accepted by ``filter_patients``."""
    filters: dict[str, object] = {}
    if date_range is not None:
        filters["admission_date_range"] = date_range
    if genders:
        filters["gender"] = genders
    if age_groups:
        filters["age_group"] = [group for group in age_groups if group in AGE_GROUPS]
    if races:
        filters["race"] = races
    if departments:
        filters["department_referral"] = departments
    if admission_status == "Admitted":
        filters["admission_status"] = True
    elif admission_status == "Non-admitted":
        filters["admission_status"] = False
    return filters


def describe_filter_state(
    *,
    date_range: tuple[date, date] | None,
    genders: list[str],
    age_groups: list[str],
    races: list[str],
    departments: list[str],
    admission_status: str,
) -> list[str]:
    """Return concise, non-sensitive labels describing active controls."""
    labels = []
    if date_range is not None:
        labels.append(
            f"{date_range[0]:%d %b %Y} to {date_range[1]:%d %b %Y}"
        )
    for label, values in (
        ("Gender", genders),
        ("Age", age_groups),
        ("Race", races),
        ("Referral", departments),
    ):
        if values:
            labels.append(f"{label}: {', '.join(values)}")
    if admission_status != "All":
        labels.append(f"Admission: {admission_status}")
    return labels