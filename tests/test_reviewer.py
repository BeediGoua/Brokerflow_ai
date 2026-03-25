"""Simple tests for reviewer deterministic and LLM-assisted behavior."""

from __future__ import annotations

from src.agents.reviewer import _parse_tool_calls, review_application, review_application_detailed
from src.config.settings import settings


def test_review_application_deterministic_when_llm_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", False)

    app = {"employment_status": "unemployed"}
    parsed_note = {"mentions_stable_job": True}
    documents = []

    detailed = review_application_detailed(app, parsed_note, documents)
    assert any(item["code"] == "INC_EMPLOYMENT_NOTE_CONTRADICTION" for item in detailed)

    legacy = review_application(app, parsed_note, documents)
    assert any("stable job" in msg.lower() for msg in legacy)


def test_review_application_merges_llm_alerts_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", True)

    raw_llm = (
        "["
        "{\"code\": \"RISK_TEXT_SIGNAL\", \"severity\": \"medium\", \"message\": \"Text suggests repayment stress\", \"source\": \"llm\", \"confidence\": 0.8}"
        "]"
    )
    monkeypatch.setattr("src.agents.reviewer.call_ollama_chat", lambda messages: raw_llm)

    app = {"employment_status": "employed"}
    parsed_note = {}
    documents = []

    detailed = review_application_detailed(app, parsed_note, documents)
    assert any(item["code"] == "RISK_TEXT_SIGNAL" for item in detailed)


def test_review_application_fallbacks_when_llm_output_invalid(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", True)
    monkeypatch.setattr("src.agents.reviewer.call_ollama_chat", lambda messages: "not-json")

    app = {"employment_status": "unemployed"}
    parsed_note = {"mentions_stable_job": True}
    documents = []

    detailed = review_application_detailed(app, parsed_note, documents)
    assert any(item["code"] == "INC_EMPLOYMENT_NOTE_CONTRADICTION" for item in detailed)


def test_parse_tool_calls_filters_unknown_tools() -> None:
    raw = (
        '{"tool_calls": ['
        '{"name": "check_required_documents", "arguments": {}},'
        '{"name": "unknown_tool", "arguments": {}},'
        '{"name": "check_payment_history_consistency", "arguments": {"x": 1}}'
        ']}'
    )

    calls = _parse_tool_calls(raw)
    assert len(calls) == 2
    assert calls[0]["name"] == "check_required_documents"
    assert calls[1]["name"] == "check_payment_history_consistency"


def test_review_application_tool_enabled_adds_tool_alerts(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", True)
    monkeypatch.setattr(settings, "agent_tools_enabled", True)

    planner_raw = '{"tool_calls": [{"name": "check_required_documents", "arguments": {}}]}'
    reviewer_raw = "[]"
    responses = iter([planner_raw, reviewer_raw])
    monkeypatch.setattr("src.agents.reviewer.call_ollama_chat", lambda messages: next(responses))

    app = {"employment_status": "employed"}
    parsed_note = {}
    documents = [
        {
            "document_type": "income_proof",
            "is_required": True,
            "is_provided": False,
        }
    ]

    detailed = review_application_detailed(app, parsed_note, documents)
    assert any(item["code"] == "DOC_REQUIRED_MISSING" for item in detailed)
