"""Reviewer agent.

This agent combines parsed note signals with structured application/document
data and exposes both legacy and structured alert outputs.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List

from src.agents.agent_logger import log_agent_execution
from src.agents.ollama_client import call_ollama_chat
from src.agents.prompts import REVIEWER_PROMPT_V1, REVIEWER_TOOL_PLANNER_PROMPT_V1
from src.agents.schema_validator import validate_reviewer_output
from src.agents.tools_registry import REVIEWER_TOOLS, execute_reviewer_tool
from src.config.settings import settings
from src.rules.consistency_checks import check_inconsistency_items

logger = logging.getLogger(__name__)


def _build_reviewer_messages(app: Dict, parsed_note: Dict, documents: List[Dict]) -> list[dict[str, str]]:
    payload = json.dumps(
        {
            "application": app,
            "parsed_note": parsed_note,
            "documents": documents,
        },
        ensure_ascii=True,
        default=str,
    )
    return [
        {"role": "system", "content": REVIEWER_PROMPT_V1},
        {"role": "user", "content": payload},
    ]


def _build_reviewer_messages_with_tool_context(
    app: Dict,
    parsed_note: Dict,
    documents: List[Dict],
    tool_alerts: List[Dict[str, Any]],
) -> list[dict[str, str]]:
    payload = json.dumps(
        {
            "application": app,
            "parsed_note": parsed_note,
            "documents": documents,
            "tool_results": tool_alerts,
        },
        ensure_ascii=True,
        default=str,
    )
    return [
        {"role": "system", "content": REVIEWER_PROMPT_V1},
        {"role": "user", "content": payload},
    ]


def _build_tool_planner_messages(app: Dict, parsed_note: Dict, documents: List[Dict]) -> list[dict[str, str]]:
    payload = json.dumps(
        {
            "application": app,
            "parsed_note": parsed_note,
            "documents": documents,
            "allowed_tools": [
                {"name": tool.name, "description": tool.description} for tool in REVIEWER_TOOLS.values()
            ],
        },
        ensure_ascii=True,
        default=str,
    )
    return [
        {"role": "system", "content": REVIEWER_TOOL_PLANNER_PROMPT_V1},
        {"role": "user", "content": payload},
    ]


def _parse_tool_calls(raw_output: str) -> list[dict[str, Any]]:
    if not isinstance(raw_output, str) or not raw_output.strip():
        return []
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return []

    calls = payload.get("tool_calls")
    if not isinstance(calls, list):
        return []

    sanitized_calls: list[dict[str, Any]] = []
    for item in calls[:3]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        arguments = item.get("arguments", {})
        if name not in REVIEWER_TOOLS:
            continue
        if not isinstance(arguments, dict):
            arguments = {}
        sanitized_calls.append({"name": name, "arguments": arguments})

    return sanitized_calls


def _plan_reviewer_tool_calls(app: Dict, parsed_note: Dict, documents: List[Dict]) -> list[dict[str, Any]]:
    messages = _build_tool_planner_messages(app, parsed_note, documents)
    raw_output = call_ollama_chat(messages)
    if raw_output is None:
        return []
    return _parse_tool_calls(raw_output)


def _execute_reviewer_tool_calls(
    app: Dict,
    parsed_note: Dict,
    documents: List[Dict],
    tool_calls: List[dict[str, Any]],
) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    seen_codes: set[str] = set()
    for call in tool_calls:
        tool_name = str(call.get("name", ""))
        args = call.get("arguments", {})
        for item in execute_reviewer_tool(tool_name, app, parsed_note, documents, args):
            code = str(item.get("code", "")).strip()
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)
            alerts.append(item)
    return alerts


def _review_llm(
    app: Dict,
    parsed_note: Dict,
    documents: List[Dict],
    tool_alerts: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]] | None:
    messages = _build_reviewer_messages_with_tool_context(app, parsed_note, documents, tool_alerts or [])

    for _ in range(2):
        started_at = time.perf_counter()
        raw_output = call_ollama_chat(messages)
        latency_ms = (time.perf_counter() - started_at) * 1000.0
        if raw_output is None:
            log_agent_execution(
                agent_name="reviewer",
                model_name=settings.ollama_model,
                prompt_version="reviewer_prompt_v1",
                latency_ms=latency_ms,
                schema_valid=False,
                fallback_used=True,
                fallback_reason="transport_or_http_error",
            )
            return None

        parsed_alerts, is_valid = validate_reviewer_output(raw_output)
        if is_valid and parsed_alerts is not None:
            log_agent_execution(
                agent_name="reviewer",
                model_name=settings.ollama_model,
                prompt_version="reviewer_prompt_v1",
                latency_ms=latency_ms,
                schema_valid=True,
                fallback_used=False,
                fallback_reason=None,
                raw_output=raw_output,
            )
            return parsed_alerts

        logger.warning("reviewer LLM output invalid JSON schema, retrying once")

    log_agent_execution(
        agent_name="reviewer",
        model_name=settings.ollama_model,
        prompt_version="reviewer_prompt_v1",
        latency_ms=0.0,
        schema_valid=False,
        fallback_used=True,
        fallback_reason="invalid_schema_after_retry",
    )

    return None


def _merge_alert_items(
    deterministic_alerts: List[Dict[str, Any]],
    llm_alerts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = list(deterministic_alerts)
    existing_codes = {str(item.get("code", "")) for item in deterministic_alerts}

    for item in llm_alerts:
        code = str(item.get("code", ""))
        if not code or code in existing_codes:
            continue
        merged.append(item)
        existing_codes.add(code)

    return merged


def review_application(app: Dict, parsed_note: Dict, documents: List[Dict]) -> List[str]:
    """Compile alerts for an application.

    Args:
        app: Application fields as a dictionary.
        parsed_note: Parsed note flags from ``note_parser.parse_note``.
        documents: List of document dictionaries belonging to the application.

    Returns:
        List of alert strings.
    """
    return [item["message"] for item in review_application_detailed(app, parsed_note, documents)]


def review_application_detailed(app: Dict, parsed_note: Dict, documents: List[Dict]) -> List[Dict[str, Any]]:
    """Return structured alerts with code/severity for policy and audit usage."""
    deterministic_alerts = check_inconsistency_items(app, parsed_note, documents)

    if not settings.agent_llm_enabled:
        return deterministic_alerts

    tool_alerts: List[Dict[str, Any]] = []
    if settings.agent_tools_enabled:
        planned_calls = _plan_reviewer_tool_calls(app, parsed_note, documents)
        tool_alerts = _execute_reviewer_tool_calls(app, parsed_note, documents, planned_calls)

    base_alerts = _merge_alert_items(deterministic_alerts, tool_alerts)

    llm_alerts = _review_llm(app, parsed_note, documents, tool_alerts=tool_alerts)
    if llm_alerts is None:
        logger.warning("reviewer fallback to deterministic mode")
        return base_alerts

    return _merge_alert_items(base_alerts, llm_alerts)