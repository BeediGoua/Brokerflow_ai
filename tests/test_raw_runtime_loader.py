"""Tests for the calibrated raw-runtime loader and prediction path."""

import numpy as np

from src.data.generate_synthetic_cases import generate_datasets
from src.models.raw_runtime_loader import RawRuntimeArtifacts, predict_application_real


class _FakeModel:
    def predict_proba(self, X):
        # Return deterministic probabilities for a single-row input.
        return np.array([[0.2, 0.8] for _ in range(len(X))])


def test_predict_application_real_returns_valid_payload(monkeypatch):
    apps, _, _ = generate_datasets(n_samples=5)
    sample = apps.iloc[0].to_dict()

    artifacts = RawRuntimeArtifacts(
        model=_FakeModel(),
        feature_cols=["loanamount", "due_vs_loan_ratio", "seg_loanamount_medium"],
        threshold=0.23,
        coefficients={"loanamount": 0.001, "due_vs_loan_ratio": 1.2},
        source="unit-test",
    )

    monkeypatch.setattr("src.models.raw_runtime_loader._get_artifacts", lambda: artifacts)

    result = predict_application_real(sample)

    assert 0.0 <= result["risk_score"] <= 1.0
    assert result["risk_class"] in {"Low", "Medium", "High"}
    assert isinstance(result["top_factors"], list)
    assert len(result["top_factors"]) <= 3
    assert 0.0 <= result["completeness"] <= 1.0
    assert result["threshold_used"] == 0.23
    assert result["model_source"] == "unit-test"
