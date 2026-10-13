import pandas as pd
from scipy import stats

MIN_SAMPLES = 2


class InsufficientDataError(Exception):
    """Not enough non-missing values to run a statistical test."""


def ks_test(reference: pd.Series, current: pd.Series, pvalue_threshold: float) -> dict:
    """
    Runs a two-sample Kolmogorov-Smirnov test comparing the distribution
    of `reference` against `current`.

    Returns:
        statistic:  KS statistic D, in [0, 1]. Larger = more different shapes.
        p_value:    probability of seeing a D this large if the two samples
                    actually came from the same distribution.
        status:     "drift" if p_value < pvalue_threshold, else "stable".
    """
    ref_clean = reference.dropna()
    cur_clean = current.dropna()

    if len(ref_clean) < MIN_SAMPLES or len(cur_clean) < MIN_SAMPLES:
        raise InsufficientDataError(
            f"Need at least {MIN_SAMPLES} non-missing values in both datasets."
        )

    result = stats.ks_2samp(ref_clean, cur_clean)
    status = "drift" if result.pvalue < pvalue_threshold else "stable"

    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "status": status,
    }
