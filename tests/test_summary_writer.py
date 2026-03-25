"""Simple tests for summary writer deterministic and LLM-assisted behavior."""

from __future__ import annotations

from src.agents.summary_writer import write_summary
from src.config.settings import settings


def test_write_summary_deterministic_when_llm_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", False)

    text = write_summary(
        risk_class="Medium",
        risk_score=0.42,
        top_factors=[("debt_to_income_ratio", 0.2)],
        recommendation="REVIEW",
        alerts=["Missing required document: income_proof"],
    )

    assert "REVIEW" in text


def test_write_summary_uses_llm_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", True)

    raw_llm = '{"summary": "Risk is medium. Recommended action: REVIEW."}'
    monkeypatch.setattr("src.agents.summary_writer.call_ollama_chat", lambda messages: raw_llm)

    text = write_summary(
        risk_class="Medium",
        risk_score=0.42,
        top_factors=[("debt_to_income_ratio", 0.2)],
        recommendation="REVIEW",
        alerts=[],
    )

    assert "REVIEW" in text
    assert text.startswith("Risk is medium")


def test_write_summary_fallbacks_when_llm_missing_recommendation(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", True)

    raw_llm = '{"summary": "Risk is medium with some concerns."}'
    monkeypatch.setattr("src.agents.summary_writer.call_ollama_chat", lambda messages: raw_llm)

    text = write_summary(
        risk_class="Medium",
        risk_score=0.42,
        top_factors=[("debt_to_income_ratio", 0.2)],
        recommendation="REVIEW",
        alerts=[],
    )

    # Deterministic fallback summary always includes recommendation in bold.
    assert "REVIEW" in text
