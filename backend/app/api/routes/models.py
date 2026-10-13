from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.explainability.shap_service import (
    ExplainabilityValidationError,
    explain_prediction,
    global_importance,
)
from app.ml.train import TrainingError
from app.schemas.explainability import ExplainabilityResponse
from app.schemas.model import ModelRead, ModelTrainRequest, model_to_read
from app.services import dataset_service, project_service, training_service

router = APIRouter(tags=["models"])


def _require_project(db: Session, project_id: int) -> None:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )


@router.post(
    "/api/projects/{project_id}/models/train",
    response_model=ModelRead,
    status_code=status.HTTP_201_CREATED,
)
def train_model(project_id: int, request: ModelTrainRequest, db: Session = Depends(get_db)):
    _require_project(db, project_id)
    try:
        model = training_service.train_model(db, project_id, request)
    except TrainingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return model_to_read(model)


@router.get("/api/projects/{project_id}/models", response_model=list[ModelRead])
def list_models(project_id: int, db: Session = Depends(get_db)):
    _require_project(db, project_id)
    return [model_to_read(m) for m in training_service.list_models(db, project_id)]


@router.get("/api/models/{model_id}", response_model=ModelRead)
def get_model(model_id: int, db: Session = Depends(get_db)):
    model = training_service.get_model(db, model_id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found",
        )
    return model_to_read(model)


@router.get("/api/models/{model_id}/explainability", response_model=ExplainabilityResponse)
def get_model_explainability(
    model_id: int,
    dataset_id: int | None = None,
    row_index: int | None = None,
    db: Session = Depends(get_db),
):
    model = training_service.get_model(db, model_id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Model {model_id} not found"
        )

    response = ExplainabilityResponse(
        model_id=model.id, global_importance=global_importance(model)
    )

    if dataset_id is not None and row_index is not None:
        dataset = dataset_service.get_dataset(db, dataset_id)
        if dataset is None or dataset.project_id != model.project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found in this project",
            )
        try:
            response.local = explain_prediction(model, dataset, row_index)
        except ExplainabilityValidationError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return response
