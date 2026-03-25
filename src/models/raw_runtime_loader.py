"""Runtime loader for the calibrated real-data model artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import pandas as pd

from src.config.settings import settings
from src.models.model_release import ensure_runtime_assets
from src.models.predict import risk_class_from_score
from src.models.raw_runtime_feature_adapter import build_raw_runtime_feature_frame


@dataclass
class RawRuntimeArtifacts:
    model: object
    feature_cols: List[str]
    threshold: float
    coefficients: Dict[str, float]
    source: str


def _load_coefficients(path: Path) -> Dict[str, float]:
    if not path.exists():
        return {}
    try:
        coef_df = pd.read_csv(path, index_col=0)
        if "coef" in coef_df.columns:
            series = coef_df["coef"]
        else:
            series = coef_df.iloc[:, 0]
        return {str(k): float(v) for k, v in series.to_dict().items()}
    except Exception:
        return {}


def _load_threshold(path: Path) -> float:
    if not path.exists():
        return 0.5
    try:
        return float(path.read_text().strip())
    except Exception:
        return 0.5


def load_raw_runtime_artifacts() -> RawRuntimeArtifacts:
    """Load calibrated runtime artifacts with safe fallbacks."""
    bundle_path = Path(settings.raw_runtime_bundle_path)
    fallback_artifact_path = Path(settings.raw_runtime_artifact_path)
    threshold_path = Path(settings.raw_runtime_threshold_path)
    coefficients_path = Path(settings.raw_runtime_coefficients_path)

    # If runtime assets are missing locally, try GitHub Release bootstrap.
    if not bundle_path.exists() and not fallback_artifact_path.exists():
        try:
            ensure_runtime_assets()
        except Exception as exc:
            raise FileNotFoundError(
                "Aucun artefact runtime local et echec du bootstrap Release. "
                "Publiez les assets via `make release-upload` ou telechargez-les avec "
                "`python -m src.models.model_release --download`."
            ) from exc

    if bundle_path.exists():
        loaded = joblib.load(bundle_path)
        if isinstance(loaded, dict) and "model" in loaded and "features" in loaded:
            return RawRuntimeArtifacts(
                model=loaded["model"],
                feature_cols=list(loaded["features"]),
                threshold=float(loaded.get("threshold", _load_threshold(threshold_path))),
                coefficients={str(k): float(v) for k, v in loaded.get("coefficients", {}).items()},
                source=str(bundle_path),
            )

    if not fallback_artifact_path.exists():
        raise FileNotFoundError(
            "Aucun artefact runtime réel trouvé. Exécutez le notebook 05 ou générez "
            f"{settings.raw_runtime_bundle_path}."
        )

    loaded = joblib.load(fallback_artifact_path)
    if not isinstance(loaded, dict) or "model" not in loaded or "features" not in loaded:
        raise ValueError("Format d'artefact invalide pour le runtime réel.")

    return RawRuntimeArtifacts(
        model=loaded["model"],
        feature_cols=list(loaded["features"]),
        threshold=_load_threshold(threshold_path),
        coefficients=_load_coefficients(coefficients_path),
        source=str(fallback_artifact_path),
    )


@lru_cache(maxsize=1)
def _get_artifacts() -> RawRuntimeArtifacts:
    return load_raw_runtime_artifacts()


def _top_factors(X: pd.DataFrame, coefficients: Dict[str, float], top_k: int = 3) -> List[Tuple[str, float]]:
    row = X.iloc[0]
    if coefficients:
        pairs = []
        for col in X.columns:
            coef = coefficients.get(col)
            if coef is None:
                continue
            pairs.append((col, float(row[col]) * float(coef)))
        pairs.sort(key=lambda x: abs(x[1]), reverse=True)
        if pairs:
            return pairs[:top_k]

    # Fallback if coefficients are unavailable.
    pairs = [(col, float(row[col])) for col in X.columns]
    pairs.sort(key=lambda x: abs(x[1]), reverse=True)
    return pairs[:top_k]


def predict_application_real(app_dict: Dict) -> Dict:
    """Predict risk score using calibrated raw-runtime artifacts."""
    artifacts = _get_artifacts()
    X, completeness, missing_columns = build_raw_runtime_feature_frame(app_dict, artifacts.feature_cols)

    prob = float(artifacts.model.predict_proba(X)[0, 1])
    risk_class = risk_class_from_score(prob)
    top_factors = _top_factors(X, artifacts.coefficients)

    return {
        "risk_score": prob,
        "risk_class": risk_class,
        "top_factors": top_factors,
        "completeness": float(completeness),
        "missing_columns": missing_columns,
        "threshold_used": float(artifacts.threshold),
        "model_source": artifacts.source,
    }
