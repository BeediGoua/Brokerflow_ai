"""Simple unit tests for LLM output schema validation."""

from __future__ import annotations

import json

from src.agents.schema_validator import (
    validate_note_parser_output,
    validate_reviewer_output,
    validate_summary_writer_output,
)


def test_validate_note_parser_output_accepts_valid_json() -> None:
    raw = json.dumps(
        {
            "risk_signals": ["late_payments"],
            "document_signals": ["missing_documents"],
            "stability_signals": ["stable_job"],
            "context_tags": ["seasonal_income"],
            "ambiguities": [],
        }
    )

    parsed, is_valid = validate_note_parser_output(raw)

    assert is_valid is True
    assert parsed is not None
    assert parsed["risk_signals"] == ["late_payments"]


def test_validate_reviewer_output_normalizes_severity() -> None:
    raw = json.dumps(
        [
            {
                "code": "DOC_REQUIRED_MISSING",
                "severity": "HIGH",
                "message": "Missing required document: income_proof",
                "source": "documents",
                "confidence": 0.95,
            }
        ]
    )

    parsed, is_valid = validate_reviewer_output(raw)

    assert is_valid is True
    assert parsed is not None
    assert parsed[0]["severity"] == "high"


def test_validate_reviewer_output_rejects_invalid_severity() -> None:
    raw = json.dumps(
        [
            {
                "code": "X",
                "severity": "critical",
                "message": "Bad",
                "source": "test",
                "confidence": 0.9,
            }
        ]
    )

    parsed, is_valid = validate_reviewer_output(raw)

    assert is_valid is False
    assert parsed is None


def test_validate_summary_writer_output_requires_summary_key() -> None:
    parsed_ok, valid_ok = validate_summary_writer_output(json.dumps({"summary": "All good."}))
    parsed_bad, valid_bad = validate_summary_writer_output(json.dumps({"text": "missing key"}))

    assert valid_ok is True
    assert parsed_ok is not None
    assert parsed_ok["summary"] == "All good."

    assert valid_bad is False
    assert parsed_bad is None
