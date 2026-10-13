import numpy as np
import pandas as pd

MIN_BUCKETS = 2
PROPORTION_FLOOR = 1e-4  # avoids log(0) / division by zero


class InsufficientDataError(Exception):
    """Not enough distinct values to form meaningful buckets."""


def psi_from_frequencies(reference_counts: pd.Series, current_counts: pd.Series) -> float:
    """
    Core PSI formula. Generic over any aligned pair of bucket counts -
    numeric buckets or category counts both use this same function.

    PSI = sum over buckets of (cur% - ref%) * ln(cur% / ref%)
    """
    reference_total = reference_counts.sum()
    current_total = current_counts.sum()
    if reference_total == 0 or current_total == 0:
        raise InsufficientDataError("Cannot compute PSI from an empty distribution.")

    reference_pct = (reference_counts / reference_total).clip(lower=PROPORTION_FLOOR)
    current_pct = (current_counts / current_total).clip(lower=PROPORTION_FLOOR)

    contributions = (current_pct - reference_pct) * np.log(current_pct / reference_pct)
    return float(contributions.sum())


def classify_psi(value: float, warning_threshold: float, drift_threshold: float) -> str:
    if value >= drift_threshold:
        return "drift"
    if value >= warning_threshold:
        return "warning"
    return "stable"


def _quantile_bin_edges(reference: pd.Series, buckets: int) -> np.ndarray:
    """
    Split the reference distribution into `buckets` equal-population bins.
    Duplicate edges are dropped. The outer edges are extended to +/-
    infinity so current values outside the reference's observed range
    still fall into the first/last bucket.
    """
    quantiles = np.linspace(0, 1, buckets + 1)
    edges = np.unique(reference.quantile(quantiles).to_numpy())
    if len(edges) - 1 < MIN_BUCKETS:
        raise InsufficientDataError(
            "Reference data has too few distinct values to form meaningful buckets."
        )
    edges[0] = -np.inf
    edges[-1] = np.inf
    return edges


def numeric_distribution(reference: pd.Series, current: pd.Series, buckets: int) -> dict:
    """
    Quantile-bins `reference` and applies the same edges to `current`.
    Returns bucket labels plus each dataset's share (%) per bucket - the
    exact same binning PSI itself uses.
    """
    ref_clean = reference.dropna()
    cur_clean = current.dropna()
    if len(ref_clean) < buckets or len(cur_clean) < MIN_BUCKETS:
        raise InsufficientDataError("Not enough non-missing values to build a distribution.")

    edges = _quantile_bin_edges(ref_clean, buckets)
    ref_binned = pd.cut(ref_clean, bins=edges, include_lowest=True)
    cur_binned = pd.cut(cur_clean, bins=edges, include_lowest=True)

    categories = ref_binned.cat.categories
    reference_counts = ref_binned.value_counts().reindex(categories, fill_value=0)
    current_counts = cur_binned.value_counts().reindex(categories, fill_value=0)

    reference_total, current_total = reference_counts.sum(), current_counts.sum()
    return {
        "labels": [str(interval) for interval in categories],
        "reference_counts": reference_counts.tolist(),
        "current_counts": current_counts.tolist(),
        "reference_percentage": (reference_counts / reference_total * 100).round(2).tolist(),
        "current_percentage": (current_counts / current_total * 100).round(2).tolist(),
    }


def numeric_psi(
    reference: pd.Series,
    current: pd.Series,
    buckets: int,
    warning_threshold: float,
    drift_threshold: float,
) -> dict:
    """Buckets both series (see numeric_distribution) and computes PSI from the resulting counts."""
    distribution = numeric_distribution(reference, current, buckets)
    reference_counts = pd.Series(distribution["reference_counts"])
    current_counts = pd.Series(distribution["current_counts"])

    psi_value = psi_from_frequencies(reference_counts, current_counts)
    return {
        "psi": psi_value,
        "status": classify_psi(psi_value, warning_threshold, drift_threshold),
        "buckets": len(distribution["labels"]),
    }
