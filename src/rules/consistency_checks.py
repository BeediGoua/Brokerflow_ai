"""Check for inconsistencies between structured data, free-text notes and documents.

This module now exposes both legacy string alerts and structured alert records
with code/severity metadata for policy decisions and auditability.
"""

from typing import Any, Dict, List


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

    return alerts


def check_inconsistencies(app: Dict, parsed_note: Dict, documents: List[Dict]) -> List[str]:
    """Legacy wrapper returning message-only alerts for backward compatibility."""
    return [item["message"] for item in check_inconsistency_items(app, parsed_note, documents)]