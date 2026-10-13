# DataDrift

**An ML model monitoring and data drift platform** that detects changes in production data, monitors model performance, tracks data quality, and explains model predictions.

> DataDrift answers one question: **"What changed in my ML data, and is that change affecting my model?"**

---

## Overview

Machine learning models are usually evaluated once, at training time, and then deployed and forgotten. In the real world, the data a model sees in production drifts away from what it was trained on. DataDrift is a self-contained platform for detecting that drift, distinguishing it from actual model performance degradation, and explaining what the model is doing along the way.

The initial use case is customer churn classification, using a clearly-labeled **synthetic** dataset (`scripts/generate_synthetic_data.py`).

**Core design principle: drift and model performance degradation are different things.** The platform never claims one causes the other — it reports both, independently measured.

## Features

- Project-based organization; CSV dataset upload with validation
- Reference vs. current dataset distinction; automated dataset profiling
- Logistic Regression training pipeline with real train/test metrics
- MLflow experiment tracking (parameters, metrics, model artifacts)
- Numerical drift: KS test + PSI. Categorical drift: chi-square + PSI + new-category detection
- Data quality checks: missing-value increases, duplicates, constant columns
- Prediction drift (drift tools applied to the model's own output)
- Model performance monitoring against ground-truth labels, when available
- Rule-based alert engine (INFO/WARNING/CRITICAL)
- SHAP-based explainability (global + local)
- React/TypeScript dashboard, feature detail pages, monitoring history
- FastAPI REST API, PostgreSQL, pytest suite, full Docker packaging

## Architecture

```
            ┌──────────────────┐
            │      React       │
            │   Dashboard      │
            └────────┬─────────┘
                      │  REST (JSON)
                      ▼
            ┌──────────────────┐
            │     FastAPI      │
            │      API         │
            └────────┬─────────┘
                      │
     ┌────────────────┼─────────────────┐
     │                │                 │
     ▼                ▼                 ▼
PostgreSQL      ML Services       Monitoring
(projects,      (train, predict,  (drift, quality,
 datasets,       evaluate)         prediction, perf.)
 models,              │                 │
 runs, results)       │            ┌────┴────┐
                       │            │         │
                       ▼         Alerts     SHAP
                   MLflow      (rule-based) (explain)
                (tracking)
```

Layered backend: **routes** (HTTP only) → **services** (business logic + DB) → **ml/ drift/ quality/ explainability/** (pure, independently-testable functions with no DB/HTTP knowledge).

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS, Recharts, React Router |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL |
| ML | pandas, NumPy, scikit-learn |
| Experiment tracking | MLflow |
| Explainability | SHAP |
| Infrastructure | Docker, Docker Compose |
| Testing | pytest |

## Getting Started

### Option A: Docker (recommended)

```bash
cp .env.example .env    # edit POSTGRES_PASSWORD at minimum
docker compose up --build
```
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- MLflow UI: http://localhost:5001

### Option B: Manual local setup

```bash
# Database
docker compose up -d db

# Backend
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev

# Generate synthetic data (optional, one-time)
python scripts/generate_synthetic_data.py
```

## Environment Variables

See `.env.example` for the full template with defaults for every drift/quality/performance threshold (all configurable, not hardcoded — see Limitations).

## API Reference

| Resource | Endpoints |
|---|---|
| Health | `GET /health` |
| Projects | `POST /api/projects`, `GET /api/projects`, `GET /api/projects/{id}` |
| Datasets | `POST /api/projects/{id}/datasets/upload`, `GET /api/projects/{id}/datasets`, `GET /api/datasets/{id}`, `DELETE /api/datasets/{id}`, `GET /api/datasets/{id}/profile`, `GET /api/datasets/{id}/features` |
| Models | `POST /api/projects/{id}/models/train`, `GET /api/projects/{id}/models`, `GET /api/models/{id}`, `GET /api/models/{id}/explainability` |
| Monitoring | `POST /api/projects/{id}/monitoring/run`, `GET /api/projects/{id}/monitoring`, `GET /api/projects/{id}/monitoring/history`, `GET /api/monitoring/{id}`, `GET /api/monitoring/{id}/summary` |
| Drift | `GET /api/monitoring/{id}/drift`, `GET /api/monitoring/{id}/drift/{feature}`, `GET /api/monitoring/{id}/features/{feature}` |
| Performance | `GET /api/monitoring/{id}/performance` |
| Alerts | `GET /api/monitoring/{id}/alerts`, `GET /api/projects/{id}/alerts` |

Full interactive docs at `/docs` while the backend is running.

## ML Pipeline

1. Preprocessing: numeric = median-impute + scale; categorical = most-frequent-impute + one-hot (`handle_unknown="ignore"`)
2. Model: Logistic Regression — fast, interpretable, exact SHAP support
3. Persistence: the whole fitted pipeline saved as one artifact
4. Tracking: every run logged to MLflow (one experiment per project)

## Drift Detection Methodology

| Signal | Method | Measures |
|---|---|---|
| Numerical shape | Kolmogorov-Smirnov | Statistical significance |
| Numerical/categorical magnitude | PSI | Size of the shift |
| Categorical shift | Chi-square goodness-of-fit | Statistical significance |
| New categories | Set difference | Categories never seen in reference |
| Prediction drift | Same tools on model output | — |

PSI thresholds (< 0.1 stable, 0.1–0.25 moderate, > 0.25 significant) are an industry convention, not a law — hence fully configurable.

## Testing

```bash
cd backend
pytest -v
```
Runs against an isolated in-memory SQLite database; needs no running Postgres or Docker.

## Docker

```bash
docker compose up --build
```
Runs PostgreSQL, FastAPI, the React frontend (nginx), and an MLflow UI — sharing the same `storage/`/`mlruns/` folders as local dev.

## Limitations

- Statistical drift does not automatically imply business impact or model failure
- Correlation between drift and a performance change is not established causation
- All severity thresholds are configurable defaults, not universal constants
- Monitoring quality depends on reference data quality and representativeness
- Model performance cannot be measured until ground-truth labels arrive
- SHAP explanations describe model behavior, not causal real-world relationships
- No database migration tool (Alembic) — schema changes during development required manual table resets
- UI currently manages a single project by convention (`CURRENT_PROJECT_ID`)
- Monitoring history summaries use a simple per-run query pattern, not one optimized joined query
- No automated alert delivery (email/Slack)

## Future Improvements

- Alembic migrations
- Multi-project navigation
- Model comparison (Random Forest / XGBoost)
- Scheduled/automatic monitoring runs
- Real alert delivery (email, Slack webhook)
- Authentication and per-user project access

## License

MIT (or your choice)
