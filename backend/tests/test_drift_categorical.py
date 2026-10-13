import pandas as pd

from app.drift.categorical import (
    align_category_counts,
    categorical_psi,
    chi_square_test,
    detect_new_categories,
)
from app.drift.psi import psi_from_frequencies


def test_align_category_counts_uses_the_union():
    reference = pd.Series(["a", "a", "b"])
    current = pd.Series(["a", "c"])
    ref_counts, cur_counts = align_category_counts(reference, current)

    assert set(ref_counts.index) == {"a", "b", "c"}
    assert ref_counts["c"] == 0
    assert cur_counts["b"] == 0


def test_detect_new_categories():
    reference = pd.Series(["monthly", "yearly"])
    current = pd.Series(["monthly", "yearly", "biannual"])
    assert detect_new_categories(reference, current) == ["biannual"]
    assert detect_new_categories(reference, pd.Series(["monthly"])) == []


def test_chi_square_test_no_difference_is_stable():
    reference = pd.Series(["a"] * 50 + ["b"] * 50)
    current = pd.Series(["a"] * 48 + ["b"] * 52)
    result = chi_square_test(*align_category_counts(reference, current), pvalue_threshold=0.05)
    assert result["status"] == "stable"


def test_chi_square_test_detects_a_real_shift():
    reference = pd.Series(["a"] * 50 + ["b"] * 50)
    current = pd.Series(["a"] * 90 + ["b"] * 10)
    result = chi_square_test(*align_category_counts(reference, current), pvalue_threshold=0.05)
    assert result["status"] == "drift"


def test_categorical_psi_matches_the_shared_psi_core():
    reference = pd.Series(["a"] * 70 + ["b"] * 30)
    current = pd.Series(["a"] * 40 + ["b"] * 60)
    ref_counts, cur_counts = align_category_counts(reference, current)

    outcome = categorical_psi(ref_counts, cur_counts, warning_threshold=0.1, drift_threshold=0.25)
    expected_psi = psi_from_frequencies(ref_counts, cur_counts)

    assert outcome["psi"] == expected_psi
