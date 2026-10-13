import pandas as pd
from sklearn.pipeline import Pipeline


def predict(pipeline: Pipeline, X: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """
    Runs a fitted pipeline on X and returns (predicted_class, predicted_probability).
    predicted_probability is the probability of the positive class (churn = 1).
    """
    predicted_class = pd.Series(pipeline.predict(X), index=X.index, name="predicted_class")
    predicted_probability = pd.Series(
        pipeline.predict_proba(X)[:, 1], index=X.index, name="predicted_probability"
    )
    return predicted_class, predicted_probability
