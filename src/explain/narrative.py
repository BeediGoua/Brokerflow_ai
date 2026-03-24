"""
Narrative generation utilities.

This module defines helper functions to turn numerical model outputs and
feature contributions into concise, human‑readable explanations.  The
narratives are intentionally simple; you can extend them to include
multiple languages and more sophisticated templates.
"""

from typing import List, Tuple


def generate_summary(risk_class: str, risk_score: float, top_factors: List[Tuple[str, float]], recommendation: str, alerts: List[str]) -> str:
    """Compose a one‑paragraph summary for the underwriter.

    Args:
        risk_class: Discrete class (Low/Medium/High).
        risk_score: Continuous probability of default.
        top_factors: List of top (feature, contribution) pairs.
        recommendation: Suggested action.
        alerts: List of detected inconsistencies or missing items.

    Returns:
        A multi‑sentence string summarising the application.
    """
    score_pct = f"{risk_score * 100:.1f}%"
    factors_desc = ", ".join([f"{feat} ({contrib:+.2f})" for feat, contrib in top_factors]) if top_factors else "no strong drivers"
    alert_desc = "; ".join(alerts) if alerts else "no alerts"
    summary = (
        f"The application has been classified as **{risk_class}** risk with an estimated default probability of {score_pct}. "
        f"Key factors influencing this assessment include: {factors_desc}. "
        f"Detected alerts: {alert_desc}. "
        f"Recommended action: **{recommendation}**."
    )
    return summary