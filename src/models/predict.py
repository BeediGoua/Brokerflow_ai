"""
Prediction utilities.

This module exposes functions to load trained models and perform risk
predictions on new applications.  It also produces auxiliary outputs such
as the risk class, top contributing factors and completeness score.  The
functions are designed to be called both from the API and tests.
"""

from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple, List

import joblib
import numpy as np
import pandas as pd

from src.config.settings import settings
from src.data.preprocess import preprocess_applications
from src.features.build_features import add_engineered_features
from src.features.completeness import completeness_score
from src.models.train_baseline import _select_feature_columns


def risk_class_from_score(score: float) -> str:
    """Map continuous risk score to discrete class."""
    if score < 0.34:
        return "Low"
    elif score < 0.67:
        return "Medium"
    return "High"


def load_baseline_pipeline() -> object:
    """Load the baseline model pipeline from disk.

    The model is always reloaded from disk to ensure that the latest
    version is used.  If the file is missing, a small baseline model is
    trained on the fly.  We intentionally avoid caching here because the
    underlying file may change during development or testing.
    """
    model_path = Path(settings.model_path)
    if model_path.exists():
        try:
            return joblib.load(model_path)
        except Exception:
            # If the file exists but is corrupt, fall back to training
            pass
    # Fallback: train a small baseline model on the fly
    try:
        from src.models.train_baseline import train_baseline_model
        pipeline = train_baseline_model(n_samples=300)
        return pipeline
    except Exception as exc:
        raise FileNotFoundError(
            f"Model file {model_path} is missing and on‑the‑fly training failed: {exc}"
        )


def prepare_features(app_dict: Dict) -> Tuple[pd.DataFrame, float, List[str], List[str]]:
    """Preprocess a single application dict and compute engineered features.

    Args:
        app_dict: A dictionary of application fields.

    Returns:
        Tuple of (feature DataFrame, completeness score, feature names, missing columns).
    """
    df = pd.DataFrame([app_dict])
    df = preprocess_applications(df)
    df = add_engineered_features(df)
    # Compute completeness and attach as a column so that the model sees it
    comp_series = completeness_score(df)
    comp = float(comp_series.iloc[0])
    df["completeness"] = comp_series
    feature_cols = _select_feature_columns(df)
    missing_cols = [c for c in feature_cols if c not in df.columns]
    X = df[feature_cols]
    return X, comp, feature_cols, missing_cols


def compute_contributions(pipeline, X: pd.DataFrame) -> List[Tuple[str, float]]:
    """Compute approximate per-feature contributions for the baseline model.

    This function multiplies each standardised feature by the logistic
    regression coefficient.  It assumes that the pipeline consists of a
    ColumnTransformer followed by a LinearModel.  The output is sorted by
    absolute contribution magnitude.

    Args:
        pipeline: Fitted scikit‑learn Pipeline with 'preprocessor' and 'model'.
        X: DataFrame of a single sample with raw feature values.

    Returns:
        List of (feature_name, contribution) tuples sorted descending.
    """
    # Obtain preprocessed numpy array
    Xt = pipeline.named_steps['preprocessor'].transform(X)
    model = pipeline.named_steps['model']
    if not hasattr(model, 'coef_'):
        return []
    coefs = model.coef_.flatten()
    # scikit 1.8 exposes feature names on the preprocessor
    try:
        feature_names = pipeline.named_steps['preprocessor'].get_feature_names_out()
    except AttributeError:
        # Fallback: use numeric range indices
        feature_names = [f"feat_{i}" for i in range(len(coefs))]
    contributions = Xt[0] * coefs
    pairs = list(zip(feature_names, contributions))
    # Sort by absolute value
    pairs.sort(key=lambda x: abs(x[1]), reverse=True)
    return pairs[:3]


def predict_application(app_dict: Dict) -> Dict:
    """Score a single application and return prediction outputs.

    Args:
        app_dict: Application data as a dictionary.

    Returns:
        A dictionary containing the risk score, class, top factors and completeness.
    """
    pipeline = load_baseline_pipeline()
    X, comp, feature_cols, missing_cols = prepare_features(app_dict)
    # Compute risk probability
    prob = float(pipeline.predict_proba(X)[0, 1])
    risk_class = risk_class_from_score(prob)
    # Compute contributions
    top_factors = compute_contributions(pipeline, X)
    return {
        "risk_score": prob,
        "risk_class": risk_class,
        "top_factors": top_factors,
        "completeness": float(comp),
        "missing_columns": missing_cols,
    }