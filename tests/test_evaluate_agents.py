"""Simple tests for agent evaluation script."""

from __future__ import annotations

from src.eval.evaluate_agents import evaluate_agent_cases, evaluate_from_file


def test_evaluate_agent_cases_returns_expected_keys() -> None:
    cases = [
        {
            "case_id": "t1",
            "application": {
                "application_id": "APP-T1",
                "customer_id": "CUST-T1",
                "snapshot_date": "2025-01-10",
                "employment_status": "unemployed",
                "monthly_income": 1200,
                "requested_amount": 15000,
                "debt_to_income_ratio": 0.7,
                "prior_late_payments": 2,
                "has_prior_default": 0,
                "free_text_note": "stable job and needs fast approval",
                "documents": [],
            },
            "expected_risk_signals": ["urgent_need"],
            "expected_alerts_codes": ["INC_EMPLOYMENT_NOTE_CONTRADICTION"],
            "expected_recommendation": "REVIEW",
        }
    ]

    out = evaluate_agent_cases(cases)

    assert "json_validity_rate" in out
    assert "alert_precision" in out
    assert "alert_recall" in out
    assert "summary_coherence" in out
    assert "latency_p50_ms" in out
    assert "latency_p95_ms" in out
    assert "fallback_rate" in out


def test_evaluate_from_file_runs_on_seed_dataset() -> None:
    out = evaluate_from_file("data/agent_eval_cases.json")
    assert out["cases_count"] >= 1
