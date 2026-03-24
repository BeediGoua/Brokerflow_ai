"""Tests for the v2 calibrated real-runtime scoring endpoint."""

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.data.generate_synthetic_cases import generate_datasets


client = TestClient(create_app())


def test_score_v2_endpoint_returns_prediction(monkeypatch):
    apps, _, _ = generate_datasets(n_samples=5)
    sample = apps.iloc[0].to_dict()
    sample.pop("target_risk_flag", None)

    monkeypatch.setattr(
        "src.api.routes.scoring_real.predict_application_real",
        lambda app_dict: {
            "risk_score": 0.42,
            "risk_class": "Medium",
            "top_factors": [("due_vs_loan_ratio", 0.3), ("loanamount", 0.1)],
            "completeness": 0.9,
            "missing_columns": [],
            "threshold_used": 0.23,
            "model_source": "unit-test",
        },
    )

    response = client.post("/v2/score", json=sample)
    assert response.status_code == 200
    payload = response.json()
    assert "risk_score" in payload
    assert 0.0 <= payload["risk_score"] <= 1.0
    assert payload["risk_class"] in {"Low", "Medium", "High"}
    assert payload["recommendation"] in {"ACCEPTABLE", "REVIEW", "REQUEST_DOCUMENTS", "ESCALATE"}
    assert isinstance(payload.get("alerts_structured"), list)
    assert isinstance(payload.get("decision_reason_codes"), list)
    assert payload.get("decision_alert_severity") in {"none", "low", "medium", "high"}
    assert payload.get("decision_completeness_bucket") in {"critical", "partial", "good"}
