import numpy as np
import pandas as pd
import pytest

from app.ml.evaluate import evaluate_classifier
from app.ml.train import TrainingError, split_feature_columns, train_logistic_regression


def _separable_churn_dataframe(n: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    risk_score = rng.normal(size=n)
    return pd.DataFrame(
        {
            "risk_score": risk_score,
            "plan": rng.choice(["monthly", "yearly"], size=n),
            "churn": (risk_score > 0).astype(int),
        }
    )


def test_split_feature_columns_separates_numeric_and_categorical():
    df = _separable_churn_dataframe()
    numeric, categorical = split_feature_columns(df, "churn")
    assert numeric == ["risk_score"]
    assert categorical == ["plan"]


def test_split_feature_columns_missing_target_raises():
    df = _separable_churn_dataframe()
    with pytest.raises(TrainingError):
        split_feature_columns(df, "does_not_exist")


def test_train_logistic_regression_achieves_high_accuracy_on_separable_data():
    df = _separable_churn_dataframe()
    result = train_logistic_regression(df, "churn", random_state=42)
    assert result["test_metrics"]["accuracy"] > 0.8
    assert set(result["feature_columns"]) == {"risk_score", "plan"}


def test_train_logistic_regression_rejects_non_binary_target():
    df = _separable_churn_dataframe()
    df["churn"] = np.random.default_rng(0).integers(0, 3, size=len(df))
    with pytest.raises(TrainingError):
        train_logistic_regression(df, "churn", random_state=42)


class _StubPipeline:
    def __init__(self, predictions, probabilities):
        self._predictions = np.array(predictions)
        self._probabilities = np.array(probabilities)

    def predict(self, X):
        return self._predictions

    def predict_proba(self, X):
        return np.column_stack([1 - self._probabilities, self._probabilities])


def test_evaluate_classifier_computes_expected_metrics():
    y_true = pd.Series([1, 1, 0, 0])
    pipeline = _StubPipeline(predictions=[1, 0, 0, 0], probabilities=[0.9, 0.4, 0.2, 0.1])
    metrics = evaluate_classifier(pipeline, X=None, y=y_true)

    assert metrics["accuracy"] == 0.75
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.5
    assert metrics["roc_auc"] is not None


def test_evaluate_classifier_roc_auc_is_none_for_a_single_class():
    y_true = pd.Series([0, 0, 0, 0])
    pipeline = _StubPipeline(predictions=[0, 0, 0, 0], probabilities=[0.1, 0.2, 0.1, 0.3])
    metrics = evaluate_classifier(pipeline, X=None, y=y_true)
    assert metrics["roc_auc"] is None
