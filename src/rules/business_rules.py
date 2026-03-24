"""
High‑level business rules for underwriter recommendations.

The decision logic sits on top of the model predictions and completeness
scores.  Real underwriting systems would include far more complex and
regulatory‑driven logic; here we provide a minimal example to illustrate
how rules can override pure model output.
"""

from typing import List


def decide_action(risk_class: str, completeness: float, alerts: List[str]) -> str:
    """Determine the recommended action based on risk, completeness and alerts.

    Args:
        risk_class: Discrete risk class (Low/Medium/High).
        completeness: Completeness score between 0 and 1.
        alerts: List of detected alerts (inconsistencies or missing documents).

    Returns:
        One of ``ACCEPTABLE``, ``REVIEW``, ``REQUEST_DOCUMENTS`` or ``ESCALATE``.
    """
    # Missing critical information always forces a request
    if completeness < 1.0:
        return "REQUEST_DOCUMENTS"
    # Incoherences flagged by agents trigger escalation
    if alerts:
        return "ESCALATE"
    if risk_class == "High":
        return "ESCALATE"
    if risk_class == "Medium":
        return "REVIEW"
    return "ACCEPTABLE"