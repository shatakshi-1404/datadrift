from app.core.config import get_settings
from app.drift.categorical import (
    InsufficientDataError as CategoricalInsufficientDataError,
    categorical_distribution,
)
from app.drift.numeric import InsufficientDataError as KsInsufficientDataError
from app.drift.psi import InsufficientDataError as PsiInsufficientDataError, numeric_distribution
from app.models.monitoring_run import MonitoringRun
from app.schemas.feature_detail import DistributionData, FeatureDetailResponse, FeatureStats
from app.services import dataset_service, monitoring_service, profiling_service
from app.services.profiling_service import infer_feature_type


class FeatureNotFoundError(Exception):
    """The requested feature does not exist in both datasets for this run."""


def _feature_stats(profile, feature_name: str) -> FeatureStats:
    feature = next((f for f in profile.features if f.name == feature_name), None)
    if feature is None:
        raise FeatureNotFoundError(f"Feature '{feature_name}' not found in dataset profile.")
    return FeatureStats(
        missing_count=feature.missing_count,
        missing_percentage=feature.missing_percentage,
        unique_count=feature.unique_count,
        numeric=feature.numeric,
        categorical=feature.categorical,
    )


def _interpretation(feature_name: str, feature_type: str, psi_status: str | None) -> str:
    """
    Describes the OBSERVED statistical change only - never a claim about
    model correctness or business impact.
    """
    kind = "numeric" if feature_type == "numeric" else "categorical"
    if psi_status is None:
        return f"Not enough data was available to compare '{feature_name}' between datasets."
    if psi_status == "stable":
        return f"The current distribution of '{feature_name}' is consistent with the reference distribution."
    if psi_status == "warning":
        return (
            f"The current distribution of '{feature_name}' ({kind}) shows a moderate difference "
            "from the reference distribution."
        )
    return (
        f"The current distribution of '{feature_name}' ({kind}) differs significantly "
        "from the reference distribution."
    )


def get_feature_detail(db, run: MonitoringRun, feature_name: str) -> FeatureDetailResponse:
    reference_dataset = dataset_service.get_dataset(db, run.reference_dataset_id)
    current_dataset = dataset_service.get_dataset(db, run.current_dataset_id)
    reference_df = dataset_service.load_dataframe(reference_dataset)
    current_df = dataset_service.load_dataframe(current_dataset)

    if feature_name not in reference_df.columns or feature_name not in current_df.columns:
        raise FeatureNotFoundError(f"Feature '{feature_name}' not found in this run's datasets.")

    feature_type = infer_feature_type(reference_df[feature_name])
    settings = get_settings()

    try:
        if feature_type == "numeric":
            raw_distribution = numeric_distribution(
                reference_df[feature_name], current_df[feature_name], settings.psi_buckets
            )
        else:
            raw_distribution = categorical_distribution(reference_df[feature_name], current_df[feature_name])
    except (PsiInsufficientDataError, CategoricalInsufficientDataError, KsInsufficientDataError):
        raw_distribution = {"labels": [], "reference_percentage": [], "current_percentage": []}

    distribution = DistributionData(
        labels=raw_distribution["labels"],
        reference_percentage=raw_distribution["reference_percentage"],
        current_percentage=raw_distribution["current_percentage"],
    )

    reference_profile = profiling_service.profile_dataframe(reference_df)
    current_profile = profiling_service.profile_dataframe(current_df)

    metrics = monitoring_service.list_drift_results(db, run.id, feature_name)
    psi_row = next((m for m in metrics if m.metric_name == "psi"), None)

    return FeatureDetailResponse(
        feature_name=feature_name,
        feature_type=feature_type,
        reference=_feature_stats(reference_profile, feature_name),
        current=_feature_stats(current_profile, feature_name),
        distribution=distribution,
        metrics=metrics,
        interpretation=_interpretation(feature_name, feature_type, psi_row.status if psi_row else None),
    )
