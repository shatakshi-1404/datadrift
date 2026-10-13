import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers every ORM model on Base before create_all
from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture()
def temp_storage(tmp_path, monkeypatch):
    """Redirects dataset/model/MLflow storage to a throwaway temp directory per test."""
    settings = get_settings()
    monkeypatch.setattr(settings, "dataset_storage_path", str(tmp_path / "datasets"))
    monkeypatch.setattr(settings, "model_storage_path", str(tmp_path / "models"))
    monkeypatch.setattr(settings, "mlflow_tracking_uri", str(tmp_path / "mlruns"))
    return settings


@pytest.fixture()
def db_session(tmp_path):
    """A fresh, isolated SQLite database for each test - never touches real Postgres."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session, temp_storage):
    """
    A TestClient wired to the isolated SQLite session above. Deliberately
    NOT using `with TestClient(app) as c:` - that would trigger the app's
    real startup lifespan, which points at the actual configured Postgres
    database. Plain TestClient(app) skips lifespan entirely.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
