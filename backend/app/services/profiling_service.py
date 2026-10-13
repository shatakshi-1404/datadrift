import math

import pandas as pd
from pandas.api import types as pdt

from app.schemas.profile import (
    CategoricalStats,
    CategoryFrequency,
    DatasetProfile,
    FeatureProfile,
    NumericStats,
)

TOP_CATEGORIES = 10


def infer_feature_type(series: pd.Series) -> str:
    """'numeric' for int/float columns, 'categorical' for everything else."""
    if pdt.is_numeric_dtype(series) and not pdt.is_bool_dtype(series):
        return "numeric"
    return "categorical"


def _to_float(value) -> float | None:
    """Make a number JSON-safe: NaN/inf become None, others are rounded."""
    if value is None or pd.isna(value):
        return None
    number = float(value)
    return None if math.isinf(number) else round(number, 4)


def _numeric_stats(series: pd.Series) -> NumericStats:
    clean = series.dropna()
    if clean.empty:
        return NumericStats(min=None, max=None, mean=None, median=None, std=None)
    return NumericStats(
        min=_to_float(clean.min()),
        max=_to_float(clean.max()),
        mean=_to_float(clean.mean()),
        median=_to_float(clean.median()),
        std=_to_float(clean.std()),
    )


def _categorical_stats(series: pd.Series) -> CategoricalStats:
    counts = series.dropna().value_counts()
    total = int(counts.sum())
    top = [
        CategoryFrequency(
            value=str(value),
            count=int(count),
            percentage=round(int(count) / total * 100, 2),
        )
        for value, count in counts.head(TOP_CATEGORIES).items()
    ]
    return CategoricalStats(unique_categories=int(len(counts)), top_categories=top)


def _profile_feature(name: str, series: pd.Series, n_rows: int) -> FeatureProfile:
    missing = int(series.isna().sum())
    feature_type = infer_feature_type(series)
    return FeatureProfile(
        name=name,
        data_type=str(series.dtype),
        feature_type=feature_type,
        missing_count=missing,
        missing_percentage=round(missing / n_rows * 100, 2),
        unique_count=int(series.nunique(dropna=True)),
        numeric=_numeric_stats(series) if feature_type == "numeric" else None,
        categorical=_categorical_stats(series) if feature_type == "categorical" else None,
    )


def profile_dataframe(df: pd.DataFrame) -> DatasetProfile:
    n_rows = len(df)
    if n_rows == 0:
        raise ValueError("Cannot profile an empty dataset.")

    duplicate_rows = int(df.duplicated().sum())
    features = [_profile_feature(str(col), df[col], n_rows) for col in df.columns]

    return DatasetProfile(
        rows=n_rows,
        columns=len(df.columns),
        duplicate_rows=duplicate_rows,
        duplicate_percentage=round(duplicate_rows / n_rows * 100, 2),
        total_missing_cells=sum(f.missing_count for f in features),
        features=features,
    )
