from app.models.alert import Alert
from app.models.drift_result import DriftResult
from app.models.performance_result import PerformanceResult
from app.schemas.performance import classify_performance_change

PREDICTION_FEATURE_NAMES = {"predicted_class", "predicted_probability"}
QUALITY_METRIC_NAMES = {"missing_percentage_increase", "duplicate_percentage"}


def _drift_severity(status: str) -> str | None:
    return {"warning": "WARNING", "drift": "CRITICAL"}.get(status)


def _quality_severity(status: str) -> str | None:
    return {"warning": "WARNING", "critical": "CRITICAL"}.get(status)


def evaluate_drift_alerts(drift_results: list[DriftResult]) -> list[tuple]:
    """
    Returns (severity, title, message) tuples derived entirely from
    already-computed DriftResult rows. PSI drives feature/prediction drift
    alerts; KS and chi-square remain visible in /drift for statistical-
    significance detail but don't independently trigger alerts.
    """
    alerts: list[tuple] = []

    for row in drift_results:
        if row.metric_name == "psi" and row.feature_name != "__dataset__":
            severity = _drift_severity(row.status)
            if severity is None:
                continue
            if row.feature_name in PREDICTION_FEATURE_NAMES:
                title = f"Prediction distribution change: {row.feature_name}"
                message = (
                    f"PSI={row.metric_value:.3f} indicates a {row.status} shift in the "
                    f"model's {row.feature_name.replace('_', ' ')} between reference and current data."
                )
            else:
                title = f"Feature drift detected: {row.feature_name}"
                message = (
                    f"PSI={row.metric_value:.3f} indicates a {row.status} shift in "
                    f"'{row.feature_name}' relative to the reference dataset."
                )
            alerts.append((severity, title, message))

        elif row.metric_name in QUALITY_METRIC_NAMES:
            severity = _quality_severity(row.status)
            if severity is None:
                continue
            if row.metric_name == "duplicate_percentage":
                title = "Data quality issue: duplicate rows"
                message = f"{row.metric_value:.1f}% of rows in the current dataset are exact duplicates."
            else:
                title = f"Data quality issue: {row.feature_name}"
                message = (
                    f"Missing values in '{row.feature_name}' increased by "
                    f"{row.metric_value:.1f} percentage points versus reference."
                )
            alerts.append((severity, title, message))

        elif row.metric_name == "constant_column":
            alerts.append(
                (
                    "WARNING",
                    f"Column became constant: {row.feature_name}",
                    f"'{row.feature_name}' now has a single unique value in the current dataset, "
                    "which often indicates an upstream data problem.",
                )
            )

        elif row.metric_name == "new_category_count" and row.metric_value > 0:
            count = int(row.metric_value)
            alerts.append(
                (
                    "WARNING",
                    f"New category detected: {row.feature_name}",
                    f"{count} new categor{'y' if count == 1 else 'ies'} appeared in "
                    f"'{row.feature_name}' that {'was' if count == 1 else 'were'} not present in reference.",
                )
            )

    return alerts


def evaluate_performance_alerts(
    performance_rows: list[PerformanceResult], degradation_threshold: float
) -> list[tuple]:
    """
    Flags a metric as degraded using the same threshold logic the
    /performance endpoint uses - alerts and API responses never disagree
    about what counts as "degraded".
    """
    alerts: list[tuple] = []
    for row in performance_rows:
        change = row.current_value - row.reference_value
        status = classify_performance_change(change, degradation_threshold)
        if status != "degraded":
            continue

        severity = "CRITICAL" if abs(change) >= degradation_threshold * 2 else "WARNING"
        title = f"Model performance degraded: {row.metric_name}"
        message = (
            f"{row.metric_name} dropped from {row.reference_value:.3f} (reference/test) "
            f"to {row.current_value:.3f} (current) - a change of {change:.3f}."
        )
        alerts.append((severity, title, message))

    return alerts


def generate_alerts(
    run_id: int,
    drift_results: list[DriftResult],
    performance_rows: list[PerformanceResult],
    degradation_threshold: float,
) -> list[Alert]:
    raw_alerts = evaluate_drift_alerts(drift_results) + evaluate_performance_alerts(
        performance_rows, degradation_threshold
    )
    return [
        Alert(monitoring_run_id=run_id, severity=severity, title=title, message=message)
        for severity, title, message in raw_alerts
    ]
