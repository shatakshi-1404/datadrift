"""
Generates a synthetic customer-churn dataset for DataDrift development.

reference.csv: the "training-time" population, used to train the model.
current.csv:   a "later" population with a genuine covariate shift
               (income lower, more support calls, contract mix shifted
               toward monthly) but churn still generated from the SAME
               underlying rule as reference. This deliberately creates
               a "drift without necessarily breaking the model" scenario
               for later phases, rather than a random/meaningless shift.

Both files are clearly synthetic and are for development/testing only.
"""

import numpy as np
import pandas as pd

RNG_SEED = 42
REFERENCE_ROWS = 2000
CURRENT_ROWS = 600


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))


def _generate(n: int, rng: np.random.Generator, drift: bool) -> pd.DataFrame:
    age = rng.integers(18, 71, size=n)

    income_mean = 55_000 * (0.85 if drift else 1.0)  # drift: lower income
    income = rng.lognormal(mean=np.log(income_mean), sigma=0.35, size=n).round(2)

    tenure = rng.integers(0, 73, size=n)

    contract_probs = [0.55, 0.15, 0.30] if drift else [0.35, 0.15, 0.50]
    contract_type = rng.choice(
        ["monthly", "weekly", "yearly"], size=n, p=contract_probs
    )

    support_calls_lambda = 2.5 if drift else 1.3  # drift: more support calls
    support_calls = rng.poisson(lam=support_calls_lambda, size=n)

    monthly_usage = np.clip(
        rng.normal(loc=150, scale=60, size=n) - support_calls * 5, 0, None
    ).round(1)

    # True churn-generating rule (same function for both datasets;
    # only the INPUT distributions shift for `current`).
    contract_risk = np.select(
        [contract_type == "monthly", contract_type == "weekly", contract_type == "yearly"],
        [0.9, 0.6, -0.9],
    )
    z = (
        -3.0
        + 0.55 * contract_risk
        + 0.40 * support_calls
        - 0.015 * tenure
        - 0.00002 * income
        - 0.01 * age
        - 0.004 * monthly_usage
        + rng.normal(0, 0.5, size=n)  # irreducible noise
    )
    churn = rng.binomial(1, _sigmoid(z))

    return pd.DataFrame(
        {
            "age": age,
            "income": income,
            "monthly_usage": monthly_usage,
            "tenure": tenure,
            "contract_type": contract_type,
            "support_calls": support_calls,
            "churn": churn,
        }
    )


def main() -> None:
    rng = np.random.default_rng(RNG_SEED)
    reference = _generate(REFERENCE_ROWS, rng, drift=False)
    current = _generate(CURRENT_ROWS, rng, drift=True)

    import os
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data")
    os.makedirs(out_dir, exist_ok=True)
    reference.to_csv(os.path.join(out_dir, "churn_reference.csv"), index=False)
    current.to_csv(os.path.join(out_dir, "churn_current.csv"), index=False)

    print(f"reference: {len(reference)} rows, churn rate {reference['churn'].mean():.3f}")
    print(f"current:   {len(current)} rows, churn rate {current['churn'].mean():.3f}")


if __name__ == "__main__":
    main()
