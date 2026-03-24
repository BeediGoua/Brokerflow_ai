"""
Data loading helpers.

These functions simplify reading CSV files into pandas DataFrames and
perform basic schema validation.  In a production setting you would
augment these functions with more robust error handling and data type
parsing.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from .validate_inputs import validate_applications_columns


def load_applications_csv(path: str) -> pd.DataFrame:
    """Load the applications CSV and validate its columns.

    Args:
        path: Path to the CSV file.

    Returns:
        Loaded DataFrame.
    """
    df = pd.read_csv(path)
    validate_applications_columns(df)
    return df


def load_documents_csv(path: str) -> pd.DataFrame:
    """Load the documents CSV.

    Args:
        path: Path to the documents CSV file.

    Returns:
        Loaded DataFrame.
    """
    return pd.read_csv(path)


def load_reviews_csv(path: str) -> pd.DataFrame:
    """Load the reviews CSV.

    Args:
        path: Path to the reviews CSV file.

    Returns:
        Loaded DataFrame.
    """
    return pd.read_csv(path)