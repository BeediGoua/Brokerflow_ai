"""
Preprocessing utilities.

This module prepares raw application data for feature engineering.  It
includes functions to cast data types, handle missing values and create
simple derived variables used downstream.  The functions are intentionally
lightweight for demonstration purposes.
"""

import pandas as pd
import numpy as np


def preprocess_applications(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and prepare application data for feature engineering.

    The preprocessing logic fills missing numeric values with the median
    of each column and converts date strings to pandas datetime.  It also
    ensures correct data types for categorical variables.

    Args:
        df: Raw applications DataFrame.

    Returns:
        A cleaned DataFrame ready for feature engineering.
    """
    df = df.copy()
    # Convert dates
    if "snapshot_date" in df.columns:
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], errors="coerce")
    # Fill numeric NaNs with median
    for col in df.select_dtypes(include=[np.number]).columns:
        median = df[col].median()
        df[col] = df[col].fillna(median)
    # Fill string columns with empty string
    for col in df.select_dtypes(include=[object]).columns:
        df[col] = df[col].fillna("")
    # Ensure categorical columns are strings
    categorical_cols = [
        "gender", "marital_status", "employment_status", "sector", "product_type",
        "region", "declared_purpose", "free_text_note",
    ]
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df