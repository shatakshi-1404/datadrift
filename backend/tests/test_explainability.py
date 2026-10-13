import numpy as np
import pandas as pd
import shap

from app.explainability.shap_service import _original_feature_for
from app.ml.train import train_logistic_regression


def _separable_dataframe(n: int = 80):
    rng = np.random.default_rng(1)
    risk_score = rng.normal(size=n)
    return pd.DataFrame(
        {
            "risk_score": risk_score,
            "plan": rng.choice(["monthly", "yearly"], size=n),
            "churn": (risk_score > 0).astype(int),
        }
    )


def test_shap_produces_finite_values_matching_transformed_feature_count():
    df = _separable_dataframe()
    result = train_logistic_regression(df, "churn", random_state=42)
    pipeline = result["pipeline"]
    preprocessor, classifier = pipeline.named_steps["preprocessor"], pipeline.named_steps["classifier"]

    background = df[result["feature_columns"]].sample(n=30, random_state=42)
    background_transformed = preprocessor.transform(background)

    explainer = shap.LinearExplainer(classifier, background_transformed)
    shap_values = explainer.shap_values(background_transformed)

    assert shap_values.shape[0] == 30
    assert shap_values.shape[1] == len(preprocessor.get_feature_names_out())
    assert np.isfinite(shap_values).all()


def test_original_feature_mapping_reconstructs_categorical_columns():
    categorical_columns = {"plan"}
    assert _original_feature_for("numeric__risk_score", categorical_columns) == "risk_score"
    assert _original_feature_for("categorical__plan_monthly", categorical_columns) == "plan"
    assert _original_feature_for("categorical__plan_yearly", categorical_columns) == "plan"
