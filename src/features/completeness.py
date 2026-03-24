"""
Compute completeness scores for applications.

Completeness is a simple measure of how many mandatory fields have been
provided by the applicant and how many documents are missing.  A higher
score indicates a more complete application.
"""

import pandas as pd


MANDATORY_FIELDS = [
    "age",
    "employment_status",
    "monthly_income",
    "existing_debt",
    "requested_amount",
    "requested_duration_months",
]


def completeness_score(df: pd.DataFrame) -> pd.Series:
    """Compute completeness score for each application.

    The score is computed as 1 minus the proportion of mandatory fields that
    are missing.  A score of 1 means all mandatory fields are present;
    0 means all mandatory fields are missing.

    Args:
        df: DataFrame with applications.

    Returns:
        A pandas Series of completeness scores.
    """
    total_required = len(MANDATORY_FIELDS)
    missing_counts = df[MANDATORY_FIELDS].isnull().sum(axis=1)
    return 1.0 - missing_counts / total_required