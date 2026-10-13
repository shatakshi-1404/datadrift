import pandas as pd
from scipy import stats

from app.drift.psi import classify_psi, psi_from_frequencies

SMOOTHING = 0.5  # Haldane-Anscombe correction: avoids zero expected frequencies


class InsufficientDataError(Exception):
    """Not enough non-missing category data to compare."""


def align_category_counts(reference: pd.Series, current: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Counts each category in both series over the UNION of categories seen
    in either one, so a category missing from one side is a real zero,
    not silently dropped from the comparison.
    """
    ref_clean, cur_clean = reference.dropna(), current.dropna()
    if ref_clean.empty or cur_clean.empty:
        raise InsufficientDataError("Need non-missing category data in both datasets.")

    categories = sorted(set(ref_clean.unique()) | set(cur_clean.unique()), key=str)
    ref_counts = ref_clean.value_counts().reindex(categories, fill_value=0)
    cur_counts = cur_clean.value_counts().reindex(categories, fill_value=0)
    return ref_counts, cur_counts


def detect_new_categories(reference: pd.Series, current: pd.Series) -> list[str]:
    """Categories that appear in `current` but never appeared in `reference` at all."""
    known = set(reference.dropna().unique())
    seen_in_current = set(current.dropna().unique())
    return sorted(str(c) for c in (seen_in_current - known))


def chi_square_test(
    reference_counts: pd.Series, current_counts: pd.Series, pvalue_threshold: float
) -> dict:
    """
    Chi-square goodness-of-fit test: are current's category counts
    consistent with reference's proportions, scaled to current's sample
    size? Smoothing avoids an undefined result when a category has zero
    expected count.
    """
    reference_total = reference_counts.sum()
    current_total = current_counts.sum()

    smoothed_reference_pct = (reference_counts + SMOOTHING) / (
        reference_total + SMOOTHING * len(reference_counts)
    )
    expected = smoothed_reference_pct * current_total

    result = stats.chisquare(f_obs=current_counts.to_numpy(), f_exp=expected.to_numpy())
    status = "drift" if result.pvalue < pvalue_threshold else "stable"
    return {"statistic": float(result.statistic), "p_value": float(result.pvalue), "status": status}


def categorical_psi(
    reference_counts: pd.Series, current_counts: pd.Series, warning_threshold: float, drift_threshold: float
) -> dict:
    """PSI over category counts directly - no binning needed, unlike numeric PSI."""
    psi_value = psi_from_frequencies(reference_counts, current_counts)
    return {"psi": psi_value, "status": classify_psi(psi_value, warning_threshold, drift_threshold)}


def categorical_distribution(reference: pd.Series, current: pd.Series) -> dict:
    """Same shape as numeric_distribution, but categories are the "buckets" - no binning needed."""
    reference_counts, current_counts = align_category_counts(reference, current)
    reference_total, current_total = reference_counts.sum(), current_counts.sum()
    return {
        "labels": [str(category) for category in reference_counts.index],
        "reference_counts": reference_counts.tolist(),
        "current_counts": current_counts.tolist(),
        "reference_percentage": (reference_counts / reference_total * 100).round(2).tolist(),
        "current_percentage": (current_counts / current_total * 100).round(2).tolist(),
    }
