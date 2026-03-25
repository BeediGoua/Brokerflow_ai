"""
Tests for FastAPI endpoints.
"""

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.data.generate_synthetic_cases import generate_datasets


client = TestClient(create_app())


def test_health_endpoint():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_score_endpoint_returns_prediction():
    apps, _, _ = generate_datasets(n_samples=5)
    sample = apps.iloc[0].to_dict()
    # Remove target for inference
    sample.pop("target_risk_flag", None)
    response = client.post("/v1/score", json=sample)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_class"] in {"Low", "Medium", "High"}
    assert "alerts_structured" in data
    assert "decision_reason_codes" in data


def test_review_detailed_endpoint_returns_structured_alerts():
    apps, _, _ = generate_datasets(n_samples=3)
    sample = apps.iloc[0].to_dict()
    sample["employment_status"] = "unemployed"
    sample["free_text_note"] = "stable job; previous loans paid"
    response = client.post("/v1/review-detailed", json=sample)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    if payload:
        first = payload[0]
        assert "code" in first
        assert "severity" in first
        assert "message" in first
        assert "source" in first


def test_review_detailed_uses_documents_payload_for_alerts():
    apps, _, _ = generate_datasets(n_samples=3)
    sample = apps.iloc[0].to_dict()
    sample["documents"] = [
        {
            "document_id": "doc-1",
            "application_id": sample["application_id"],
            "document_type": "income_proof",
            "is_required": True,
            "is_provided": False,
        }
    ]

    response = client.post("/v1/review-detailed", json=sample)
    assert response.status_code == 200
    payload = response.json()
    assert any(item.get("code") == "DOC_REQUIRED_MISSING" for item in payload)