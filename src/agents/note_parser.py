"""
Simple note parser agent.

This agent scans the free‑text note for a predefined list of phrases
indicative of risk or stability.  It returns a structured dictionary
containing boolean flags for each recognised phrase.  The parser is
intentionally lightweight; in a production system you could replace it
with a transformer model or a rules engine.
"""

from typing import Dict


PHRASES = {
    "urgent need": "mentions_urgent_need",
    "missing documents": "mentions_missing_documents",
    "steady income": "mentions_stable_income",
    "multiple late payments": "mentions_late_payments",
    "recent default": "mentions_recent_default",
    "stable job": "mentions_stable_job",
    "previous loans paid": "mentions_no_late_payments",
    "needs fast approval": "mentions_urgent_need",
}


def parse_note(note: str) -> Dict[str, bool]:
    """Parse a free‑text note and extract keyword indicators.

    Args:
        note: The note string.

    Returns:
        Dictionary mapping indicator names to booleans.
    """
    note_lower = note.lower() if note else ""
    result = {flag: False for flag in set(PHRASES.values())}
    for phrase, flag in PHRASES.items():
        if phrase in note_lower:
            result[flag] = True
    return result