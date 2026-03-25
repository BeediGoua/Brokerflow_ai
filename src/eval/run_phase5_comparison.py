"""Run Phase 5 deterministic vs LLM-assisted comparison on agent eval cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.agents import note_parser, reviewer, summary_writer
from src.config.settings import settings
from src.eval.evaluate_agents import evaluate_from_file


def _set_setting(name: str, value: Any) -> None:
    """Set runtime settings even if the settings object is frozen."""
    try:
        setattr(settings, name, value)
    except Exception:
        object.__setattr__(settings, name, value)


def _delta(det: float, llm: float) -> float:
    return llm - det


def _fmt(v: float, digits: int = 4) -> str:
    return f"{v:.{digits}f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 5 agent comparison")
    parser.add_argument("--cases", default="data/agent_eval_cases.json")
    parser.add_argument("--llm-timeout", type=int, default=2)
    parser.add_argument("--llm-retries", type=int, default=0)
    parser.add_argument(
        "--llm-transport-mode",
        choices=["offline", "live"],
        default="offline",
        help="offline: force immediate fallback (no network); live: call Ollama",
    )
    parser.add_argument("--out-json", default="models/agent_eval_phase5_results.json")
    parser.add_argument("--out-md", default="docs/agent_eval_results.md")
    args = parser.parse_args()

    # Baseline deterministic mode.
    _set_setting("agent_llm_enabled", False)
    deterministic = evaluate_from_file(args.cases)

    # LLM-assisted mode with bounded timeout/retries to keep evaluation tractable.
    _set_setting("agent_llm_enabled", True)
    _set_setting("agent_request_timeout_seconds", int(args.llm_timeout))
    _set_setting("agent_max_retries", int(args.llm_retries))

    # Keep references so we can restore after the run.
    orig_np_call = note_parser.call_ollama_chat
    orig_rev_call = reviewer.call_ollama_chat
    orig_sum_call = summary_writer.call_ollama_chat

    if args.llm_transport_mode == "offline":
        # Force fallback path with LLM feature flag ON but no network dependency.
        note_parser.call_ollama_chat = lambda messages: None
        reviewer.call_ollama_chat = lambda messages: None
        summary_writer.call_ollama_chat = lambda messages: None
    else:
        # Enforce transport bounds even if settings object is immutable in runtime.
        note_parser.call_ollama_chat = lambda messages: orig_np_call(
            messages,
            timeout_seconds=int(args.llm_timeout),
            max_retries=int(args.llm_retries),
        )
        reviewer.call_ollama_chat = lambda messages: orig_rev_call(
            messages,
            timeout_seconds=int(args.llm_timeout),
            max_retries=int(args.llm_retries),
        )
        summary_writer.call_ollama_chat = lambda messages: orig_sum_call(
            messages,
            timeout_seconds=int(args.llm_timeout),
            max_retries=int(args.llm_retries),
        )

    llm_assisted = evaluate_from_file(args.cases)

    # Restore original callables for safety when reusing process.
    note_parser.call_ollama_chat = orig_np_call
    reviewer.call_ollama_chat = orig_rev_call
    summary_writer.call_ollama_chat = orig_sum_call

    result = {
        "cases_file": args.cases,
        "cases_count": deterministic.get("cases_count", 0.0),
        "llm_timeout_seconds": int(args.llm_timeout),
        "llm_max_retries": int(args.llm_retries),
        "llm_transport_mode": args.llm_transport_mode,
        "deterministic": deterministic,
        "llm_assisted": llm_assisted,
        "delta": {
            "json_validity_rate": _delta(deterministic["json_validity_rate"], llm_assisted["json_validity_rate"]),
            "summary_coherence": _delta(deterministic["summary_coherence"], llm_assisted["summary_coherence"]),
            "parser_precision": _delta(deterministic["parser_precision"], llm_assisted["parser_precision"]),
            "parser_recall": _delta(deterministic["parser_recall"], llm_assisted["parser_recall"]),
            "parser_f1": _delta(deterministic["parser_f1"], llm_assisted["parser_f1"]),
            "alert_precision": _delta(deterministic["alert_precision"], llm_assisted["alert_precision"]),
            "alert_recall": _delta(deterministic["alert_recall"], llm_assisted["alert_recall"]),
            "alert_f1": _delta(deterministic["alert_f1"], llm_assisted["alert_f1"]),
            "latency_p50_ms": _delta(deterministic["latency_p50_ms"], llm_assisted["latency_p50_ms"]),
            "latency_p95_ms": _delta(deterministic["latency_p95_ms"], llm_assisted["latency_p95_ms"]),
            "fallback_rate": _delta(deterministic["fallback_rate"], llm_assisted["fallback_rate"]),
        },
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")

    rows = [
        ("json_validity_rate", "json_validity_rate"),
        ("summary_coherence", "summary_coherence"),
        ("parser_precision", "parser_precision"),
        ("parser_recall", "parser_recall"),
        ("parser_f1", "parser_f1"),
        ("alert_precision", "alert_precision"),
        ("alert_recall", "alert_recall"),
        ("alert_f1", "alert_f1"),
        ("latency_p50_ms", "latency_p50_ms"),
        ("latency_p95_ms", "latency_p95_ms"),
        ("fallback_rate", "fallback_rate"),
    ]

    md_lines = [
        "# Agent Evaluation Results (Phase 5)",
        "",
        f"- Cases: `{int(result['cases_count'])}` from `{args.cases}`",
        f"- LLM mode run config: timeout={int(args.llm_timeout)}s, retries={int(args.llm_retries)}",
        f"- LLM transport mode: `{args.llm_transport_mode}`",
        "",
        "| Metric | Deterministic | LLM assisted | Delta (LLM-Det) |",
        "|---|---:|---:|---:|",
    ]

    for label, key in rows:
        d = float(deterministic[key])
        l = float(llm_assisted[key])
        md_lines.append(f"| {label} | {_fmt(d)} | {_fmt(l)} | {_fmt(l - d)} |")

    md_lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `fallback_rate` is currently a placeholder metric in the evaluator (always `0.0`).",
            "- LLM mode still uses deterministic fallback when Ollama is unavailable or times out.",
        ]
    )

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
