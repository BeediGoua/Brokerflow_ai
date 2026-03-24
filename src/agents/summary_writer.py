"""
Summary writer agent.

This agent composes the final summary for the underwriter by calling the
narrative utility.  It abstracts away the narrative template from the
rest of the pipeline.
"""

from typing import List, Tuple

from src.explain.narrative import generate_summary


def write_summary(risk_class: str, risk_score: float, top_factors: List[Tuple[str, float]], recommendation: str, alerts: List[str]) -> str:
    """Generate a summary sentence for the underwriter."""
    return generate_summary(risk_class, risk_score, top_factors, recommendation, alerts)