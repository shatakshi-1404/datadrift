from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.alert import AlertRead
from app.schemas.feature_detail import FeatureDetailResponse
from app.schemas.monitoring import (
    DriftResultRead,
    MonitoringRunRead,
    MonitoringRunRequest,
    MonitoringRunSummary,
)
from app.schemas.performance import PerformanceResultRead, performance_result_to_read
from app.services import monitoring_service, project_service
from app.services.feature_detail_service import FeatureNotFoundError, get_feature_detail
from app.services.monitoring_service import MonitoringValidationError

router = APIRouter(tags=["monitoring"])


def _require_project(db: Session, project_id: int) -> None:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )


def _get_run_or_404(db: Session, run_id: int):
    run = monitoring_service.get_run(db, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitoring run {run_id} not found",
        )
    return run


@router.post(
    "/api/projects/{project_id}/monitoring/run",
    response_model=MonitoringRunRead,
    status_code=status.HTTP_201_CREATED,
)
def run_monitoring(project_id: int, request: MonitoringRunRequest, db: Session = Depends(get_db)):
    _require_project(db, project_id)
    try:
        return monitoring_service.run_monitoring(db, project_id, request)
    except MonitoringValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/api/projects/{project_id}/monitoring", response_model=list[MonitoringRunRead])
def list_monitoring_runs(project_id: int, db: Session = Depends(get_db)):
    _require_project(db, project_id)
    return monitoring_service.list_runs(db, project_id)


@router.get(
    "/api/projects/{project_id}/monitoring/history", response_model=list[MonitoringRunSummary]
)
def get_monitoring_history(project_id: int, db: Session = Depends(get_db)):
    _require_project(db, project_id)
    return monitoring_service.list_run_summaries(db, project_id)


@router.get("/api/monitoring/{run_id}", response_model=MonitoringRunRead)
def get_monitoring_run(run_id: int, db: Session = Depends(get_db)):
    return _get_run_or_404(db, run_id)


@router.get("/api/monitoring/{run_id}/summary", response_model=MonitoringRunSummary)
def get_run_summary(run_id: int, db: Session = Depends(get_db)):
    run = _get_run_or_404(db, run_id)
    return monitoring_service.get_run_summary(db, run)


@router.get("/api/monitoring/{run_id}/drift", response_model=list[DriftResultRead])
def get_drift_results(run_id: int, db: Session = Depends(get_db)):
    _get_run_or_404(db, run_id)
    return monitoring_service.list_drift_results(db, run_id)


@router.get("/api/monitoring/{run_id}/drift/{feature_name}", response_model=list[DriftResultRead])
def get_feature_drift(run_id: int, feature_name: str, db: Session = Depends(get_db)):
    _get_run_or_404(db, run_id)
    results = monitoring_service.list_drift_results(db, run_id, feature_name)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No drift results for feature '{feature_name}' in run {run_id}",
        )
    return results


@router.get(
    "/api/monitoring/{run_id}/features/{feature_name}", response_model=FeatureDetailResponse
)
def get_feature_detail_view(run_id: int, feature_name: str, db: Session = Depends(get_db)):
    run = _get_run_or_404(db, run_id)
    try:
        return get_feature_detail(db, run, feature_name)
    except FeatureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/api/monitoring/{run_id}/performance", response_model=list[PerformanceResultRead])
def get_performance_results(run_id: int, db: Session = Depends(get_db)):
    _get_run_or_404(db, run_id)
    settings = get_settings()
    rows = monitoring_service.list_performance_results(db, run_id)
    return [performance_result_to_read(row, settings.performance_degradation_threshold) for row in rows]


@router.get("/api/monitoring/{run_id}/alerts", response_model=list[AlertRead])
def get_run_alerts(run_id: int, db: Session = Depends(get_db)):
    _get_run_or_404(db, run_id)
    return monitoring_service.list_alerts(db, run_id)


@router.get("/api/projects/{project_id}/alerts", response_model=list[AlertRead])
def get_project_alerts(project_id: int, db: Session = Depends(get_db)):
    _require_project(db, project_id)
    return monitoring_service.list_recent_alerts(db, project_id)
