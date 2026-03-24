"""
Data loading helpers.

These functions simplify reading CSV files into pandas DataFrames and
perform basic schema validation.  In a production setting you would
augment these functions with more robust error handling and data type
parsing.
"""

import pandas as pd

from .raw_competition import RawCompetitionBundle, build_current_loan_tables, load_raw_competition_zip
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


def load_raw_competition_bundle(path: str) -> RawCompetitionBundle:
    """Load the Zindi competition ZIP directly from disk."""
    return load_raw_competition_zip(path)


def load_enriched_raw_competition_tables(path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the Zindi competition ZIP and return enriched train/test tables."""
    bundle = load_raw_competition_bundle(path)
    return build_current_loan_tables(bundle)


def load_reviews_csv(path: str) -> pd.DataFrame:
    """Load the reviews CSV.

    Args:
        path: Path to the reviews CSV file.

    Returns:
        Loaded DataFrame.
    """
    return pd.read_csv(path)