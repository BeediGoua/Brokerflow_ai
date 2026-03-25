"""Tool registry for agent-side bounded tool execution.

This module defines local, deterministic tools that agents can request.
All tools are read-only and pure over in-memory payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ToolFn = Callable[[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]], list[dict[str, Any]]]


@dataclass(frozen=True)
class AgentTool:
    name: str
    description: str
    runner: ToolFn


def _make_alert(code: str, severity: str, message: str, source: str, confidence: float) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "source": source,
        "confidence": float(confidence),
    }


def _tool_check_required_documents(
    app: dict[str, Any],
    parsed_note: dict[str, Any],
    documents: list[dict[str, Any]],
    arguments: dict[str, Any],
) -> list[dict[str, Any]]:
    del app, parsed_note, arguments
    alerts: list[dict[str, Any]] = []
    for doc in documents:
        if doc.get("is_required") and not doc.get("is_provided"):
            doc_type = str(doc.get("document_type") or "unknown_document")
            alerts.append(
                _make_alert(
                    code="DOC_REQUIRED_MISSING",
                    severity="medium",
                    message=f"Missing required document: {doc_type}",
                    source="tool:check_required_documents",
                    confidence=1.0,
                )
            )
    return alerts


def _tool_check_employment_note_consistency(
    app: dict[str, Any],
    parsed_note: dict[str, Any],
    documents: list[dict[str, Any]],
    arguments: dict[str, Any],
) -> list[dict[str, Any]]:
    del documents, arguments
    employment_status = str(app.get("employment_status", "")).lower()
    if employment_status == "unemployed" and parsed_note.get("mentions_stable_job"):
        return [
            _make_alert(
                code="INC_EMPLOYMENT_NOTE_CONTRADICTION",
                severity="high",
                message="Inconsistency: applicant declares unemployed but note mentions a stable job",
                source="tool:check_employment_note_consistency",
                confidence=0.98,
            )
        ]
    return []


def _tool_check_payment_history_consistency(
    app: dict[str, Any],
    parsed_note: dict[str, Any],
    documents: list[dict[str, Any]],
    arguments: dict[str, Any],
) -> list[dict[str, Any]]:
    del documents, arguments
    prior_late = int(app.get("prior_late_payments") or 0)
    if prior_late > 0 and parsed_note.get("mentions_no_late_payments"):
        return [
            _make_alert(
                code="INC_PAYMENT_HISTORY_CONTRADICTION",
                severity="high",
                message="Inconsistency: prior late payments but note claims none",
                source="tool:check_payment_history_consistency",
                confidence=0.96,
            )
        ]
    return []


REVIEWER_TOOLS: dict[str, AgentTool] = {
    "check_required_documents": AgentTool(
        name="check_required_documents",
        description="Detect missing required documents from documents payload.",
        runner=_tool_check_required_documents,
    ),
    "check_employment_note_consistency": AgentTool(
        name="check_employment_note_consistency",
        description="Check mismatch between employment status and stable-job claim in note.",
        runner=_tool_check_employment_note_consistency,
    ),
    "check_payment_history_consistency": AgentTool(
        name="check_payment_history_consistency",
        description="Check contradiction between prior late payments and note claiming none.",
        runner=_tool_check_payment_history_consistency,
    ),
}


def execute_reviewer_tool(
    tool_name: str,
    app: dict[str, Any],
    parsed_note: dict[str, Any],
    documents: list[dict[str, Any]],
    arguments: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute one whitelisted reviewer tool and return structured alerts."""
    tool = REVIEWER_TOOLS.get(tool_name)
    if tool is None:
        return []
    return tool.runner(app, parsed_note, documents, arguments or {})
