import json
import uuid
from pathlib import Path

import joblib
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ml.train import TrainingError, train_logistic_regression
from app.ml.tracking import log_training_run
from app.models.model import MLModel
from app.schemas.model import ModelTrainRequest
from app.services import dataset_service, project_service

ALGORITHM = "logistic_regression"


def _next_version(db: Session, project_id: int, name: str) -> int:
    stmt = select(func.max(MLModel.version)).where(
        MLModel.project_id == project_id, MLModel.name == name
    )
    current_max = db.scalar(stmt)
    return (current_max or 0) + 1


def _save_pipeline(pipeline, project_id: int) -> Path:
    settings = get_settings()
    directory = settings.model_storage_dir / str(project_id)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid.uuid4().hex}.joblib"
    joblib.dump(pipeline, path)
    return path


def train_model(db: Session, project_id: int, request: ModelTrainRequest) -> MLModel:
    project = project_service.get_project(db, project_id)
    if project is None:
        raise TrainingError(f"Project {project_id} not found.")

    dataset = dataset_service.get_dataset(db, request.dataset_id)
    if dataset is None or dataset.project_id != project_id:
        raise TrainingError(f"Dataset {request.dataset_id} not found in this project.")
    if dataset.dataset_type != "reference":
        raise TrainingError("Models should be trained on a 'reference' dataset, not 'current'.")

    settings = get_settings()
    df = dataset_service.load_dataframe(dataset)
    result = train_logistic_regression(df, request.target_column, settings.ml_random_state)

    run_id, experiment_id = log_training_run(
        project_id=project_id,
        project_name=project.name,
        model_name=request.name,
        params={
            "algorithm": ALGORITHM,
            "target_column": request.target_column,
            "feature_columns": ",".join(result["feature_columns"]),
            "random_state": settings.ml_random_state,
            "training_dataset_id": dataset.id,
        },
        train_metrics=result["train_metrics"],
        test_metrics=result["test_metrics"],
        pipeline=result["pipeline"],
    )

    artifact_path = _save_pipeline(result["pipeline"], project_id)
    try:
        model = MLModel(
            project_id=project_id,
            training_dataset_id=dataset.id,
            name=request.name,
            version=_next_version(db, project_id, request.name),
            algorithm=ALGORITHM,
            target_column=request.target_column,
            feature_columns=json.dumps(result["feature_columns"]),
            numeric_feature_columns=json.dumps(result["numeric_features"]),
            categorical_feature_columns=json.dumps(result["categorical_features"]),
            artifact_path=str(artifact_path),
            train_metrics=json.dumps(result["train_metrics"]),
            test_metrics=json.dumps(result["test_metrics"]),
            mlflow_run_id=run_id,
            mlflow_experiment_id=experiment_id,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model
    except Exception:
        db.rollback()
        artifact_path.unlink(missing_ok=True)
        raise


def list_models(db: Session, project_id: int) -> list[MLModel]:
    stmt = (
        select(MLModel)
        .where(MLModel.project_id == project_id)
        .order_by(MLModel.created_at.desc(), MLModel.id.desc())
    )
    return list(db.scalars(stmt))


def get_model(db: Session, model_id: int) -> MLModel | None:
    return db.get(MLModel, model_id)


def load_pipeline(model: MLModel):
    """Load the fitted sklearn pipeline back from disk."""
    return joblib.load(model.artifact_path)
