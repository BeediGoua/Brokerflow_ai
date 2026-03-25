"""Simple tests for note parser deterministic and LLM-enabled paths."""

from __future__ import annotations

from src.agents.note_parser import parse_note
from src.config.settings import settings


def test_parse_note_deterministic_default_mode(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", False)

    result = parse_note("Applicant has stable job and steady income.")

    assert result["mentions_stable_job"] is True
    assert result["mentions_stable_income"] is True
    assert result["mentions_missing_documents"] is False


def test_parse_note_uses_llm_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", True)

    raw_llm = (
        '{"risk_signals": ["urgent_need"], '
        '"document_signals": ["missing_documents"], '
        '"stability_signals": ["stable_job"], '
        '"context_tags": [], '
        '"ambiguities": []}'
    )

    monkeypatch.setattr("src.agents.note_parser.call_ollama_chat", lambda messages: raw_llm)

    result = parse_note("free text note")

    assert result["mentions_urgent_need"] is True
    assert result["mentions_missing_documents"] is True
    assert result["mentions_stable_job"] is True


def test_parse_note_fallbacks_to_deterministic_when_llm_invalid(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", True)

    monkeypatch.setattr("src.agents.note_parser.call_ollama_chat", lambda messages: "not-json")

    result = parse_note("multiple late payments")

    assert result["mentions_late_payments"] is True


def test_parse_note_detects_synonyms_in_french_and_english(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", False)

    result = parse_note("Le client a des impayes et plusieurs retards de paiement.")

    assert result["mentions_late_payments"] is True


def test_parse_note_detects_ambiguity_markers(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", False)

    result = parse_note("Peut-etre un incident, a verifier selon le broker.")

    assert result["mentions_ambiguous_context"] is True


def test_parse_note_avoids_false_positive_on_unrelated_text(monkeypatch) -> None:
    monkeypatch.setattr(settings, "agent_llm_enabled", False)

    result = parse_note("Client wants to finance studies and move to a new city.")

    assert result["mentions_late_payments"] is False
    assert result["mentions_urgent_need"] is False
