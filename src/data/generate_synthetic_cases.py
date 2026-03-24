"""
Synthetic dataset generator for BrokerFlow AI.

This script builds synthetic datasets that roughly follow the structure of
common credit‑risk competitions such as Zindi's *Loan Default Prediction*.
It creates three CSV files:

- ``applications.csv``: main tabular dataset with demographic, financial and historical variables.
- ``documents.csv``: simulated document metadata for each application.
- ``reviews.csv``: empty file reserved for future annotation.

Run this module as a script to write the files into the ``data/synthetic``
directory.  Use ``python -m src.data.generate_synthetic_cases``.
"""

import os
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from .validate_inputs import EXPECTED_APPLICATION_COLUMNS


def _make_applications(n_samples: int = 1000, random_state: int = 42) -> pd.DataFrame:
    """Generate a synthetic applications DataFrame.

    The distributions are chosen to look somewhat realistic while remaining
    completely artificial.  Some fields are correlated so that the model can
    learn meaningful patterns.

    Args:
        n_samples: Number of synthetic records to generate.
        random_state: Seed for reproducibility.

    Returns:
        A :class:`pandas.DataFrame` with the expected application columns.
    """

    rng = np.random.default_rng(random_state)

    # IDs
    application_id = [f"APP{i:05d}" for i in range(n_samples)]
    customer_id = [f"CUST{i:05d}" for i in range(n_samples)]
    snapshot_date = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, size=n_samples), unit="D")

    # Demographics
    age = rng.integers(20, 70, size=n_samples)
    gender = rng.choice(["M", "F", None], size=n_samples, p=[0.49, 0.49, 0.02])
    marital_status = rng.choice(["single", "married", "divorced", None], size=n_samples, p=[0.4, 0.45, 0.1, 0.05])

    # Employment
    employment_status = rng.choice(["employed", "self-employed", "unemployed"], size=n_samples, p=[0.7, 0.2, 0.1])
    sector = rng.choice(["finance", "tech", "retail", "health", "agriculture"], size=n_samples)
    years_in_job = rng.integers(0, 25, size=n_samples)

    # Income
    # Use a gamma distribution to simulate positive skew
    monthly_income = rng.gamma(shape=5.0, scale=500.0, size=n_samples)
    income_stability_score = rng.beta(a=2.0, b=2.0, size=n_samples)

    # Debt and requested amount
    existing_debt = rng.gamma(shape=3.0, scale=2000.0, size=n_samples)
    requested_amount = rng.gamma(shape=4.0, scale=3000.0, size=n_samples)
    debt_to_income_ratio = existing_debt / (monthly_income + 1e-3)
    requested_duration_months = rng.integers(6, 60, size=n_samples)

    product_type = rng.choice(["personal", "mortgage", "auto", "education"], size=n_samples)
    region = rng.choice(["north", "south", "east", "west"], size=n_samples)

    # Customer history
    account_tenure_months = rng.integers(1, 120, size=n_samples)
    prior_loans_count = rng.integers(0, 10, size=n_samples)
    prior_late_payments = rng.binomial(prior_loans_count, 0.2)
    has_prior_default = (prior_late_payments > 3).astype(int)
    days_since_last_loan = rng.integers(30, 365, size=n_samples)
    declared_purpose = rng.choice(["home", "car", "business", "education", "holiday"], size=n_samples)

    # Generate free text notes by sampling from a set of phrases.  To make
    # the note parser more interesting, include a few travel and booking‑related
    # strings (e.g. mentioning Booking.com).  These phrases are entirely
    # synthetic but allow users to test cross‑domain behaviour of the NLP
    # component.
    phrases = [
        "urgent need",
        "steady income",
        "previous loans paid",
        "missing documents",
        "multiple late payments",
        "recent default",
        "stable job",
        "needs fast approval",
        "travel booking via Booking.com",
        "hotel booked on Booking.com",
        "planned holiday using booking.com discount"
    ]
    free_text_note = []
    for _ in range(n_samples):
        # select between 1 and 4 phrases to build a semi‑structured note
        k = rng.integers(1, 4)
        selected = rng.choice(phrases, size=k, replace=False)
        free_text_note.append("; ".join(selected))

    # Compute a synthetic risk score and derive the target
    # Heavier weight on debt_to_income_ratio and prior_late_payments
    linear_score = (
        0.5 * debt_to_income_ratio +
        0.3 * prior_late_payments -
        0.2 * income_stability_score +
        0.5 * has_prior_default
    )
    noise = rng.normal(0.0, 1.0, size=n_samples)
    prob = 1.0 / (1.0 + np.exp(-(linear_score + noise)))
    target_risk_flag = (prob > 0.5).astype(int)

    # Compute additional synthetic financial proxies.  Monthly instalment is the
    # requested amount divided by the duration (proxy for amortised payments).  We
    # simulate "other monthly debt" as 30 % of this instalment.  Residual
    # income proxy subtracts monthly obligations from the income.  Finally we
    # build a simple credit score proxy inspired by FICO guidelines: severe
    # late behaviour, high debt‑to‑income and frequent borrowing reduce the
    # score, while long account tenure and many years in the same job boost it.
    # Ensure we never divide by zero for the instalment.  requested_duration_months
    # is a NumPy array here, so we cannot use pandas' ``clip`` method.  We
    # instead compute an element‑wise maximum with 1 to avoid division by zero.
    duration_nonzero = np.maximum(requested_duration_months, 1)
    monthly_installment = requested_amount / duration_nonzero
    other_monthly_debt_proxy = 0.3 * monthly_installment
    residual_income_proxy = monthly_income - (monthly_installment + other_monthly_debt_proxy)
    # Flags for credit score proxy
    severe_late_flag = (prior_late_payments > 5).astype(int)
    high_dti_flag = (debt_to_income_ratio > 0.5).astype(int)
    high_recent_borrowing_flag = (days_since_last_loan < 90).astype(int)
    long_history_flag = (account_tenure_months > 24).astype(int)
    stable_employment_flag = (years_in_job > 5).astype(int)
    credit_score_proxy = (
        650
        - 120 * severe_late_flag
        - 80 * high_dti_flag
        - 40 * high_recent_borrowing_flag
        + 30 * long_history_flag
        + 20 * stable_employment_flag
        + rng.normal(0.0, 20.0, size=n_samples)
    )
    # Bound the score within a typical FICO‑like range
    credit_score_proxy = credit_score_proxy.clip(300, 850)

    df = pd.DataFrame({
        "application_id": application_id,
        "customer_id": customer_id,
        "snapshot_date": snapshot_date.astype(str),
        "age": age,
        "gender": gender,
        "marital_status": marital_status,
        "employment_status": employment_status,
        "sector": sector,
        "years_in_job": years_in_job,
        "monthly_income": monthly_income,
        "income_stability_score": income_stability_score,
        "existing_debt": existing_debt,
        "debt_to_income_ratio": debt_to_income_ratio,
        "requested_amount": requested_amount,
        "requested_duration_months": requested_duration_months,
        "product_type": product_type,
        "region": region,
        "account_tenure_months": account_tenure_months,
        "prior_loans_count": prior_loans_count,
        "prior_late_payments": prior_late_payments,
        "has_prior_default": has_prior_default,
        "days_since_last_loan": days_since_last_loan,
        "declared_purpose": declared_purpose,
        "free_text_note": free_text_note,
        # Newly added synthetic proxies
        "monthly_installment": monthly_installment,
        "other_monthly_debt_proxy": other_monthly_debt_proxy,
        "residual_income_proxy": residual_income_proxy,
        "credit_score_proxy": credit_score_proxy,
        "target_risk_flag": target_risk_flag,
    })

    # Ensure column order matches expectation
    return df[EXPECTED_APPLICATION_COLUMNS]


def _make_documents(df_applications: pd.DataFrame, random_state: int = 42) -> pd.DataFrame:
    """Generate a documents DataFrame aligned with the applications.

    For each application, we randomly decide if each document type is required
    and whether it was provided.  A small extraction confidence and quality
    score is assigned.

    Args:
        df_applications: The applications DataFrame to derive IDs from.
        random_state: Seed for reproducibility.

    Returns:
        A :class:`pandas.DataFrame` of documents.
    """
    rng = np.random.default_rng(random_state)
    records = []
    document_types = ["id_proof", "income_proof", "bank_statement", "address_proof"]
    for app_id in df_applications["application_id"]:
        for doc_type in document_types:
            is_required = rng.choice([True, False], p=[0.9, 0.1])
            is_provided = is_required and rng.choice([True, False], p=[0.9, 0.1])
            quality = rng.uniform(0.6, 1.0) if is_provided else None
            confidence = rng.uniform(0.7, 1.0) if is_provided else None
            records.append({
                "document_id": f"DOC-{app_id}-{doc_type}",
                "application_id": app_id,
                "document_type": doc_type,
                "is_required": is_required,
                "is_provided": is_provided,
                "document_quality_score": quality,
                "extracted_text": None,
                "extraction_confidence": confidence,
            })
    return pd.DataFrame(records)


def generate_datasets(n_samples: int = 1000, output_dir: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate and optionally write the synthetic datasets.

    Args:
        n_samples: Number of synthetic applications to generate.
        output_dir: If provided, write CSV files into this directory.

    Returns:
        Tuple of (applications_df, documents_df, reviews_df).
    """
    apps = _make_applications(n_samples=n_samples)
    docs = _make_documents(apps)
    reviews = pd.DataFrame(columns=[
        "review_id",
        "application_id",
        "predicted_score",
        "predicted_class",
        "recommended_action",
        "human_decision",
        "human_risk_class",
        "reviewer_comment",
        "review_time_seconds",
    ])
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        apps.to_csv(output_path / "applications.csv", index=False)
        docs.to_csv(output_path / "documents.csv", index=False)
        reviews.to_csv(output_path / "reviews.csv", index=False)
    return apps, docs, reviews


def main() -> None:
    """Entry point when run as a script."""
    base_dir = Path(__file__).resolve().parents[2]  # project root
    synthetic_dir = base_dir / "data" / "synthetic"
    synthetic_dir.mkdir(parents=True, exist_ok=True)
    print(f"Generating synthetic datasets into {synthetic_dir}…")
    apps, docs, reviews = generate_datasets(n_samples=1000, output_dir=str(synthetic_dir))
    print(f"Generated {len(apps)} applications, {len(docs)} documents and {len(reviews)} reviews.")


if __name__ == "__main__":
    main()