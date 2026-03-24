"""
Tests for business rule logic.
"""

from src.rules.business_rules import decide_action


def test_decide_action_requests_documents_when_incomplete():
    action = decide_action(risk_class="Low", completeness=0.8, alerts=[])
    assert action == "REQUEST_DOCUMENTS"


def test_decide_action_escalates_on_alerts():
    action = decide_action(risk_class="Low", completeness=1.0, alerts=["Missing doc"])
    assert action == "ESCALATE"


def test_decide_action_escalates_on_high_risk():
    action = decide_action(risk_class="High", completeness=1.0, alerts=[])
    assert action == "ESCALATE"


def test_decide_action_reviews_on_medium_risk():
    action = decide_action(risk_class="Medium", completeness=1.0, alerts=[])
    assert action == "REVIEW"


def test_decide_action_accepts_on_low_risk():
    action = decide_action(risk_class="Low", completeness=1.0, alerts=[])
    assert action == "ACCEPTABLE"