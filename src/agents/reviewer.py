"""
Reviewer agent.

This agent combines the parsed note with the structured application and
document metadata to identify inconsistencies and missing items.  It
delegates the core checks to the ``consistency_checks`` module.
"""

from typing import Dict, List

from src.rules.consistency_checks import check_inconsistencies


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