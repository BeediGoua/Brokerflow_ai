"""
High‑level business rules for underwriter recommendations.

The decision logic sits on top of the model predictions and completeness
scores.  Real underwriting systems would include far more complex and
regulatory‑driven logic; here we provide a minimal example to illustrate
how rules can override pure model output.
"""

from dataclasses import dataclass
from typing import List


# V2 thresholds tuned for calibrated probabilities and operational review.
CRITICAL_COMPLETENESS = 0.60
PARTIAL_COMPLETENESS = 0.90


@dataclass(frozen=True)
class DecisionResult:
    """Structured decision output for auditable business-rule decisions."""

    action: str
    alert_severity: str
    completeness_bucket: str
    reason_codes: List[str]


def classify_alert_severity(alerts: List[str]) -> str:
    """Map raw alert strings to coarse severity buckets.

    Heuristic mapping:
    - `high`: contradictions/inconsistencies in applicant narrative
    - `low`: missing-document style alerts
    - `none`: no alerts
    """
    if not alerts:
        return "none"

    lowered = [a.lower() for a in alerts]
    high_markers = ["inconsistency", "incoherence", "contradiction"]
    for msg in lowered:
        if any(marker in msg for marker in high_markers):
            return "high"
    return "low"


def bucket_completeness(completeness: float) -> str:
    """Bucketize completeness for simpler policy logic."""
    if completeness < CRITICAL_COMPLETENESS:
        return "critical"
    if completeness < PARTIAL_COMPLETENESS:
        return "partial"
    return "good"


def decide_action_v2(
    risk_score: float,
    threshold: float,
    completeness: float,
    alerts: List[str],
    alert_severity: str | None = None,
) -> DecisionResult:
    """Improved policy using calibrated score, threshold and alert severity.

    Decision policy:
    1. High-severity inconsistency alerts => ESCALATE.
    2. Very high risk (>= 0.50) with incomplete file (< 0.90) => ESCALATE.
    3. Risk >= operational threshold and critical completeness => REQUEST_DOCUMENTS.
    4. Risk >= operational threshold and non-critical completeness => REVIEW.
    5. Risk below threshold and incomplete file => REQUEST_DOCUMENTS.
    6. Else => ACCEPTABLE.
    """
    severity = alert_severity if alert_severity in {"none", "low", "medium", "high"} else classify_alert_severity(alerts)
    completeness_bucket = bucket_completeness(completeness)
    reason_codes: List[str] = []

    if severity == "high":
        reason_codes.append("HIGH_SEVERITY_ALERT")
        return DecisionResult("ESCALATE", severity, completeness_bucket, reason_codes)

    if risk_score >= 0.50 and completeness < PARTIAL_COMPLETENESS:
        reason_codes.extend(["VERY_HIGH_RISK", "INCOMPLETE_FILE"])
        return DecisionResult("ESCALATE", severity, completeness_bucket, reason_codes)

    if risk_score >= threshold:
        reason_codes.append("ABOVE_OPERATIONAL_THRESHOLD")
        if completeness_bucket == "critical":
            reason_codes.append("CRITICAL_COMPLETENESS")
            return DecisionResult("REQUEST_DOCUMENTS", severity, completeness_bucket, reason_codes)
        reason_codes.append("MANUAL_REVIEW_REQUIRED")
        return DecisionResult("REVIEW", severity, completeness_bucket, reason_codes)

    if completeness_bucket != "good":
        reason_codes.append("INCOMPLETE_FILE")
        return DecisionResult("REQUEST_DOCUMENTS", severity, completeness_bucket, reason_codes)

    reason_codes.append("LOW_RISK_COMPLETE_FILE")
    return DecisionResult("ACCEPTABLE", severity, completeness_bucket, reason_codes)