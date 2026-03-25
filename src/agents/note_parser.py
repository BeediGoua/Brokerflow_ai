"""Note parser agent with deterministic and optional LLM modes.

The public contract remains a legacy dict of boolean flags because downstream
review rules depend on it. When LLM mode is enabled, outputs are validated and
then mapped back to the same legacy flags.
"""

from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from typing import Any

from src.agents.agent_logger import log_agent_execution
from src.agents.ollama_client import call_ollama_chat
from src.agents.prompts import NOTE_PARSER_PROMPT_V1
from src.agents.schema_validator import validate_note_parser_output
from src.config.settings import settings

logger = logging.getLogger(__name__)


FLAG_PATTERNS = {
    "mentions_urgent_need": [
        r"\burgent(?: need)?\b",
        r"\bneeds? fast approval\b",
        r"\bfast approval\b",
        r"\bbesoin (?:urgent|rapide)\b",
        r"\bsituation tendue\b",
        r"\bcash[\s\-]?flow serre\b",
    ],
    "mentions_missing_documents": [
        r"\bmissing documents?\b",
        r"\bdocuments? missing\b",
        r"\bdocuments? incomplets?\b",
        r"\bdossier incomplet\b",
        r"\bpieces? manquantes?\b",
    ],
    "mentions_stable_income": [
        r"\bsteady income\b",
        r"\bstable income\b",
        r"\brevenu(?:s)? stables?\b",
        r"\bincome is stable\b",
    ],
    "mentions_late_payments": [
        r"\bmultiple late payments?\b",
        r"\blate payments?\b",
        r"\bpayment delays?\b",
        r"\bretards? de paiement\b",
        r"\bimpayes?\b",
        r"\becheances? manquees?\b",
    ],
    "mentions_recent_default": [
        r"\brecent default\b",
        r"\bdefault(?:ed)? last year\b",
        r"\bincident de paiement recent\b",
    ],
    "mentions_stable_job": [
        r"\bstable job\b",
        r"\bjob is stable\b",
        r"\bemploi stable\b",
    ],
    "mentions_no_late_payments": [
        r"\bprevious loans? paid\b",
        r"\bno late payments?\b",
        r"\baucun retard\b",
        r"\bjamais de retard\b",
    ],
}

AMBIGUITY_PATTERNS = [
    r"\bmaybe\b",
    r"\bperhaps\b",
    r"\bpossible\b",
    r"\bnot impossible\b",
    r"\ba verifier\b",
    r"\bincertain\b",
    r"\bpeut[- ]etre\b",
]


STRUCTURED_TO_LEGACY_FLAGS = {
    "risk_signals": {
        "urgent_need": "mentions_urgent_need",
        "late_payments": "mentions_late_payments",
        "recent_default": "mentions_recent_default",
        "no_late_payments": "mentions_no_late_payments",
    },
    "document_signals": {
        "missing_documents": "mentions_missing_documents",
    },
    "stability_signals": {
        "stable_income": "mentions_stable_income",
        "stable_job": "mentions_stable_job",
    },
}


def _empty_legacy_result() -> dict[str, bool]:
    flags = set(FLAG_PATTERNS.keys())
    flags.add("mentions_ambiguous_context")
    return {flag: False for flag in flags}


def _normalize_note(note: str) -> str:
    normalized = unicodedata.normalize("NFKD", note or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return normalized.lower()


def _parse_note_deterministic(note: str) -> dict[str, bool]:
    """Parse note using regex patterns for synonyms and common phrasing variants."""
    note_lower = _normalize_note(note)
    result = _empty_legacy_result()

    for flag, patterns in FLAG_PATTERNS.items():
        if any(re.search(pattern, note_lower) for pattern in patterns):
            result[flag] = True

    if any(re.search(pattern, note_lower) for pattern in AMBIGUITY_PATTERNS):
        result["mentions_ambiguous_context"] = True

    return result


def _build_messages(note: str) -> list[dict[str, str]]:
    user_payload = json.dumps({"note": note or ""}, ensure_ascii=True)
    return [
        {"role": "system", "content": NOTE_PARSER_PROMPT_V1},
        {"role": "user", "content": user_payload},
    ]


def _structured_to_legacy(parsed_structured: dict[str, Any]) -> dict[str, bool]:
    """Map structured LLM categories to legacy mention flags."""
    result = _empty_legacy_result()

    for category, mapping in STRUCTURED_TO_LEGACY_FLAGS.items():
        values = parsed_structured.get(category, [])
        if not isinstance(values, list):
            continue
        normalized_values = {str(v).strip().lower() for v in values}
        for label, legacy_flag in mapping.items():
            if label in normalized_values:
                result[legacy_flag] = True

    return result


def _parse_note_llm(note: str) -> dict[str, bool] | None:
    """Call LLM parser and return legacy mapped flags when validation succeeds."""
    messages = _build_messages(note)

    # Try once, then retry once if schema is invalid.
    for _ in range(2):
        started_at = time.perf_counter()
        raw_output = call_ollama_chat(messages)
        latency_ms = (time.perf_counter() - started_at) * 1000.0
        if raw_output is None:
            log_agent_execution(
                agent_name="note_parser",
                model_name=settings.ollama_model,
                prompt_version="note_parser_prompt_v1",
                latency_ms=latency_ms,
                schema_valid=False,
                fallback_used=True,
                fallback_reason="transport_or_http_error",
            )
            return None

        parsed_structured, is_valid = validate_note_parser_output(raw_output)
        if is_valid and parsed_structured is not None:
            log_agent_execution(
                agent_name="note_parser",
                model_name=settings.ollama_model,
                prompt_version="note_parser_prompt_v1",
                latency_ms=latency_ms,
                schema_valid=True,
                fallback_used=False,
                fallback_reason=None,
                raw_output=raw_output,
            )
            return _structured_to_legacy(parsed_structured)

        logger.warning("note_parser LLM output invalid JSON schema, retrying once")

    log_agent_execution(
        agent_name="note_parser",
        model_name=settings.ollama_model,
        prompt_version="note_parser_prompt_v1",
        latency_ms=0.0,
        schema_valid=False,
        fallback_used=True,
        fallback_reason="invalid_schema_after_retry",
    )

    return None


def parse_note(note: str) -> dict[str, bool]:
    """Parse a free‑text note and extract keyword indicators.

    Args:
        note: The note string.

    Returns:
        Dictionary mapping indicator names to booleans.
    """
    if settings.agent_llm_enabled:
        llm_result = _parse_note_llm(note)
        if llm_result is not None:
            return llm_result
        logger.warning("note_parser fallback to deterministic mode")

    return _parse_note_deterministic(note)