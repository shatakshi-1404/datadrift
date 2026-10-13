from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DatasetType(str, Enum):
    reference = "reference"
    current = "current"


class DatasetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    dataset_type: DatasetType
    rows: int
    columns: int
    created_at: datetime
