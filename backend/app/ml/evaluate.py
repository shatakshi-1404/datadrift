import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline


def evaluate_classifier(pipeline: Pipeline, X, y) -> dict:
    """
    Compute real classification metrics. roc_auc is None when y contains
    only one class, since AUC is undefined in that case.
    """
    y_pred = pipeline.predict(X)

    roc_auc = None
    if len(np.unique(y)) > 1:
        y_proba = pipeline.predict_proba(X)[:, 1]
        roc_auc = float(roc_auc_score(y, y_proba))

    return {
        "accuracy": float(accuracy_score(y, y_pred)),
        "precision": float(precision_score(y, y_pred, zero_division=0)),
        "recall": float(recall_score(y, y_pred, zero_division=0)),
        "f1": float(f1_score(y, y_pred, zero_division=0)),
        "roc_auc": roc_auc,
    }
