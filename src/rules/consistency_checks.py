"""
Check for inconsistencies between structured data, free‑text notes and documents.

The functions defined here take the parsed note information, the structured
application fields and the list of documents to flag mismatches or missing
information.  Alerts produced here influence the business decision.
"""

from typing import List, Dict


def check_inconsistencies(app: Dict, parsed_note: Dict, documents: List[Dict]) -> List[str]:
    """Detect simple inconsistencies and missing information.

    Args:
        app: Application fields as a dictionary.
        parsed_note: Output of the note parser (structured information).
        documents: List of document records for the application.

    Returns:
        List of alert strings describing problems.
    """
    alerts = []
    # Example 1: employment status conflict
    employment_status = app.get("employment_status", "").lower()
    if employment_status == "unemployed" and parsed_note.get("mentions_stable_job"):
        alerts.append("Inconsistency: applicant declares unemployed but note mentions a stable job")
    # Example 2: missing critical documents
    for doc in documents:
        if doc.get("is_required") and not doc.get("is_provided"):
            alerts.append(f"Missing required document: {doc.get('document_type')}")
    # Example 3: note mentions missing documents
    if parsed_note.get("mentions_missing_documents"):
        alerts.append("Note indicates missing documents")
    # Example 4: multiple late payments vs note
    if app.get("prior_late_payments", 0) > 0 and parsed_note.get("mentions_no_late_payments"):
        alerts.append("Inconsistency: prior late payments but note claims none")
    return alerts