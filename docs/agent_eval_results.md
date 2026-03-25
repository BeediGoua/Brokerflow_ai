# Agent Evaluation Results (Phase 5)

- Cases: `50` from `data/agent_eval_cases.json`
- LLM mode run config: timeout=1s, retries=0
- LLM transport mode: `offline`

| Metric | Deterministic | LLM assisted | Delta (LLM-Det) |
|---|---:|---:|---:|
| json_validity_rate | 1.0000 | 1.0000 | 0.0000 |
| summary_coherence | 1.0000 | 1.0000 | 0.0000 |
| parser_precision | 0.8000 | 0.8000 | 0.0000 |
| parser_recall | 1.0000 | 1.0000 | 0.0000 |
| parser_f1 | 0.8889 | 0.8889 | 0.0000 |
| alert_precision | 1.0000 | 1.0000 | 0.0000 |
| alert_recall | 1.0000 | 1.0000 | 0.0000 |
| alert_f1 | 1.0000 | 1.0000 | 0.0000 |
| latency_p50_ms | 0.0049 | 0.3256 | 0.3207 |
| latency_p95_ms | 0.0831 | 0.6106 | 0.5275 |
| fallback_rate | 0.0000 | 0.0000 | 0.0000 |

## Notes

- `fallback_rate` is currently a placeholder metric in the evaluator (always `0.0`).
- LLM mode still uses deterministic fallback when Ollama is unavailable or times out.
