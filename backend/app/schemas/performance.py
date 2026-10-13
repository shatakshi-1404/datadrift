from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.performance_result import PerformanceResult


class PerformanceResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monitoring_run_id: int
    metric_name: str
    reference_value: float
    current_value: float
    change: float  # current_value - reference_value; positive = improved
    status: str  # "improved" | "stable" | "degraded", derived at read time
    created_at: datetime


def classify_performance_change(change: float, degradation_threshold: float) -> str:
    if change <= -degradation_threshold:
        return "degraded"
    if change >= degradation_threshold:
        return "improved"
    return "stable"


def performance_result_to_read(row: PerformanceResult, degradation_threshold: float) -> PerformanceResultRead:
    change = round(row.current_value - row.reference_value, 4)
    status = classify_performance_change(change, degradation_threshold)

    return PerformanceResultRead(
        id=row.id,
        monitoring_run_id=row.monitoring_run_id,
        metric_name=row.metric_name,
        reference_value=row.reference_value,
        current_value=row.current_value,
        change=change,
        status=status,
        created_at=row.created_at,
    )
