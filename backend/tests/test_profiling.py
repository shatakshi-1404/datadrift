import pandas as pd
import pytest

from app.services.profiling_service import infer_feature_type, profile_dataframe


def test_infer_feature_type_numeric_vs_categorical():
    assert infer_feature_type(pd.Series([1, 2, 3])) == "numeric"
    assert infer_feature_type(pd.Series([1.5, 2.5])) == "numeric"
    assert infer_feature_type(pd.Series(["a", "b"])) == "categorical"
    assert infer_feature_type(pd.Series([True, False])) == "categorical"


def test_profile_dataframe_basic_stats():
    df = pd.DataFrame(
        {
            "age": [20, 20, 30, None],
            "plan": ["monthly", "monthly", "yearly", "yearly"],
        }
    )
    profile = profile_dataframe(df)

    assert profile.rows == 4
    assert profile.columns == 2
    assert profile.duplicate_rows == 1

    age = next(f for f in profile.features if f.name == "age")
    assert age.feature_type == "numeric"
    assert age.missing_count == 1
    assert age.missing_percentage == 25.0
    assert age.numeric.min == 20
    assert age.numeric.max == 30

    plan = next(f for f in profile.features if f.name == "plan")
    assert plan.feature_type == "categorical"
    assert plan.categorical.unique_categories == 2


def test_profile_dataframe_rejects_empty_dataframe():
    with pytest.raises(ValueError):
        profile_dataframe(pd.DataFrame())
