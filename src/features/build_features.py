"""
Feature construction functions.

This module contains helper functions to derive model features from the
preprocessed application data.  New variables such as ratios and buckets
are added to facilitate downstream modelling.  The functions avoid in‑place
modification to make it easier to compose operations.
"""

import pandas as pd


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute engineered features from raw application data.

    Args:
        df: Preprocessed applications DataFrame.

    Returns:
        A copy of the DataFrame with additional columns for model training.
    """
    df = df.copy()
    # Avoid division by zero
    df["monthly_income_safe"] = df["monthly_income"].replace({0: 1e-3})
    # Ratio of existing debt to income
    df["ratio_debt_income"] = df["existing_debt"] / df["monthly_income_safe"]
    # Ratio of requested amount to income
    df["ratio_requested_income"] = df["requested_amount"] / df["monthly_income_safe"]
    # Requested loan per month (rough proxy for instalment)
    df["instalment_proxy"] = df["requested_amount"] / df["requested_duration_months"].clip(lower=1)

    # Full monthly debt‑to‑income ratio.  In addition to the existing debt, we
    # include the new monthly instalment and an estimate of other obligations.  This
    # follows the CFPB definition of DTI as total monthly debt payments divided
    # by gross monthly income.
    if "monthly_installment" in df.columns and "other_monthly_debt_proxy" in df.columns:
        df["dti_monthly_full"] = (
            (df["monthly_installment"] + df["other_monthly_debt_proxy"]) / df["monthly_income_safe"]
        )
    else:
        df["dti_monthly_full"] = None

    # Normalised residual income proxy.  A positive residual income suggests
    # available cash after paying debts.  We normalise by income to keep
    # magnitudes comparable across applicants.
    if "residual_income_proxy" in df.columns:
        df["residual_income_ratio"] = df["residual_income_proxy"] / (df["monthly_income_safe"] + 1e-3)
    else:
        df["residual_income_ratio"] = None

    # Normalised credit score proxy on a 0–1 scale.  Original proxy ranges
    # roughly between 300 and 850.  Normalising helps the model treat it
    # comparably to other features.
    if "credit_score_proxy" in df.columns:
        df["credit_score_norm"] = df["credit_score_proxy"] / 850.0
    else:
        df["credit_score_norm"] = None
    # Bucketed years in job
    df["years_in_job_bucket"] = pd.cut(df["years_in_job"], bins=[-1, 1, 3, 5, 10, 20, 50], labels=False)
    # Bucket account tenure
    df["account_tenure_bucket"] = pd.cut(df["account_tenure_months"], bins=[-1, 6, 12, 24, 60, 120, 999], labels=False)
    # Late payment rate
    df["late_payment_rate"] = df["prior_late_payments"] / (df["prior_loans_count"].replace({0: 1}))
    # Recent credit activity flag
    df["recent_credit_activity_flag"] = (df["days_since_last_loan"] < 60).astype(int)
    # Drop helper
    df = df.drop(columns=["monthly_income_safe"], errors="ignore")
    return df