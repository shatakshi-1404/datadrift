from app.quality.checks import check_constant_columns, check_duplicates, check_missing_values
from app.schemas.profile import DatasetProfile, FeatureProfile


def _profile(features, duplicate_percentage: float = 0.0) -> DatasetProfile:
    return DatasetProfile(
        rows=100,
        columns=len(features),
        duplicate_rows=0,
        duplicate_percentage=duplicate_percentage,
        total_missing_cells=0,
        features=features,
    )


def _feature(name: str, missing_pct: float, unique: int = 5) -> FeatureProfile:
    return FeatureProfile(
        name=name,
        data_type="int64",
        feature_type="numeric",
        missing_count=0,
        missing_percentage=missing_pct,
        unique_count=unique,
    )


def test_missing_value_increase_severity_tiers():
    reference = _profile([_feature("income", missing_pct=2.0)])
    current_stable = _profile([_feature("income", missing_pct=4.0)])
    current_warning = _profile([_feature("income", missing_pct=10.0)])
    current_critical = _profile([_feature("income", missing_pct=25.0)])

    assert check_missing_values(reference, current_stable, 5, 15)[0]["status"] == "stable"
    assert check_missing_values(reference, current_warning, 5, 15)[0]["status"] == "warning"
    assert check_missing_values(reference, current_critical, 5, 15)[0]["status"] == "critical"


def test_duplicate_check_severity():
    assert check_duplicates(_profile([], duplicate_percentage=0.2), 1, 5)["status"] == "stable"
    assert check_duplicates(_profile([], duplicate_percentage=2.0), 1, 5)["status"] == "warning"
    assert check_duplicates(_profile([], duplicate_percentage=10.0), 1, 5)["status"] == "critical"


def test_constant_column_detection():
    profile = _profile([_feature("plan_type", missing_pct=0.0, unique=1), _feature("age", missing_pct=0.0, unique=40)])
    assert check_constant_columns(profile) == ["plan_type"]
