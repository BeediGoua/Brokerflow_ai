"""Tests for improved V2 business-rule policy."""

from src.rules.business_rules import (
    bucket_completeness,
    classify_alert_severity,
    decide_action_v2,
)


def test_alert_severity_high_on_inconsistency():
    severity = classify_alert_severity([
        "Inconsistency: applicant declares unemployed but note mentions a stable job"
    ])
    assert severity == "high"


def test_alert_severity_low_on_missing_docs_only():
    severity = classify_alert_severity(["Missing required document: bank_statement"])
    assert severity == "low"


def test_completeness_bucket_values():
    assert bucket_completeness(0.50) == "critical"
    assert bucket_completeness(0.75) == "partial"
    assert bucket_completeness(0.95) == "good"


def test_v2_escalates_on_high_severity_alert():
    decision = decide_action_v2(
        risk_score=0.10,
        threshold=0.23,
        completeness=1.0,
        alerts=["Inconsistency: prior late payments but note claims none"],
    )
    assert decision.action == "ESCALATE"


def test_v2_reviews_above_threshold_with_noncritical_completeness():
    decision = decide_action_v2(
        risk_score=0.30,
        threshold=0.23,
        completeness=0.80,
        alerts=[],
    )
    assert decision.action == "REVIEW"


def test_v2_requests_documents_below_threshold_when_incomplete():
    decision = decide_action_v2(
        risk_score=0.10,
        threshold=0.23,
        completeness=0.80,
        alerts=[],
    )
    assert decision.action == "REQUEST_DOCUMENTS"


def test_v2_accepts_low_risk_complete_no_alerts():
    decision = decide_action_v2(
        risk_score=0.10,
        threshold=0.23,
        completeness=0.95,
        alerts=[],
    )
    assert decision.action == "ACCEPTABLE"
