from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py -> core -> app -> backend -> project root
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "DataDrift"
    app_env: str = "development"
    database_url: str
    cors_origins: str = "http://localhost:5173"
    dataset_storage_path: str = "storage/datasets"
    max_upload_size: int = 20 * 1024 * 1024  # bytes
    model_storage_path: str = "storage/models"
    ml_random_state: int = 42
    mlflow_tracking_uri: str = "mlruns"
    ks_pvalue_threshold: float = 0.05
    psi_warning_threshold: float = 0.1
    psi_drift_threshold: float = 0.25
    psi_buckets: int = 10
    chi2_pvalue_threshold: float = 0.05
    missing_increase_warning_threshold: float = 5.0
    missing_increase_critical_threshold: float = 15.0
    duplicate_warning_threshold: float = 1.0
    duplicate_critical_threshold: float = 5.0
    performance_degradation_threshold: float = 0.05
    shap_background_sample_size: int = 200

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def dataset_storage_dir(self) -> Path:
        path = Path(self.dataset_storage_path)
        return path if path.is_absolute() else ROOT_DIR / path

    @property
    def model_storage_dir(self) -> Path:
        path = Path(self.model_storage_path)
        return path if path.is_absolute() else ROOT_DIR / path

    @property
    def mlflow_tracking_dir(self) -> Path:
        path = Path(self.mlflow_tracking_uri)
        return path if path.is_absolute() else ROOT_DIR / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
