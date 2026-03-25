"""Train baseline/challenger models and select a winner.

This module benchmarks three candidates on the synthetic underwriting flow:

1. Baseline: calibrated logistic regression.
2. Challenger: calibrated LightGBM.
3. Challenger: calibrated stacking ensemble (logreg + LightGBM).

It exports a comparison table and winner metadata under ``models/``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import joblib
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import StackingClassifier

from src.config.logging import get_logger
from src.data.generate_synthetic_cases import generate_datasets
from src.data.preprocess import preprocess_applications
from src.features.build_features import add_engineered_features
from src.features.completeness import completeness_score

logger = get_logger(__name__)

OUTPUT_DIR = Path("models")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _select_feature_columns(df: pd.DataFrame) -> list[str]:
    exclude = {
        "application_id",
        "customer_id",
        "snapshot_date",
        "free_text_note",
        "target_risk_flag",
    }
    return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]


def _best_f1_threshold(y_true: pd.Series, y_prob: pd.Series) -> float:
    thresholds = [i / 100 for i in range(5, 96)]
    best_thr = 0.5
    best_f1 = -1.0
    for thr in thresholds:
        y_pred = (y_prob >= thr).astype(int)
        score = f1_score(y_true, y_pred, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_thr = thr
    return best_thr


def _compute_metrics(y_true: pd.Series, y_prob: pd.Series, threshold: float) -> Dict[str, float]:
    y_pred_05 = (y_prob >= 0.5).astype(int)
    y_pred_best = (y_prob >= threshold).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "brier": float(brier_score_loss(y_true, y_prob)),
        "threshold_best_f1": float(threshold),
        "accuracy@0.5": float(accuracy_score(y_true, y_pred_05)),
        "precision@0.5": float(precision_score(y_true, y_pred_05, zero_division=0)),
        "recall@0.5": float(recall_score(y_true, y_pred_05, zero_division=0)),
        "f1@0.5": float(f1_score(y_true, y_pred_05, zero_division=0)),
        "accuracy@best": float(accuracy_score(y_true, y_pred_best)),
        "precision@best": float(precision_score(y_true, y_pred_best, zero_division=0)),
        "recall@best": float(recall_score(y_true, y_pred_best, zero_division=0)),
        "f1@best": float(f1_score(y_true, y_pred_best, zero_division=0)),
    }


def _winner_score(metrics: Dict[str, float]) -> float:
    """Business-oriented score prioritizing risk detection and calibration."""
    return (
        0.45 * metrics["recall@best"]
        + 0.35 * metrics["f1@best"]
        + 0.15 * metrics["roc_auc"]
        - 0.05 * metrics["brier"]
    )


def _build_models(feature_cols: list[str]) -> Dict[str, object]:
    preprocessor = ColumnTransformer(
        transformers=[("scaler", StandardScaler(), feature_cols)],
        remainder="drop",
    )

    baseline_logreg = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(max_iter=400, n_jobs=-1, random_state=42)),
        ]
    )

    lightgbm = LGBMClassifier(
        objective="binary",
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
    )

    base_lr = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(max_iter=300, n_jobs=-1, random_state=42)),
        ]
    )
    base_lgbm = LGBMClassifier(
        objective="binary",
        n_estimators=220,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
    )
    challenger_ensemble = StackingClassifier(
        estimators=[("lr", base_lr), ("lgbm", base_lgbm)],
        final_estimator=LogisticRegression(max_iter=300, random_state=42),
        stack_method="predict_proba",
        passthrough=False,
        cv=3,
        n_jobs=-1,
    )

    return {
        "baseline_logreg": baseline_logreg,
        "lightgbm": lightgbm,
        "stacking_logreg_lgbm": challenger_ensemble,
    }


def run_challenger_benchmark(n_samples: int = 1500) -> Tuple[pd.DataFrame, str]:
    apps, _, _ = generate_datasets(n_samples=n_samples)
    apps = preprocess_applications(apps)
    apps = add_engineered_features(apps)
    apps["completeness"] = completeness_score(apps)

    feature_cols = _select_feature_columns(apps)
    X = apps[feature_cols]
    y = apps["target_risk_flag"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y,
    )

    models = _build_models(feature_cols)
    rows = []
    fitted_models: Dict[str, object] = {}

    for model_name, base_model in models.items():
        logger.info("Training %s", model_name)
        calibrated = CalibratedClassifierCV(base_model, method="sigmoid", cv=3)
        calibrated.fit(X_train, y_train)

        y_prob = calibrated.predict_proba(X_test)[:, 1]
        best_thr = _best_f1_threshold(y_test, y_prob)
        metrics = _compute_metrics(y_test, y_prob, best_thr)
        score = _winner_score(metrics)

        rows.append({"model": model_name, **metrics, "business_score": score})
        fitted_models[model_name] = calibrated

        model_path = OUTPUT_DIR / f"{model_name}_calibrated.pkl"
        joblib.dump(calibrated, model_path)
        logger.info("Saved %s to %s", model_name, model_path)

    results = pd.DataFrame(rows).sort_values("business_score", ascending=False).reset_index(drop=True)
    winner_name = str(results.iloc[0]["model"])

    metrics_path = OUTPUT_DIR / "challenger_metrics.csv"
    results.to_csv(metrics_path, index=False)

    winner_payload = {
        "winner_model": winner_name,
        "selection_rule": "0.45*recall@best + 0.35*f1@best + 0.15*roc_auc - 0.05*brier",
        "winner_threshold_best_f1": float(results.iloc[0]["threshold_best_f1"]),
    }
    winner_path = OUTPUT_DIR / "challenger_winner.json"
    with winner_path.open("w", encoding="utf-8") as f:
        json.dump(winner_payload, f, indent=2)

    logger.info("Saved comparison table to %s", metrics_path)
    logger.info("Saved winner metadata to %s", winner_path)
    logger.info("Winner: %s", winner_name)

    return results, winner_name


def main() -> None:
    logger.info("Running champion-challenger benchmark...")
    results, winner = run_challenger_benchmark(n_samples=1500)
    logger.info("Top 3:\n%s", results.head(3).to_string(index=False))
    logger.info("Selected winner: %s", winner)


if __name__ == "__main__":
    main()
