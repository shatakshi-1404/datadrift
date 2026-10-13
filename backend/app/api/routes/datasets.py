from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetRead, DatasetType
from app.schemas.profile import DatasetFeatureRead, DatasetProfile
from app.services import dataset_service, project_service
from app.services.dataset_service import (
    DatasetFileMissingError,
    DatasetValidationError,
    FileTooLargeError,
)

router = APIRouter(tags=["datasets"])


def _require_project(db: Session, project_id: int) -> None:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )


def _get_dataset_or_404(db: Session, dataset_id: int) -> Dataset:
    dataset = dataset_service.get_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found",
        )
    return dataset


@router.post(
    "/api/projects/{project_id}/datasets/upload",
    response_model=DatasetRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_dataset(
    project_id: int,
    file: UploadFile = File(...),
    dataset_type: DatasetType = Form(...),
    name: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    _require_project(db, project_id)
    try:
        return dataset_service.create_dataset(db, project_id, file, dataset_type, name)
    except FileTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except DatasetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/api/projects/{project_id}/datasets", response_model=list[DatasetRead])
def list_datasets(project_id: int, db: Session = Depends(get_db)):
    _require_project(db, project_id)
    return dataset_service.list_datasets(db, project_id)


@router.get("/api/datasets/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    return _get_dataset_or_404(db, dataset_id)


@router.delete("/api/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset_or_404(db, dataset_id)
    dataset_service.delete_dataset(db, dataset)


@router.get("/api/datasets/{dataset_id}/features", response_model=list[DatasetFeatureRead])
def list_dataset_features(dataset_id: int, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    return dataset_service.list_features(db, dataset_id)


@router.get("/api/datasets/{dataset_id}/profile", response_model=DatasetProfile)
def get_dataset_profile(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset_or_404(db, dataset_id)
    try:
        return dataset_service.profile_dataset(dataset)
    except DatasetFileMissingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
