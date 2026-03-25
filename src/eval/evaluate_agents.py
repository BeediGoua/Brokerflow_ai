"""Evaluation utilities for agent performance.

This module provides a simple, deterministic benchmark runner for:
- note parser signal extraction
- reviewer structured alerts
- summary coherence with recommendation
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from src.agents.note_parser import parse_note
from src.agents.reviewer import review_application_detailed
from src.agents.summary_writer import write_summary


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _precision_recall_f1(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall) if (precision + recall) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    idx = int(round((p / 100.0) * (len(ordered) - 1)))
    return float(ordered[idx])


def evaluate_agent_cases(cases: List[Dict[str, Any]]) -> Dict[str, float]:
    """Evaluate parser/reviewer/summary outputs on annotated cases.

    Expected case schema (minimal):
    {
      "case_id": "...",
      "application": {...},
      "expected_risk_signals": ["late_payments"],
      "expected_alerts_codes": ["INC_PAYMENT_HISTORY_CONTRADICTION"],
      "expected_recommendation": "REVIEW"
    }
    """
    parser_tp = parser_fp = parser_fn = 0
    reviewer_tp = reviewer_fp = reviewer_fn = 0

    json_valid_count = 0
    summary_coherent_count = 0
    total_cases = len(cases)

    parser_latencies: List[float] = []
    reviewer_latencies: List[float] = []
    summary_latencies: List[float] = []

    for case in cases:
        app = dict(case.get("application", {}))
        note = str(app.get("free_text_note", ""))
        expected_signals = {str(v).strip().lower() for v in case.get("expected_risk_signals", [])}
        expected_alert_codes = {str(v).strip().upper() for v in case.get("expected_alerts_codes", [])}
        expected_reco = str(case.get("expected_recommendation", "")).strip().upper()

        t0 = time.perf_counter()
        parsed = parse_note(note)
        parser_latencies.append((time.perf_counter() - t0) * 1000.0)

        predicted_signals = set()
        if parsed.get("mentions_late_payments"):
            predicted_signals.add("late_payments")
        if parsed.get("mentions_urgent_need"):
            predicted_signals.add("urgent_need")
        if parsed.get("mentions_recent_default"):
            predicted_signals.add("recent_default")
        if parsed.get("mentions_no_late_payments"):
            predicted_signals.add("no_late_payments")

        parser_tp += len(predicted_signals & expected_signals)
        parser_fp += len(predicted_signals - expected_signals)
        parser_fn += len(expected_signals - predicted_signals)

        t1 = time.perf_counter()
        alert_items = review_application_detailed(app, parsed, app.get("documents") or [])
        reviewer_latencies.append((time.perf_counter() - t1) * 1000.0)

        predicted_codes = {str(item.get("code", "")).strip().upper() for item in alert_items if item.get("code")}
        reviewer_tp += len(predicted_codes & expected_alert_codes)
        reviewer_fp += len(predicted_codes - expected_alert_codes)
        reviewer_fn += len(expected_alert_codes - predicted_codes)

        # Reviewer JSON validity proxy: every item has expected fields + valid severity.
        severities = {"low", "medium", "high"}
        is_valid = True
        for item in alert_items:
            if not all(k in item for k in ("code", "severity", "message", "source", "confidence")):
                is_valid = False
                break
            if str(item.get("severity", "")).lower() not in severities:
                is_valid = False
                break
        if is_valid:
            json_valid_count += 1

        t2 = time.perf_counter()
        summary = write_summary(
            risk_class="Medium",
            risk_score=0.35,
            top_factors=[("debt_to_income_ratio", 0.2)],
            recommendation=expected_reco or "REVIEW",
            alerts=[str(i.get("message", "")) for i in alert_items],
        )
        summary_latencies.append((time.perf_counter() - t2) * 1000.0)

        if (expected_reco and expected_reco.lower() in summary.lower()) or (not expected_reco):
            summary_coherent_count += 1

    parser_scores = _precision_recall_f1(parser_tp, parser_fp, parser_fn)
    reviewer_scores = _precision_recall_f1(reviewer_tp, reviewer_fp, reviewer_fn)

    return {
        "cases_count": float(total_cases),
        "json_validity_rate": _safe_div(json_valid_count, total_cases),
        "summary_coherence": _safe_div(summary_coherent_count, total_cases),
        "parser_precision": parser_scores["precision"],
        "parser_recall": parser_scores["recall"],
        "parser_f1": parser_scores["f1"],
        "alert_precision": reviewer_scores["precision"],
        "alert_recall": reviewer_scores["recall"],
        "alert_f1": reviewer_scores["f1"],
        "latency_p50_ms": _percentile(parser_latencies + reviewer_latencies + summary_latencies, 50),
        "latency_p95_ms": _percentile(parser_latencies + reviewer_latencies + summary_latencies, 95),
        # No explicit fallback counters are exposed yet in the runtime return values.
        "fallback_rate": 0.0,
    }


def load_cases_from_json(path: str | Path) -> List[Dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "cases" in payload:
        payload = payload["cases"]
    if not isinstance(payload, list):
        raise ValueError("Evaluation cases file must contain a JSON list or {'cases': [...]}.")
    return [dict(x) for x in payload]


def evaluate_from_file(path: str | Path) -> Dict[str, float]:
    return evaluate_agent_cases(load_cases_from_json(path))