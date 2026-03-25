"""
Train a baseline logistic regression model.

This script loads the synthetic applications dataset, applies preprocessing and
feature engineering, then trains a logistic regression classifier on the
engineered features.  The trained pipeline (preprocessor + model) is
persisted to disk under ``models/baseline_logreg.pkl``.  A separate
preprocessor file is also saved for use by other models.

Run this module with ``python -m src.models.train_baseline``.
"""

import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report, roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from src.data.generate_synthetic_cases import generate_datasets
from src.data.preprocess import preprocess_applications
from src.features.build_features import add_engineered_features
from src.features.completeness import completeness_score
from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)


def _select_feature_columns(df: pd.DataFrame) -> list:
    """Select numeric columns to use for the logistic regression model."""
    # Exclude identifier, target and free text
    exclude = {
        "application_id", "customer_id", "snapshot_date", "free_text_note", "target_risk_flag"
    }
    numeric_cols = [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]
    return numeric_cols


def train_baseline_model(n_samples: int = 500) -> Pipeline:
    """Generate synthetic data and train a logistic regression pipeline.

    Args:
        n_samples: Number of samples to use for training.  Smaller numbers
            speed up testing at the expense of performance.

    Returns:
        A fitted scikit‑learn Pipeline object.
    """
    # Generate synthetic data in memory
    apps, _, _ = generate_datasets(n_samples=n_samples)
    # Preprocess and engineer features
    apps = preprocess_applications(apps)
    apps = add_engineered_features(apps)
    # Create completeness as a feature too
    apps["completeness"] = completeness_score(apps)
    # Select features and target
    feature_cols = _select_feature_columns(apps)
    X = apps[feature_cols]
    y = apps["target_risk_flag"]
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    # Preprocessor: scale numeric features
    preprocessor = ColumnTransformer(
        transformers=[('scaler', StandardScaler(), feature_cols)], remainder='drop'
    )
    # Model
    clf = LogisticRegression(max_iter=200, n_jobs=-1)
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', clf),
    ])
    # Fit
    pipeline.fit(X_train, y_train)
    # Evaluate
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    y_pred = pipeline.predict(X_test)
    auc = roc_auc_score(y_test, y_prob)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    logger.info(
        f"Baseline logistic regression metrics -- AUC: {auc:.3f}, Acc: {acc:.3f}, "
        f"Prec: {prec:.3f}, Rec: {rec:.3f}, F1: {f1:.3f}"
    )
    logger.debug(classification_report(y_test, y_pred))
    return pipeline


def save_model(model: Pipeline, model_path: str) -> None:
    """Persist the trained model to disk."""
    model_file = Path(model_path)
    model_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_file)
    # Optionally save the preprocessor separately for other models
    preproc_path = settings.preprocessor_path
    joblib.dump(model.named_steps['preprocessor'], preproc_path)
    logger.info(f"Saved baseline model to {model_file}")
    logger.info(f"Saved preprocessor to {preproc_path}")


def main() -> None:
    """Entry point for training the baseline model."""
    logger.info("Training baseline logistic regression model…")
    pipeline = train_baseline_model(n_samples=1000)
    save_model(pipeline, settings.model_path)


if __name__ == "__main__":
    main()