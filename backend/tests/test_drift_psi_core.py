import pandas as pd
import pytest

from app.drift.psi import classify_psi, psi_from_frequencies


def test_psi_is_near_zero_for_identical_distributions():
    counts = pd.Series([25, 25, 25, 25])
    assert psi_from_frequencies(counts, counts) < 1e-9


def test_psi_is_large_for_a_complete_shift():
    reference = pd.Series([100, 0, 0, 0])
    current = pd.Series([0, 0, 0, 100])
    psi_value = psi_from_frequencies(reference, current)
    assert psi_value > 5
    assert psi_value != float("inf")


def test_psi_from_frequencies_rejects_empty_distribution():
    with pytest.raises(Exception):
        psi_from_frequencies(pd.Series([0, 0]), pd.Series([1, 2]))


def test_classify_psi_boundaries():
    assert classify_psi(0.05, warning_threshold=0.1, drift_threshold=0.25) == "stable"
    assert classify_psi(0.1, warning_threshold=0.1, drift_threshold=0.25) == "warning"
    assert classify_psi(0.25, warning_threshold=0.1, drift_threshold=0.25) == "drift"


def test_psi_handles_a_bucket_that_disappears_entirely():
    reference = pd.Series([50, 50])
    current = pd.Series([100, 0])
    psi_value = psi_from_frequencies(reference, current)
    assert psi_value > 0
    assert psi_value != float("inf")
