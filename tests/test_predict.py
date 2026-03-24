"""
Tests for prediction logic.
"""

from src.data.generate_synthetic_cases import generate_datasets
from src.models.predict import predict_application, risk_class_from_score


def test_predict_application_returns_valid_outputs():
    apps, _, _ = generate_datasets(n_samples=10)
    sample = apps.iloc[0].to_dict()
    result = predict_application(sample)
    assert 0.0 <= result["risk_score"] <= 1.0
    assert result["risk_class"] in {"Low", "Medium", "High"}
    assert len(result["top_factors"]) <= 3
    assert 0.0 <= result["completeness"] <= 1.0