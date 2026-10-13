from app.models.drift_result import DriftResult
from app.models.performance_result import PerformanceResult
from app.services.alert_service import evaluate_drift_alerts, evaluate_performance_alerts


def _drift_row(feature_name: str, metric_name: str, value: float, status: str) -> DriftResult:
    return DriftResult(
        monitoring_run_id=1, feature_name=feature_name, metric_name=metric_name,
        metric_value=value, status=status,
    )


def test_psi_drift_status_produces_a_critical_alert():
    rows = [_drift_row("income", "psi", 0.4, "drift")]
    alerts = evaluate_drift_alerts(rows)
    assert len(alerts) == 1
    severity, title, _ = alerts[0]
    assert severity == "CRITICAL"
    assert "income" in title


def test_psi_stable_status_produces_no_alert():
    rows = [_drift_row("income", "psi", 0.02, "stable")]
    assert evaluate_drift_alerts(rows) == []


def test_ks_statistic_alone_does_not_trigger_an_alert():
    rows = [_drift_row("income", "ks_statistic", 0.4, "drift")]
    assert evaluate_drift_alerts(rows) == []


def test_constant_column_produces_a_warning_alert():
    rows = [_drift_row("plan", "constant_column", 1.0, "warning")]
    severity, _, _ = evaluate_drift_alerts(rows)[0]
    assert severity == "WARNING"


def test_new_category_alert_only_fires_when_count_is_positive():
    assert evaluate_drift_alerts([_drift_row("plan", "new_category_count", 0.0, "stable")]) == []
    severity, _, _ = evaluate_drift_alerts([_drift_row("plan", "new_category_count", 1.0, "warning")])[0]
    assert severity == "WARNING"


def _performance_row(metric_name: str, reference: float, current: float) -> PerformanceResult:
    return PerformanceResult(
        monitoring_run_id=1, metric_name=metric_name, reference_value=reference, current_value=current,
    )


def test_performance_degradation_severity_scales_with_drop_size():
    mild_drop = [_performance_row("f1", 0.80, 0.74)]
    severe_drop = [_performance_row("f1", 0.80, 0.60)]

    mild_severity, _, _ = evaluate_performance_alerts(mild_drop, degradation_threshold=0.05)[0]
    severe_severity, _, _ = evaluate_performance_alerts(severe_drop, degradation_threshold=0.05)[0]

    assert mild_severity == "WARNING"
    assert severe_severity == "CRITICAL"


def test_performance_improvement_produces_no_alert():
    rows = [_performance_row("f1", 0.70, 0.85)]
    assert evaluate_performance_alerts(rows, degradation_threshold=0.05) == []
