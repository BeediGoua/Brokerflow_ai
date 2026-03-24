"""
Tests for feature engineering functions.
"""

import pandas as pd

from src.features.build_features import add_engineered_features


def test_add_engineered_features_adds_expected_columns():
    df = pd.DataFrame({
        "monthly_income": [5000],
        "existing_debt": [10000],
        "requested_amount": [15000],
        "requested_duration_months": [36],
        "years_in_job": [5],
        "account_tenure_months": [24],
        "prior_loans_count": [2],
        "prior_late_payments": [0],
        "days_since_last_loan": [100],
    })
    df_out = add_engineered_features(df)
    assert "ratio_debt_income" in df_out.columns
    assert "ratio_requested_income" in df_out.columns
    assert "instalment_proxy" in df_out.columns
    assert "years_in_job_bucket" in df_out.columns
    assert "account_tenure_bucket" in df_out.columns
    assert "late_payment_rate" in df_out.columns
    assert "recent_credit_activity_flag" in df_out.columns