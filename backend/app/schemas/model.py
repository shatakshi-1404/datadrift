import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.model import MLModel


class ModelTrainRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    dataset_id: int
    target_column: str = Field(min_length=1, max_length=100)
    name: str = Field(default="churn_baseline", min_length=1, max_length=100)


class ClassificationMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float | None  # None if only one class is present to score against


class ModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    training_dataset_id: int
    name: str
    version: int
    algorithm: str
    target_column: str
    feature_columns: list[str]
    train_metrics: ClassificationMetrics
    test_metrics: ClassificationMetrics
    mlflow_run_id: str
    mlflow_experiment_id: str
    created_at: datetime


def model_to_read(model: MLModel) -> ModelRead:
    return ModelRead(
        id=model.id,
        project_id=model.project_id,
        training_dataset_id=model.training_dataset_id,
        name=model.name,
        version=model.version,
        algorithm=model.algorithm,
        target_column=model.target_column,
        feature_columns=json.loads(model.feature_columns),
        train_metrics=ClassificationMetrics(**json.loads(model.train_metrics)),
        test_metrics=ClassificationMetrics(**json.loads(model.test_metrics)),
        mlflow_run_id=model.mlflow_run_id,
        mlflow_experiment_id=model.mlflow_experiment_id,
        created_at=model.created_at,
    )
