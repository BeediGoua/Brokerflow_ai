"""
Summary writer agent.

This agent composes the final summary for the underwriter by calling the
narrative utility.  It abstracts away the narrative template from the
rest of the pipeline.
"""

from __future__ import annotations

import json
import logging
import time
from typing import List, Tuple

from src.agents.agent_logger import log_agent_execution
from src.agents.ollama_client import call_ollama_chat
from src.agents.prompts import SUMMARY_PROMPT_V1
from src.agents.schema_validator import validate_summary_writer_output
from src.config.settings import settings
from src.explain.narrative import generate_summary

logger = logging.getLogger(__name__)


def _build_summary_messages(
    risk_class: str,
    risk_score: float,
    top_factors: List[Tuple[str, float]],
    recommendation: str,
    alerts: List[str],
) -> list[dict[str, str]]:
    payload = json.dumps(
        {
            "risk_class": risk_class,
            "risk_score": risk_score,
            "top_factors": top_factors,
            "recommendation": recommendation,
            "alerts": alerts,
        },
        ensure_ascii=True,
        default=str,
    )
    return [
        {"role": "system", "content": SUMMARY_PROMPT_V1},
        {"role": "user", "content": payload},
    ]


def _summary_mentions_recommendation(summary: str, recommendation: str) -> bool:
    return recommendation.strip().lower() in summary.strip().lower()


def _write_summary_llm(
    risk_class: str,
    risk_score: float,
    top_factors: List[Tuple[str, float]],
    recommendation: str,
    alerts: List[str],
) -> str | None:
    messages = _build_summary_messages(risk_class, risk_score, top_factors, recommendation, alerts)

    for _ in range(2):
        started_at = time.perf_counter()
        raw_output = call_ollama_chat(messages)
        latency_ms = (time.perf_counter() - started_at) * 1000.0
        if raw_output is None:
            log_agent_execution(
                agent_name="summary_writer",
                model_name=settings.ollama_model,
                prompt_version="summary_prompt_v1",
                latency_ms=latency_ms,
                schema_valid=False,
                fallback_used=True,
                fallback_reason="transport_or_http_error",
            )
            return None

        parsed_output, is_valid = validate_summary_writer_output(raw_output)
        if not is_valid or parsed_output is None:
            logger.warning("summary_writer LLM output invalid JSON schema, retrying once")
            continue

        summary_text = str(parsed_output.get("summary", "")).strip()
        if not summary_text:
            logger.warning("summary_writer LLM output missing summary text, retrying once")
            continue

        if not _summary_mentions_recommendation(summary_text, recommendation):
            logger.warning("summary_writer LLM output not aligned with recommendation, retrying once")
            continue

        log_agent_execution(
            agent_name="summary_writer",
            model_name=settings.ollama_model,
            prompt_version="summary_prompt_v1",
            latency_ms=latency_ms,
            schema_valid=True,
            fallback_used=False,
            fallback_reason=None,
            raw_output=raw_output,
        )

        return summary_text

    log_agent_execution(
        agent_name="summary_writer",
        model_name=settings.ollama_model,
        prompt_version="summary_prompt_v1",
        latency_ms=0.0,
        schema_valid=False,
        fallback_used=True,
        fallback_reason="invalid_schema_or_policy_after_retry",
    )

    return None


def write_summary(risk_class: str, risk_score: float, top_factors: List[Tuple[str, float]], recommendation: str, alerts: List[str]) -> str:
    """Generate a summary sentence for the underwriter."""
    if settings.agent_llm_enabled:
        llm_summary = _write_summary_llm(risk_class, risk_score, top_factors, recommendation, alerts)
        if llm_summary is not None:
            return llm_summary
        logger.warning("summary_writer fallback to deterministic mode")

    return generate_summary(risk_class, risk_score, top_factors, recommendation, alerts)