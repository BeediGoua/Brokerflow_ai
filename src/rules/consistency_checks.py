"""Check for inconsistencies between structured data, free-text notes and documents.

This module now exposes both legacy string alerts and structured alert records
with code/severity metadata for policy decisions and auditability.
"""

from typing import Any, Dict, List


HIGH_DEBT_BURDEN_THRESHOLD = 0.60
LOAN_TO_INCOME_MULTIPLIER_LIMIT = 10.0


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _make_alert(code: str, severity: str, message: str, source: str, confidence: float = 1.0) -> Dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "source": source,
        "confidence": float(confidence),
    }


def check_inconsistency_items(app: Dict, parsed_note: Dict, documents: List[Dict]) -> List[Dict[str, Any]]:
    """Return structured alerts with code and severity taxonomy."""
    alerts: List[Dict[str, Any]] = []

    # Example 1: employment-status contradiction between structure and text.
    employment_status = str(app.get("employment_status", "")).lower()
    if employment_status == "unemployed" and parsed_note.get("mentions_stable_job"):
        alerts.append(
            _make_alert(
                code="INC_EMPLOYMENT_NOTE_CONTRADICTION",
                severity="high",
                message="Inconsistency: applicant declares unemployed but note mentions a stable job",
                source="cross_check",
            )
        )

    # Example 2: missing required documents.
    for doc in documents:
        if doc.get("is_required") and not doc.get("is_provided"):
            doc_type = str(doc.get("document_type") or "unknown_document")
            alerts.append(
                _make_alert(
                    code="DOC_REQUIRED_MISSING",
                    severity="medium",
                    message=f"Missing required document: {doc_type}",
                    source="documents",
                )
            )

    # Example 3: note explicitly claims missing docs.
    if parsed_note.get("mentions_missing_documents"):
        alerts.append(
            _make_alert(
                code="NOTE_MENTIONS_MISSING_DOCUMENTS",
                severity="low",
                message="Note indicates missing documents",
                source="note_parser",
                confidence=0.9,
            )
        )

    # Example 4: payment-history contradiction.
    if (app.get("prior_late_payments") or 0) > 0 and parsed_note.get("mentions_no_late_payments"):
        alerts.append(
            _make_alert(
                code="INC_PAYMENT_HISTORY_CONTRADICTION",
                severity="high",
                message="Inconsistency: prior late payments but note claims none",
                source="cross_check",
            )
        )

    # Example 5: requested amount incompatible with declared monthly income.
    requested_amount = _to_float(app.get("requested_amount"))
    monthly_income = _to_float(app.get("monthly_income"))
    if requested_amount is not None and monthly_income is not None and monthly_income > 0:
        if requested_amount > (LOAN_TO_INCOME_MULTIPLIER_LIMIT * monthly_income):
            alerts.append(
                _make_alert(
                    code="INC_INCOME_LOAN_RATIO",
                    severity="medium",
                    message="Inconsistency: requested amount is unusually high relative to declared monthly income",
                    source="cross_check",
                    confidence=0.95,
                )
            )

    # Example 6: unemployed applicant with positive declared monthly income.
    employment_status = str(app.get("employment_status", "")).lower()
    if employment_status == "unemployed" and monthly_income is not None and monthly_income > 0:
        alerts.append(
            _make_alert(
                code="INC_EMPLOYMENT_INCOME_MISMATCH",
                severity="high",
                message="Inconsistency: applicant declares unemployed while reporting positive monthly income",
                source="cross_check",
                confidence=0.98,
            )
        )

    # Example 7: high debt burden signal.
    debt_to_income_ratio = _to_float(app.get("debt_to_income_ratio"))
    if debt_to_income_ratio is not None and debt_to_income_ratio > HIGH_DEBT_BURDEN_THRESHOLD:
        alerts.append(
            _make_alert(
                code="RISK_HIGH_DEBT_BURDEN",
                severity="medium",
                message="Risk signal: debt-to-income ratio indicates high debt burden",
                source="structured_data",
                confidence=0.9,
            )
        )

    # Example 8: urgency in note combined with risk proxies.
    high_risk_proxy = bool((app.get("has_prior_default") or 0) == 1 or (app.get("prior_late_payments") or 0) >= 2)
    if parsed_note.get("mentions_urgent_need") and high_risk_proxy:
        alerts.append(
            _make_alert(
                code="AMB_NOTE_URGENCY_FLAG",
                severity="low",
                message="Ambiguity: note mentions urgent need alongside elevated risk proxies",
                source="cross_check",
                confidence=0.8,
            )
        )

    # Example 9: note has hedging language that weakens confidence in text-based signals.
    if parsed_note.get("mentions_ambiguous_context"):
        alerts.append(
            _make_alert(
                code="AMB_NOTE_CONTEXT_UNCLEAR",
                severity="low",
                message="Ambiguity: note contains uncertain wording, manual interpretation recommended",
                source="note_parser",
                confidence=0.75,
            )
        )

    return alerts


def check_inconsistencies(app: Dict, parsed_note: Dict, documents: List[Dict]) -> List[str]:
    """Legacy wrapper returning message-only alerts for backward compatibility."""
    return [item["message"] for item in check_inconsistency_items(app, parsed_note, documents)]