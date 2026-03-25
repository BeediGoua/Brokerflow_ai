"""
Train a LightGBM classifier as the candidate model.

LightGBM is a gradient boosting algorithm that can handle non‑linear
relationships and feature interactions.  This script follows a similar
pattern to ``train_baseline.py`` but uses the LightGBM classifier.  It
saves the trained model to ``models/candidate_lgbm.pkl``.

Run this module with ``python -m src.models.train_lgbm``.
"""

import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

from lightgbm import LGBMClassifier

from src.data.generate_synthetic_cases import generate_datasets
from src.data.preprocess import preprocess_applications
from src.features.build_features import add_engineered_features
from src.features.completeness import completeness_score
from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)


def _select_feature_columns(df: pd.DataFrame) -> list:
    exclude = {
        "application_id", "customer_id", "snapshot_date", "free_text_note", "target_risk_flag"
    }
    numeric_cols = [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]
    return numeric_cols


def train_lgbm_model(n_samples: int = 1000) -> LGBMClassifier:
    """Generate synthetic data and train a LightGBM classifier.

    Args:
        n_samples: Number of samples to use for training.

    Returns:
        A fitted LightGBM model.
    """
    apps, _, _ = generate_datasets(n_samples=n_samples)
    apps = preprocess_applications(apps)
    apps = add_engineered_features(apps)
    apps["completeness"] = completeness_score(apps)
    feature_cols = _select_feature_columns(apps)
    X = apps[feature_cols]
    y = apps["target_risk_flag"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    model = LGBMClassifier(
        objective="binary",
        n_estimators=200,
        learning_rate=0.05,
        max_depth=-1,
        random_state=42,
    )
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    auc = roc_auc_score(y_test, y_prob)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    logger.info(
        f"LightGBM metrics -- AUC: {auc:.3f}, Acc: {acc:.3f}, Prec: {prec:.3f}, Rec: {rec:.3f}, F1: {f1:.3f}"
    )
    logger.debug(classification_report(y_test, y_pred))
    return model


def save_model(model: LGBMClassifier, model_path: str) -> None:
    model_file = Path(model_path)
    model_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_file)
    logger.info(f"Saved LightGBM model to {model_file}")


def main() -> None:
    logger.info("Training LightGBM model…")
    model = train_lgbm_model(n_samples=1000)
    save_model(model, "models/candidate_lgbm.pkl")


if __name__ == "__main__":
    main()