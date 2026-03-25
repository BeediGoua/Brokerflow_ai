"""Schema validation helpers for agent outputs.

This module validates JSON outputs produced by LLM agents.
It does not perform network calls and does not contain prompting logic.
"""

from __future__ import annotations

import json
import logging
from typing import cast
from typing import Any, TypeVar

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

TModel = TypeVar("TModel", bound=BaseModel)

ALERT_SEVERITIES = ("low", "medium", "high")


class NoteParserOutput(BaseModel):
    risk_signals: list[str] = Field(default_factory=list)
    document_signals: list[str] = Field(default_factory=list)
    stability_signals: list[str] = Field(default_factory=list)
    context_tags: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


class ReviewerAlertItem(BaseModel):
    code: str
    severity: str
    message: str
    source: str
    confidence: float = 1.0


class SummaryWriterOutput(BaseModel):
    summary: str


def _parse_raw_json(raw_text: str) -> Any | None:
    """Parse raw JSON text from an LLM response."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        return None

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Agent output is not valid JSON")
        return None


def _model_dump(instance: BaseModel) -> dict[str, Any]:
    """Compatibility dump for Pydantic v1/v2."""
    dump_method = getattr(instance, "model_dump", None)
    if callable(dump_method):
        return cast(dict[str, Any], dump_method())
    return instance.dict()


def _validate_with_model(raw_text: str, model_cls: type[TModel]) -> tuple[dict[str, Any] | None, bool]:
    """Validate a raw JSON string against a Pydantic model."""
    parsed = _parse_raw_json(raw_text)
    if parsed is None:
        return None, False

    try:
        instance = model_cls(**parsed)
    except ValidationError:
        logger.warning("Agent output schema validation failed for %s", model_cls.__name__)
        return None, False

    return _model_dump(instance), True


def validate_note_parser_output(raw_text: str) -> tuple[dict[str, Any] | None, bool]:
    """Validate note_parser JSON output."""
    return _validate_with_model(raw_text, NoteParserOutput)


def validate_reviewer_output(raw_text: str) -> tuple[list[dict[str, Any]] | None, bool]:
    """Validate reviewer JSON output.

    Expected payload shape:
    [
      {"code": "...", "severity": "low|medium|high", "message": "...", "source": "...", "confidence": 0.95}
    ]
    """
    parsed = _parse_raw_json(raw_text)
    if not isinstance(parsed, list):
        logger.warning("Reviewer output must be a JSON list")
        return None, False

    validated_items: list[dict[str, Any]] = []
    try:
        for item in parsed:
            alert = ReviewerAlertItem(**item)
            if alert.severity.lower() not in ALERT_SEVERITIES:
                logger.warning("Reviewer severity must be one of: %s", ALERT_SEVERITIES)
                return None, False
            dumped = _model_dump(alert)
            dumped["severity"] = str(dumped["severity"]).lower()
            validated_items.append(dumped)
    except ValidationError:
        logger.warning("Reviewer output schema validation failed")
        return None, False

    return validated_items, True


def validate_summary_writer_output(raw_text: str) -> tuple[dict[str, Any] | None, bool]:
    """Validate summary_writer JSON output."""
    return _validate_with_model(raw_text, SummaryWriterOutput)
