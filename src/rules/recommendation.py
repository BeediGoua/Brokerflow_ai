"""
Recommendation orchestrator.

This module ties together the model prediction, completeness, alerts and
business rules to produce a final recommendation string.
"""

from typing import List

from .business_rules import decide_action


def recommend(risk_class: str, completeness: float, alerts: List[str]) -> str:
    """Return the recommended action for an application."""
    return decide_action(risk_class, completeness, alerts)