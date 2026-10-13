from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MonitoringRunRequest(BaseModel):
    reference_dataset_id: int
    current_dataset_id: int
    model_id: int | None = None


class MonitoringRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    reference_dataset_id: int
    current_dataset_id: int
    model_id: int | None
    status: str
    started_at: datetime
    completed_at: datetime | None


class DriftResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monitoring_run_id: int
    feature_name: str
    metric_name: str
    metric_value: float
    status: str
    created_at: datetime


class MonitoringRunSummary(BaseModel):
    id: int
    status: str
    started_at: datetime
    completed_at: datetime | None
    reference_dataset_name: str
    current_dataset_name: str
    model_name: str | None
    drifted_feature_count: int
    alert_count: int
