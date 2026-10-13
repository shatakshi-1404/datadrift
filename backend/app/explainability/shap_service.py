import json

import numpy as np
import pandas as pd
import shap

from app.core.config import get_settings
from app.models.dataset import Dataset
from app.models.model import MLModel
from app.services import dataset_service, training_service


class ExplainabilityValidationError(Exception):
    """The requested explanation cannot be produced as specified."""


def _load_background(model: MLModel) -> pd.DataFrame:
    """
    Uses a sample of the model's own training dataset as SHAP's background
    (the reference point "what does this model typically see"). Using an
    unrelated dataset here would make base_value meaningless for this model.
    """
    training_dataset = dataset_service.get_dataset_by_id_unchecked(model.training_dataset_id)
    df = dataset_service.load_dataframe(training_dataset)
    feature_columns = json.loads(model.feature_columns)
    df = df.dropna(subset=[model.target_column])[feature_columns]

    sample_size = min(get_settings().shap_background_sample_size, len(df))
    return df.sample(n=sample_size, random_state=get_settings().ml_random_state)


def _split_pipeline(model: MLModel):
    pipeline = training_service.load_pipeline(model)
    return pipeline, pipeline.named_steps["preprocessor"], pipeline.named_steps["classifier"]


def _original_feature_for(transformed_name: str, categorical_columns: set) -> str:
    """
    ColumnTransformer names transformed columns like "numeric__age" or
    "categorical__contract_type_monthly". This maps either form back to
    the ORIGINAL column name ("age" or "contract_type").
    """
    _, _, remainder = transformed_name.partition("__")
    for column in categorical_columns:
        if remainder == column or remainder.startswith(f"{column}_"):
            return column
    return remainder  # numeric columns pass through unchanged


def global_importance(model: MLModel) -> list[dict]:
    pipeline, preprocessor, classifier = _split_pipeline(model)
    categorical_columns = set(json.loads(model.categorical_feature_columns))

    background = _load_background(model)
    background_transformed = preprocessor.transform(background)

    explainer = shap.LinearExplainer(classifier, background_transformed)
    shap_values = explainer.shap_values(background_transformed)

    transformed_names = list(preprocessor.get_feature_names_out())
    mean_abs = np.abs(shap_values).mean(axis=0)

    aggregated: dict = {}
    for name, value in zip(transformed_names, mean_abs):
        original = _original_feature_for(name, categorical_columns)
        aggregated[original] = aggregated.get(original, 0.0) + float(value)

    ranked = sorted(aggregated.items(), key=lambda item: item[1], reverse=True)
    return [{"feature": name, "mean_abs_shap": round(value, 5)} for name, value in ranked]


def explain_prediction(model: MLModel, dataset: Dataset, row_index: int) -> dict:
    pipeline, preprocessor, classifier = _split_pipeline(model)
    feature_columns = json.loads(model.feature_columns)
    categorical_columns = set(json.loads(model.categorical_feature_columns))

    df = dataset_service.load_dataframe(dataset)
    if row_index < 0 or row_index >= len(df):
        raise ExplainabilityValidationError(
            f"Row index {row_index} is out of range for dataset {dataset.id} ({len(df)} rows)."
        )
    row = df.iloc[[row_index]][feature_columns]

    background = _load_background(model)
    background_transformed = preprocessor.transform(background)
    explainer = shap.LinearExplainer(classifier, background_transformed)

    row_transformed = preprocessor.transform(row)
    shap_row = explainer.shap_values(row_transformed)[0]

    transformed_names = list(preprocessor.get_feature_names_out())
    contributions: dict = {}
    for name, value in zip(transformed_names, shap_row):
        original = _original_feature_for(name, categorical_columns)
        contributions[original] = contributions.get(original, 0.0) + float(value)

    ranked = sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)

    return {
        "row_index": row_index,
        "base_value": float(np.atleast_1d(explainer.expected_value)[0]),
        "predicted_probability": float(pipeline.predict_proba(row)[0, 1]),
        "predicted_class": int(pipeline.predict(row)[0]),
        "contributions": [
            {
                "feature": name,
                "contribution": round(value, 5),
                "direction": "increases churn risk" if value > 0 else "decreases churn risk",
            }
            for name, value in ranked
        ],
    }
