"""
Local explanation utilities using SHAP.

This module exposes helper functions to compute SHAP values for a single
sample.  It automatically chooses the appropriate explainer for linear
versus tree models.  For heavy models, caching the explainer across
requests is recommended.
"""

from functools import lru_cache
from typing import Dict, List, Tuple

import pandas as pd
import shap


@lru_cache(maxsize=1)
def _get_explainer(model):
    """Return a SHAP explainer appropriate for the model."""
    try:
        # Tree models
        return shap.TreeExplainer(model)
    except Exception:
        # Fallback to linear models
        return shap.LinearExplainer(model, masker=None)


def shap_local_contributions(model, X: pd.DataFrame) -> List[Tuple[str, float]]:
    """Compute local SHAP contributions for a single row.

    Args:
        model: Trained model (lightGBM or linear).
        X: DataFrame with a single row of features.

    Returns:
        List of (feature, contribution) pairs sorted by absolute value.
    """
    explainer = _get_explainer(model)
    shap_values = explainer.shap_values(X)
    # shap_values for binary classification returns list for each class
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    values = shap_values[0]
    feature_names = X.columns
    pairs = list(zip(feature_names, values))
    pairs.sort(key=lambda x: abs(x[1]), reverse=True)
    return pairs[:3]