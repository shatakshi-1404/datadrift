from typing import Literal

from pydantic import BaseModel, ConfigDict


class NumericStats(BaseModel):
    min: float | None
    max: float | None
    mean: float | None
    median: float | None
    std: float | None


class CategoryFrequency(BaseModel):
    value: str
    count: int
    percentage: float  # share of non-missing values


class CategoricalStats(BaseModel):
    unique_categories: int
    top_categories: list[CategoryFrequency]


class FeatureProfile(BaseModel):
    name: str
    data_type: str  # pandas dtype, e.g. "int64", "object"
    feature_type: Literal["numeric", "categorical"]
    missing_count: int
    missing_percentage: float
    unique_count: int
    numeric: NumericStats | None = None
    categorical: CategoricalStats | None = None


class DatasetProfile(BaseModel):
    rows: int
    columns: int
    duplicate_rows: int
    duplicate_percentage: float
    total_missing_cells: int
    features: list[FeatureProfile]


class DatasetFeatureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    feature_name: str
    data_type: str
    missing_count: int
    missing_percentage: float
    unique_count: int
