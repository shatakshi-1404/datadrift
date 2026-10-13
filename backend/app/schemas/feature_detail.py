from pydantic import BaseModel

from app.schemas.monitoring import DriftResultRead
from app.schemas.profile import CategoricalStats, NumericStats


class DistributionData(BaseModel):
    labels: list[str]
    reference_percentage: list[float]
    current_percentage: list[float]


class FeatureStats(BaseModel):
    missing_count: int
    missing_percentage: float
    unique_count: int
    numeric: NumericStats | None = None
    categorical: CategoricalStats | None = None


class FeatureDetailResponse(BaseModel):
    feature_name: str
    feature_type: str  # "numeric" | "categorical"
    reference: FeatureStats
    current: FeatureStats
    distribution: DistributionData
    metrics: list[DriftResultRead]
    interpretation: str
