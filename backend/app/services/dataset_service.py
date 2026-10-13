import csv
import uuid
from pathlib import Path

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.models.dataset_feature import DatasetFeature
from app.schemas.dataset import DatasetType
from app.schemas.profile import DatasetProfile
from app.services import profiling_service

CHUNK_SIZE = 1024 * 1024  # 1 MB
MAX_COLUMNS = 200
ALLOWED_EXTENSION = ".csv"


class DatasetValidationError(Exception):
    """The uploaded file is not an acceptable dataset."""


class FileTooLargeError(Exception):
    """The uploaded file exceeds MAX_UPLOAD_SIZE."""


class DatasetFileMissingError(Exception):
    """The dataset row exists but its file is gone from disk."""


def _save_upload(file: UploadFile, project_id: int) -> Path:
    """Stream the upload to disk under a server-generated name."""
    settings = get_settings()
    directory = settings.dataset_storage_dir / str(project_id)
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / f"{uuid.uuid4().hex}{ALLOWED_EXTENSION}"
    written = 0
    try:
        with path.open("wb") as out:
            while chunk := file.file.read(CHUNK_SIZE):
                written += len(chunk)
                if written > settings.max_upload_size:
                    limit_mb = settings.max_upload_size // (1024 * 1024)
                    raise FileTooLargeError(f"File exceeds the {limit_mb} MB limit.")
                out.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def _validate_header(path: Path) -> None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            header = next(csv.reader(f), None)
    except UnicodeDecodeError:
        raise DatasetValidationError("File must be UTF-8 encoded text.")

    if not header:
        raise DatasetValidationError("File is empty.")

    names = [h.strip() for h in header]
    if any(n == "" for n in names):
        raise DatasetValidationError("Header contains an empty column name.")
    if len(set(names)) != len(names):
        raise DatasetValidationError("Header contains duplicate column names.")
    if len(names) > MAX_COLUMNS:
        raise DatasetValidationError(f"Too many columns (max {MAX_COLUMNS}).")


def _validate_csv(path: Path) -> pd.DataFrame:
    """Return the parsed DataFrame or raise DatasetValidationError."""
    _validate_header(path)
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise DatasetValidationError("File must be UTF-8 encoded text.")
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        raise DatasetValidationError("File could not be parsed as a valid CSV.")

    if len(df) == 0:
        raise DatasetValidationError("CSV contains a header but no data rows.")
    return df


def _display_name(name: str | None, filename: str | None) -> str:
    """Filename is only a label, never a path."""
    candidate = (name or "").strip() or Path(filename or "dataset").stem
    return candidate[:100] or "dataset"


def _feature_rows(dataset_id: int, profile: DatasetProfile) -> list[DatasetFeature]:
    return [
        DatasetFeature(
            dataset_id=dataset_id,
            feature_name=f.name,
            data_type=f.data_type,
            missing_count=f.missing_count,
            missing_percentage=f.missing_percentage,
            unique_count=f.unique_count,
        )
        for f in profile.features
    ]


def create_dataset(
    db: Session,
    project_id: int,
    file: UploadFile,
    dataset_type: DatasetType,
    name: str | None,
) -> Dataset:
    if Path(file.filename or "").suffix.lower() != ALLOWED_EXTENSION:
        raise DatasetValidationError("Only .csv files are allowed.")

    path = _save_upload(file, project_id)
    try:
        df = _validate_csv(path)
        profile = profiling_service.profile_dataframe(df)

        dataset = Dataset(
            project_id=project_id,
            name=_display_name(name, file.filename),
            dataset_type=dataset_type.value,
            file_path=str(path),
            rows=profile.rows,
            columns=profile.columns,
        )
        db.add(dataset)
        db.flush()  # sends the INSERT so dataset.id exists, still uncommitted
        db.add_all(_feature_rows(dataset.id, profile))
        db.commit()  # dataset + features saved together, or not at all
        db.refresh(dataset)
        return dataset
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise


def list_datasets(db: Session, project_id: int) -> list[Dataset]:
    stmt = (
        select(Dataset)
        .where(Dataset.project_id == project_id)
        .order_by(Dataset.created_at.desc(), Dataset.id.desc())
    )
    return list(db.scalars(stmt))


def get_dataset(db: Session, dataset_id: int) -> Dataset | None:
    return db.get(Dataset, dataset_id)


def delete_dataset(db: Session, dataset: Dataset) -> None:
    path = Path(dataset.file_path)
    path.unlink(missing_ok=True)
    db.delete(dataset)
    db.commit()


def list_features(db: Session, dataset_id: int) -> list[DatasetFeature]:
    stmt = (
        select(DatasetFeature)
        .where(DatasetFeature.dataset_id == dataset_id)
        .order_by(DatasetFeature.id)
    )
    return list(db.scalars(stmt))


def load_dataframe(dataset: Dataset) -> pd.DataFrame:
    """Read a stored dataset back from disk (reused throughout later phases)."""
    path = Path(dataset.file_path)
    if not path.is_file():
        raise DatasetFileMissingError(f"File for dataset {dataset.id} is missing.")
    return pd.read_csv(path, encoding="utf-8-sig")


def profile_dataset(dataset: Dataset) -> DatasetProfile:
    return profiling_service.profile_dataframe(load_dataframe(dataset))


def get_dataset_by_id_unchecked(dataset_id: int) -> Dataset:
    """
    Used internally (e.g. by SHAP's background-data loader) where the
    caller already trusts dataset_id - unlike get_dataset, this raises
    instead of returning None, since a model's own training_dataset_id
    should always resolve to a real, undeleted dataset.
    """
    from app.core.database import SessionLocal  # local import avoids a circular dependency

    with SessionLocal() as db:
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise DatasetFileMissingError(f"Training dataset {dataset_id} no longer exists.")
        return dataset
