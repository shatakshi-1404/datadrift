from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MLModel(Base):
    """Named `MLModel` to avoid clashing with SQLAlchemy's own `Model` concept."""

    __tablename__ = "models"
    __table_args__ = (UniqueConstraint("project_id", "name", "version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    training_dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    target_column: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_columns: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    numeric_feature_columns: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    categorical_feature_columns: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=False)
    train_metrics: Mapped[str] = mapped_column(Text, nullable=False)  # JSON dict
    test_metrics: Mapped[str] = mapped_column(Text, nullable=False)  # JSON dict
    mlflow_run_id: Mapped[str] = mapped_column(String(100), nullable=False)
    mlflow_experiment_id: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
