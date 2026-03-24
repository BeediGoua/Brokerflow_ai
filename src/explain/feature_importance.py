"""
Global feature importance computation.

Provides utilities to extract and format feature importances from both
linear models (via coefficients) and tree models (via the built‑in
``feature_importances_`` attribute).  The caller must supply the list of
feature names in the order used by the model.
"""

import pandas as pd
import numpy as np


def logistic_global_importance(model, feature_names: list) -> pd.DataFrame:
    """Compute absolute coefficient magnitudes for a linear model.

    Args:
        model: Fitted linear model with a ``coef_`` attribute.
        feature_names: Names of the features in the same order as the coefficients.

    Returns:
        DataFrame with columns ``feature`` and ``importance`` sorted descending.
    """
    coefs = model.coef_.flatten()
    importance = pd.DataFrame({
        'feature': feature_names,
        'importance': np.abs(coefs),
    }).sort_values(by='importance', ascending=False)
    return importance


def tree_global_importance(model, feature_names: list) -> pd.DataFrame:
    """Compute feature importance for tree‑based models.

    Args:
        model: Fitted tree model with a ``feature_importances_`` attribute.
        feature_names: Names of the features.

    Returns:
        DataFrame of global importances.
    """
    importances = model.feature_importances_
    return pd.DataFrame({
        'feature': feature_names,
        'importance': importances,
    }).sort_values(by='importance', ascending=False)