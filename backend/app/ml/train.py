import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.evaluate import evaluate_classifier
from app.ml.preprocessing import build_preprocessor
from app.services.profiling_service import infer_feature_type


class TrainingError(Exception):
    """The dataset is unsuitable for training as requested."""


MIN_ROWS_PER_CLASS = 5


def split_feature_columns(
    df: pd.DataFrame, target_column: str
) -> tuple[list[str], list[str]]:
    if target_column not in df.columns:
        raise TrainingError(f"Target column '{target_column}' not found in dataset.")

    feature_df = df.drop(columns=[target_column])
    numeric, categorical = [], []
    for col in feature_df.columns:
        if infer_feature_type(feature_df[col]) == "numeric":
            numeric.append(col)
        else:
            categorical.append(col)
    if not numeric and not categorical:
        raise TrainingError("Dataset has no feature columns besides the target.")
    return numeric, categorical


def _validate_target(y: pd.Series) -> None:
    counts = y.value_counts(dropna=True)
    if len(counts) != 2:
        raise TrainingError(
            "Target column must be binary (exactly two classes) for this classifier."
        )
    if counts.min() < MIN_ROWS_PER_CLASS:
        raise TrainingError(
            f"Each class needs at least {MIN_ROWS_PER_CLASS} rows; "
            f"smallest class has {counts.min()}."
        )


def train_logistic_regression(
    df: pd.DataFrame, target_column: str, random_state: int
) -> dict:
    """
    Trains a Logistic Regression pipeline and returns everything the
    caller needs to persist it: the fitted pipeline, the feature columns
    used (split by type), and metrics computed on both the train and
    test splits.
    """
    numeric_features, categorical_features = split_feature_columns(df, target_column)

    working = df.dropna(subset=[target_column])
    if len(working) < len(df):
        raise TrainingError("Target column contains missing values.")

    X = working[numeric_features + categorical_features]
    y = working[target_column].astype(int)
    _validate_target(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )

    preprocessor = build_preprocessor(numeric_features, categorical_features)
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, random_state=random_state)),
        ]
    )
    pipeline.fit(X_train, y_train)

    return {
        "pipeline": pipeline,
        "feature_columns": numeric_features + categorical_features,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "train_metrics": evaluate_classifier(pipeline, X_train, y_train),
        "test_metrics": evaluate_classifier(pipeline, X_test, y_test),
    }
