import re

import mlflow
import mlflow.sklearn
from sklearn.pipeline import Pipeline

from app.core.config import get_settings

_EXPERIMENT_NAME_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def _configure() -> None:
    """Point MLflow at our local tracking directory. Safe to call every time."""
    settings = get_settings()
    settings.mlflow_tracking_dir.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(settings.mlflow_tracking_dir.as_uri())


def experiment_name_for_project(project_id: int, project_name: str) -> str:
    """One MLflow experiment per DataDrift project, human-readable but safe."""
    safe_name = _EXPERIMENT_NAME_RE.sub("_", project_name.strip()) or "project"
    return f"project_{project_id}_{safe_name}"


def log_training_run(
    *,
    project_id: int,
    project_name: str,
    model_name: str,
    params: dict,
    train_metrics: dict,
    test_metrics: dict,
    pipeline: Pipeline,
) -> tuple[str, str]:
    """
    Logs one training run to MLflow and returns (run_id, experiment_id).
    Metrics with value None (e.g. roc_auc on a single-class split) are
    skipped, since MLflow only accepts numeric metric values.
    """
    _configure()
    experiment = mlflow.set_experiment(experiment_name_for_project(project_id, project_name))

    with mlflow.start_run(run_name=model_name) as run:
        mlflow.log_params(params)

        for prefix, metrics in (("train", train_metrics), ("test", test_metrics)):
            for key, value in metrics.items():
                if value is not None:
                    mlflow.log_metric(f"{prefix}_{key}", value)

        mlflow.sklearn.log_model(pipeline, artifact_path="model")

        return run.info.run_id, experiment.experiment_id
