"""Agent execution logging helpers.

Logs execution metadata as JSON for auditability.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

logger = logging.getLogger(__name__)


def log_agent_execution(
    *,
    agent_name: str,
    model_name: str,
    prompt_version: str,
    latency_ms: float,
    schema_valid: bool,
    fallback_used: bool,
    fallback_reason: str | None,
    raw_output: str | None = None,
    request_id: str | None = None,
) -> None:
    """Emit a single JSON log line with agent execution metadata."""
    payload: dict[str, Any] = {
        "request_id": request_id or str(uuid.uuid4()),
        "agent_name": agent_name,
        "model_name": model_name,
        "prompt_version": prompt_version,
        "latency_ms": round(float(latency_ms), 2),
        "schema_valid": bool(schema_valid),
        "fallback_used": bool(fallback_used),
        "fallback_reason": fallback_reason,
        "logged_at": int(time.time()),
    }

    if raw_output is not None:
        payload["raw_output"] = raw_output[:1000]

    logger.info(json.dumps(payload, ensure_ascii=True))
