"""Build consolidated runtime bundle and manifest for calibrated raw model."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd


def _load_coefficients(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    coef_df = pd.read_csv(path, index_col=0)
    if "coef" in coef_df.columns:
        series = coef_df["coef"]
    else:
        series = coef_df.iloc[:, 0]
    return {str(k): float(v) for k, v in series.to_dict().items()}


def build_runtime_bundle(project_root: Path) -> tuple[Path, Path]:
    models_dir = project_root / "models"
    src_artifact = models_dir / "logreg_raw.pkl"
    threshold_path = models_dir / "best_threshold.txt"
    coefficients_path = models_dir / "model_coefficients.csv"

    if not src_artifact.exists():
        raise FileNotFoundError(f"Missing source artifact: {src_artifact}")

    loaded = joblib.load(src_artifact)
    if not isinstance(loaded, dict) or "model" not in loaded or "features" not in loaded:
        raise ValueError("Invalid source artifact format in logreg_raw.pkl")

    threshold = 0.5
    if threshold_path.exists():
        try:
            threshold = float(threshold_path.read_text().strip())
        except Exception:
            threshold = 0.5

    coefficients = _load_coefficients(coefficients_path)
    feature_cols = [str(c) for c in loaded["features"]]

    runtime_bundle = {
        "model": loaded["model"],
        "features": feature_cols,
        "threshold": threshold,
        "coefficients": coefficients,
        "model_name": "logreg_raw_calibrated",
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    bundle_path = models_dir / "logreg_raw_runtime_bundle.joblib"
    manifest_path = models_dir / "logreg_raw_runtime_manifest.json"

    joblib.dump(runtime_bundle, bundle_path)

    manifest = {
        "artifact": str(bundle_path.relative_to(project_root)),
        "model_name": runtime_bundle["model_name"],
        "schema_version": runtime_bundle["schema_version"],
        "created_at": runtime_bundle["created_at"],
        "threshold": threshold,
        "n_features": len(feature_cols),
        "features": feature_cols,
        "coefficients_available": bool(coefficients),
        "source_artifact": str(src_artifact.relative_to(project_root)),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return bundle_path, manifest_path


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    bundle_path, manifest_path = build_runtime_bundle(project_root)
    print(f"Runtime bundle created: {bundle_path}")
    print(f"Runtime manifest created: {manifest_path}")


if __name__ == "__main__":
    main()
