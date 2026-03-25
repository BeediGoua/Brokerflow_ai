"""
Model evaluation utilities.

This module contains helper functions to evaluate trained models on a
hold‑out set.  It calculates a range of commonly used classification
metrics.  The functions are generic enough to evaluate both linear and tree
models.
"""

from typing import Dict, Any

import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, accuracy_score, precision_score, recall_score, f1_score, brier_score_loss


def evaluate_predictions(y_true: pd.Series, y_prob: pd.Series, y_pred: pd.Series) -> Dict[str, Any]:
    """Compute a suite of evaluation metrics for binary classification.

    Args:
        y_true: Ground truth binary labels.
        y_prob: Predicted probabilities for the positive class.
        y_pred: Predicted class labels.

    Returns:
        Dictionary of metric names to values.
    """
    metrics = {
        "roc_auc": roc_auc_score(y_true, y_prob),
        "pr_auc": average_precision_score(y_true, y_prob),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred),
        "brier_score": brier_score_loss(y_true, y_prob),
    }
    return metrics