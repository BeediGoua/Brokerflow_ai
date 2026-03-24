"""
Recommendation orchestrator.

This module ties together the model prediction, completeness, alerts and
business rules to produce a final recommendation string.
"""

from typing import List

from .business_rules import DecisionResult, decide_action, decide_action_v2


def recommend(risk_class: str, completeness: float, alerts: List[str]) -> str:
    """Return the recommended action for an application."""
    return decide_action(risk_class, completeness, alerts)


def recommend_detailed(
    risk_score: float,
    threshold: float,
    completeness: float,
    alerts: List[str],
    alert_severity: str | None = None,
) -> DecisionResult:
    """Return a structured policy decision for calibrated runtime scoring."""
    return decide_action_v2(
        risk_score=risk_score,
        threshold=threshold,
        completeness=completeness,
        alerts=alerts,
        alert_severity=alert_severity,
    )