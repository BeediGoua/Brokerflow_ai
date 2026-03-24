"""
Input validation functions for data loading.

The synthetic generation logic uses this module to enforce a stable column
ordering and to provide a reference list of expected columns.  Real-world
applications should expand these checks to include type enforcement and
business rule validation.
"""

from typing import List

EXPECTED_APPLICATION_COLUMNS: List[str] = [
    "application_id",
    "customer_id",
    "snapshot_date",
    "age",
    "gender",
    "marital_status",
    "employment_status",
    "sector",
    "years_in_job",
    "monthly_income",
    "income_stability_score",
    "existing_debt",
    "debt_to_income_ratio",
    "requested_amount",
    "requested_duration_months",
    "product_type",
    "region",
    "account_tenure_months",
    "prior_loans_count",
    "prior_late_payments",
    "has_prior_default",
    "days_since_last_loan",
    "declared_purpose",
    "free_text_note",
    # Newly added synthetic proxies.  These enhance the credit risk model and
    # align with common underwriting metrics such as instalment size, other
    # monthly debt obligations, residual income and a credit score proxy.
    "monthly_installment",
    "other_monthly_debt_proxy",
    "residual_income_proxy",
    "credit_score_proxy",
    "target_risk_flag",
]


def validate_applications_columns(df) -> None:
    """Validate that a DataFrame has the expected columns.

    Raises a ``ValueError`` if columns are missing.

    Args:
        df: DataFrame to validate.

    Returns:
        None if the DataFrame is valid.
    """
    missing = [c for c in EXPECTED_APPLICATION_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")