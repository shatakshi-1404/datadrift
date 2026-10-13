import json
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.drift.categorical import (
    InsufficientDataError as CategoricalInsufficientDataError,
    align_category_counts,
    categorical_psi,
    chi_square_test,
    detect_new_categories,
)
from app.drift.numeric import InsufficientDataError as KsInsufficientDataError, ks_test
from app.drift.psi import InsufficientDataError as PsiInsufficientDataError, numeric_psi
from app.ml.evaluate import evaluate_classifier
from app.ml.predict import predict
from app.models.alert import Alert
from app.models.dataset import Dataset
from app.models.drift_result import DriftResult
from app.models.monitoring_run import MonitoringRun
from app.models.performance_result import PerformanceResult
from app.quality.checks import check_constant_columns, check_duplicates, check_missing_values
from app.schemas.monitoring import MonitoringRunSummary
from app.services import alert_service, dataset_service, profiling_service, training_service
from app.services.profiling_service import infer_feature_type

PERFORMANCE_METRIC_NAMES = ("accuracy", "precision", "recall", "f1", "roc_auc")


class MonitoringValidationError(Exception):
    """The requested monitoring run cannot be executed as specified."""


def _validate_dataset(db: Session, project_id: int, dataset_id: int, role: str) -> Dataset:
    dataset = dataset_service.get_dataset(db, dataset_id)
    if dataset is None or dataset.project_id != project_id:
        raise MonitoringValidationError(f"{role} dataset {dataset_id} not found in this project.")
    return dataset


def _shared_numeric_columns(reference_df: pd.DataFrame, current_df: pd.DataFrame) -> list[str]:
    shared = [c for c in reference_df.columns if c in current_df.columns]
    return [c for c in shared if infer_feature_type(reference_df[c]) == "numeric"]


def _shared_categorical_columns(reference_df: pd.DataFrame, current_df: pd.DataFrame) -> list[str]:
    shared = [c for c in reference_df.columns if c in current_df.columns]
    return [c for c in shared if infer_feature_type(reference_df[c]) == "categorical"]


# ---------------------------------------------------------------------------
# Reusable per-"column" metric builders. feature_name and the two series
# don't have to come from a real dataset column - this lets Phase 11 reuse
# them for a model's predicted_class / predicted_probability.
# ---------------------------------------------------------------------------


def _numeric_metric_rows(
    run_id: int, feature_name: str, reference: pd.Series, current: pd.Series, settings
) -> list[DriftResult]:
    results: list[DriftResult] = []

    try:
        ks_outcome = ks_test(reference, current, settings.ks_pvalue_threshold)
        results.append(
            DriftResult(
                monitoring_run_id=run_id,
                feature_name=feature_name,
                metric_name="ks_statistic",
                metric_value=ks_outcome["statistic"],
                status=ks_outcome["status"],
            )
        )
        results.append(
            DriftResult(
                monitoring_run_id=run_id,
                feature_name=feature_name,
                metric_name="ks_pvalue",
                metric_value=ks_outcome["p_value"],
                status="info",
            )
        )
    except KsInsufficientDataError:
        pass

    try:
        psi_outcome = numeric_psi(
            reference,
            current,
            buckets=settings.psi_buckets,
            warning_threshold=settings.psi_warning_threshold,
            drift_threshold=settings.psi_drift_threshold,
        )
        results.append(
            DriftResult(
                monitoring_run_id=run_id,
                feature_name=feature_name,
                metric_name="psi",
                metric_value=psi_outcome["psi"],
                status=psi_outcome["status"],
            )
        )
    except PsiInsufficientDataError:
        pass

    return results


def _categorical_metric_rows(
    run_id: int, feature_name: str, reference: pd.Series, current: pd.Series, settings
) -> list[DriftResult]:
    try:
        reference_counts, current_counts = align_category_counts(reference, current)
    except CategoricalInsufficientDataError:
        return []

    results: list[DriftResult] = []

    chi2_outcome = chi_square_test(reference_counts, current_counts, settings.chi2_pvalue_threshold)
    results.append(
        DriftResult(
            monitoring_run_id=run_id,
            feature_name=feature_name,
            metric_name="chi2_statistic",
            metric_value=chi2_outcome["statistic"],
            status=chi2_outcome["status"],
        )
    )
    results.append(
        DriftResult(
            monitoring_run_id=run_id,
            feature_name=feature_name,
            metric_name="chi2_pvalue",
            metric_value=chi2_outcome["p_value"],
            status="info",
        )
    )

    psi_outcome = categorical_psi(
        reference_counts, current_counts, settings.psi_warning_threshold, settings.psi_drift_threshold
    )
    results.append(
        DriftResult(
            monitoring_run_id=run_id,
            feature_name=feature_name,
            metric_name="psi",
            metric_value=psi_outcome["psi"],
            status=psi_outcome["status"],
        )
    )

    new_categories = detect_new_categories(reference, current)
    results.append(
        DriftResult(
            monitoring_run_id=run_id,
            feature_name=feature_name,
            metric_name="new_category_count",
            metric_value=float(len(new_categories)),
            status="warning" if new_categories else "stable",
        )
    )

    return results


def _numeric_drift_results(
    run_id: int, reference_df: pd.DataFrame, current_df: pd.DataFrame, settings
) -> list[DriftResult]:
    results: list[DriftResult] = []
    for column in _shared_numeric_columns(reference_df, current_df):
        results += _numeric_metric_rows(run_id, column, reference_df[column], current_df[column], settings)
    return results


def _categorical_drift_results(
    run_id: int, reference_df: pd.DataFrame, current_df: pd.DataFrame, settings
) -> list[DriftResult]:
    results: list[DriftResult] = []
    for column in _shared_categorical_columns(reference_df, current_df):
        results += _categorical_metric_rows(
            run_id, column, reference_df[column], current_df[column], settings
        )
    return results


def _quality_drift_results(
    run_id: int, reference_df: pd.DataFrame, current_df: pd.DataFrame, settings
) -> list[DriftResult]:
    reference_profile = profiling_service.profile_dataframe(reference_df)
    current_profile = profiling_service.profile_dataframe(current_df)

    results: list[DriftResult] = []

    for item in check_missing_values(
        reference_profile,
        current_profile,
        settings.missing_increase_warning_threshold,
        settings.missing_increase_critical_threshold,
    ):
        results.append(
            DriftResult(
                monitoring_run_id=run_id,
                feature_name=item["feature"],
                metric_name="missing_percentage_increase",
                metric_value=item["increase"],
                status=item["status"],
            )
        )

    duplicates = check_duplicates(
        current_profile, settings.duplicate_warning_threshold, settings.duplicate_critical_threshold
    )
    results.append(
        DriftResult(
            monitoring_run_id=run_id,
            feature_name="__dataset__",
            metric_name="duplicate_percentage",
            metric_value=duplicates["percentage"],
            status=duplicates["status"],
        )
    )

    for column in check_constant_columns(current_profile):
        results.append(
            DriftResult(
                monitoring_run_id=run_id,
                feature_name=column,
                metric_name="constant_column",
                metric_value=1.0,
                status="warning",
            )
        )

    return results


def _prediction_drift_results(
    run_id: int, model, reference_df: pd.DataFrame, current_df: pd.DataFrame, settings
) -> list[DriftResult]:
    feature_columns = json.loads(model.feature_columns)
    missing = [
        c for c in feature_columns if c not in reference_df.columns or c not in current_df.columns
    ]
    if missing:
        raise MonitoringValidationError(
            f"Model {model.id} needs columns {missing} not present in both selected datasets."
        )

    pipeline = training_service.load_pipeline(model)
    reference_class, reference_proba = predict(pipeline, reference_df[feature_columns])
    current_class, current_proba = predict(pipeline, current_df[feature_columns])

    results = _numeric_metric_rows(run_id, "predicted_probability", reference_proba, current_proba, settings)
    results += _categorical_metric_rows(run_id, "predicted_class", reference_class, current_class, settings)
    return results


def _current_performance_metrics(model, current_df: pd.DataFrame) -> dict | None:
    """
    Returns real classification metrics computed on current_df's labeled
    rows, or None if no usable ground truth is available yet.
    """
    if model.target_column not in current_df.columns:
        return None

    labeled = current_df.dropna(subset=[model.target_column])
    if labeled.empty:
        return None

    y = labeled[model.target_column].astype(int)
    if y.nunique() < 2:
        return None

    feature_columns = json.loads(model.feature_columns)
    missing = [c for c in feature_columns if c not in labeled.columns]
    if missing:
        raise MonitoringValidationError(
            f"Model {model.id} needs columns {missing} not present in the current dataset."
        )

    pipeline = training_service.load_pipeline(model)
    return evaluate_classifier(pipeline, labeled[feature_columns], y)


def _performance_results(run_id: int, model, current_df: pd.DataFrame) -> list[PerformanceResult]:
    current_metrics = _current_performance_metrics(model, current_df)
    if current_metrics is None:
        return []

    reference_metrics = json.loads(model.test_metrics)
    rows = []
    for metric_name in PERFORMANCE_METRIC_NAMES:
        reference_value = reference_metrics.get(metric_name)
        current_value = current_metrics.get(metric_name)
        if reference_value is None or current_value is None:
            continue
        rows.append(
            PerformanceResult(
                monitoring_run_id=run_id,
                metric_name=metric_name,
                reference_value=reference_value,
                current_value=current_value,
            )
        )
    return rows


def run_monitoring(db: Session, project_id: int, request) -> MonitoringRun:
    reference = _validate_dataset(db, project_id, request.reference_dataset_id, "Reference")
    current = _validate_dataset(db, project_id, request.current_dataset_id, "Current")

    model = None
    if request.model_id is not None:
        model = training_service.get_model(db, request.model_id)
        if model is None or model.project_id != project_id:
            raise MonitoringValidationError(f"Model {request.model_id} not found in this project.")

    reference_df = dataset_service.load_dataframe(reference)
    current_df = dataset_service.load_dataframe(current)

    run = MonitoringRun(
        project_id=project_id,
        reference_dataset_id=reference.id,
        current_dataset_id=current.id,
        model_id=model.id if model else None,
        status="running",
    )
    db.add(run)
    db.flush()  # get run.id before inserting drift_results

    settings = get_settings()
    results = _numeric_drift_results(run.id, reference_df, current_df, settings)
    results += _categorical_drift_results(run.id, reference_df, current_df, settings)
    results += _quality_drift_results(run.id, reference_df, current_df, settings)

    performance_rows: list[PerformanceResult] = []
    if model is not None:
        results += _prediction_drift_results(run.id, model, reference_df, current_df, settings)
        performance_rows = _performance_results(run.id, model, current_df)

    db.add_all(results)
    db.add_all(performance_rows)

    alerts = alert_service.generate_alerts(
        run.id, results, performance_rows, settings.performance_degradation_threshold
    )
    db.add_all(alerts)

    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


def list_runs(db: Session, project_id: int) -> list[MonitoringRun]:
    stmt = (
        select(MonitoringRun)
        .where(MonitoringRun.project_id == project_id)
        .order_by(MonitoringRun.started_at.desc(), MonitoringRun.id.desc())
    )
    return list(db.scalars(stmt))


def get_run(db: Session, run_id: int) -> MonitoringRun | None:
    return db.get(MonitoringRun, run_id)


def list_drift_results(db: Session, run_id: int, feature_name: str | None = None) -> list[DriftResult]:
    stmt = select(DriftResult).where(DriftResult.monitoring_run_id == run_id)
    if feature_name is not None:
        stmt = stmt.where(DriftResult.feature_name == feature_name)
    return list(db.scalars(stmt.order_by(DriftResult.feature_name, DriftResult.metric_name)))


def list_performance_results(db: Session, run_id: int) -> list[PerformanceResult]:
    stmt = (
        select(PerformanceResult)
        .where(PerformanceResult.monitoring_run_id == run_id)
        .order_by(PerformanceResult.metric_name)
    )
    return list(db.scalars(stmt))


def list_alerts(db: Session, run_id: int) -> list[Alert]:
    stmt = (
        select(Alert)
        .where(Alert.monitoring_run_id == run_id)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
    )
    return list(db.scalars(stmt))


def list_recent_alerts(db: Session, project_id: int, limit: int = 20) -> list[Alert]:
    stmt = (
        select(Alert)
        .join(MonitoringRun, Alert.monitoring_run_id == MonitoringRun.id)
        .where(MonitoringRun.project_id == project_id)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def _build_run_summary(db: Session, run: MonitoringRun) -> MonitoringRunSummary:
    reference = dataset_service.get_dataset(db, run.reference_dataset_id)
    current = dataset_service.get_dataset(db, run.current_dataset_id)
    model = training_service.get_model(db, run.model_id) if run.model_id else None

    drift_results = list_drift_results(db, run.id)
    drifted_features = {
        r.feature_name
        for r in drift_results
        if r.metric_name == "psi" and r.status == "drift" and r.feature_name != "__dataset__"
    }

    return MonitoringRunSummary(
        id=run.id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        reference_dataset_name=reference.name if reference else "(deleted)",
        current_dataset_name=current.name if current else "(deleted)",
        model_name=f"{model.name} v{model.version}" if model else None,
        drifted_feature_count=len(drifted_features),
        alert_count=len(list_alerts(db, run.id)),
    )


def list_run_summaries(db: Session, project_id: int) -> list[MonitoringRunSummary]:
    # One query per run's related lookups - simple and fast enough at
    # portfolio/small-team scale; a single joined+aggregated query would
    # be the next step if run history grew into the thousands.
    return [_build_run_summary(db, run) for run in list_runs(db, project_id)]


def get_run_summary(db: Session, run: MonitoringRun) -> MonitoringRunSummary:
    return _build_run_summary(db, run)
