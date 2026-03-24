"""Reviewer agent.

This agent combines parsed note signals with structured application/document
data and exposes both legacy and structured alert outputs.
"""

from typing import Any, Dict, List

from src.rules.consistency_checks import check_inconsistencies, check_inconsistency_items


def review_application(app: Dict, parsed_note: Dict, documents: List[Dict]) -> List[str]:
    """Compile alerts for an application.

    Args:
        app: Application fields as a dictionary.
        parsed_note: Parsed note flags from ``note_parser.parse_note``.
        documents: List of document dictionaries belonging to the application.

    Returns:
        List of alert strings.
    """
    alerts = check_inconsistencies(app, parsed_note, documents)
    return alerts


def review_application_detailed(app: Dict, parsed_note: Dict, documents: List[Dict]) -> List[Dict[str, Any]]:
    """Return structured alerts with code/severity for policy and audit usage."""
    return check_inconsistency_items(app, parsed_note, documents)