import numpy as np
import pandas as pd
import pytest

from app.drift.numeric import InsufficientDataError, ks_test
from app.drift.psi import numeric_psi


def test_ks_test_identical_distributions_is_stable():
    values = pd.Series(np.arange(50))
    result = ks_test(values, values.copy(), pvalue_threshold=0.05)
    assert result["statistic"] == 0.0
    assert result["p_value"] == 1.0
    assert result["status"] == "stable"


def test_ks_test_detects_a_clear_shift():
    reference = pd.Series(np.arange(0, 100))
    current = pd.Series(np.arange(1000, 1100))
    result = ks_test(reference, current, pvalue_threshold=0.05)
    assert result["statistic"] > 0.9
    assert result["status"] == "drift"


def test_ks_test_raises_on_insufficient_data():
    with pytest.raises(InsufficientDataError):
        ks_test(pd.Series([1.0]), pd.Series([2.0]), pvalue_threshold=0.05)


def test_numeric_psi_no_drift_between_identical_samples():
    values = pd.Series(np.arange(200))
    outcome = numeric_psi(values, values.copy(), buckets=5, warning_threshold=0.1, drift_threshold=0.25)
    assert outcome["psi"] < 1e-6
    assert outcome["status"] == "stable"
    assert outcome["buckets"] == 5


def test_numeric_psi_detects_a_shifted_distribution():
    reference = pd.Series(np.arange(200))
    current = pd.Series(np.arange(200) + 500)
    outcome = numeric_psi(reference, current, buckets=5, warning_threshold=0.1, drift_threshold=0.25)
    assert outcome["status"] == "drift"
