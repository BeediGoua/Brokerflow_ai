"""
Tests for data validation functions.
"""

import pandas as pd
import pytest

from src.data.validate_inputs import validate_applications_columns, EXPECTED_APPLICATION_COLUMNS


def test_validate_applications_columns_passes_on_complete_df():
    # Create a DataFrame with all required columns
    df = pd.DataFrame({c: [] for c in EXPECTED_APPLICATION_COLUMNS})
    # Should not raise an exception
    validate_applications_columns(df)


def test_validate_applications_columns_raises_on_missing():
    df = pd.DataFrame({"application_id": ["A"]})
    with pytest.raises(ValueError):
        validate_applications_columns(df)