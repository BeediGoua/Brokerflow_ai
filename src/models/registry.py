"""
Model registry utilities.

This module provides helper functions to load persisted models from disk.
If a model file is missing it raises a FileNotFoundError.  Use the
``settings`` object to determine the default paths.
"""

from pathlib import Path
import joblib

from src.config.settings import settings


def load_baseline_model() -> object:
    """Load the baseline logistic regression pipeline."""
    path = Path(settings.model_path)
    if not path.exists():
        raise FileNotFoundError(f"Baseline model file {path} is missing.  Run `make train`. ")
    return joblib.load(path)


def load_candidate_model() -> object:
    """Load the LightGBM candidate model."""
    path = Path("models/candidate_lgbm.pkl")
    if not path.exists():
        raise FileNotFoundError(f"Candidate model file {path} is missing.  Run `make train`. ")
    return joblib.load(path)