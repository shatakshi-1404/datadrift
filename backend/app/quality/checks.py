from app.schemas.profile import DatasetProfile


def _severity(value: float, warning_threshold: float, critical_threshold: float) -> str:
    if value >= critical_threshold:
        return "critical"
    if value >= warning_threshold:
        return "warning"
    return "stable"


def check_missing_values(
    reference: DatasetProfile,
    current: DatasetProfile,
    warning_threshold: float,
    critical_threshold: float,
) -> list[dict]:
    """
    For every feature present in both profiles, compares current's
    missing percentage against reference's. Flags an INCREASE, not an
    absolute level.
    """
    reference_by_name = {f.name: f for f in reference.features}
    results = []
    for feature in current.features:
        reference_feature = reference_by_name.get(feature.name)
        if reference_feature is None:
            continue

        increase = round(feature.missing_percentage - reference_feature.missing_percentage, 2)
        results.append(
            {
                "feature": feature.name,
                "reference_missing_pct": reference_feature.missing_percentage,
                "current_missing_pct": feature.missing_percentage,
                "increase": increase,
                "status": _severity(increase, warning_threshold, critical_threshold),
            }
        )
    return results


def check_duplicates(
    current: DatasetProfile, warning_threshold: float, critical_threshold: float
) -> dict:
    """Dataset-level check: what share of current's rows are exact duplicates?"""
    return {
        "percentage": current.duplicate_percentage,
        "status": _severity(current.duplicate_percentage, warning_threshold, critical_threshold),
    }


def check_constant_columns(current: DatasetProfile) -> list[str]:
    """Columns with at most one distinct value in current."""
    return [feature.name for feature in current.features if feature.unique_count <= 1]
