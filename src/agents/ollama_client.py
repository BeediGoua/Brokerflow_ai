"""Ollama HTTP client for agent calls.

This module centralizes low-level network calls to Ollama.
It intentionally does not validate or parse business JSON payloads produced by the LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any

import requests

from src.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OllamaClientConfig:
    """Runtime config for Ollama client calls."""

    base_url: str
    model_name: str
    temperature: float
    timeout_seconds: int
    max_retries: int

    @classmethod
    def from_settings(cls) -> "OllamaClientConfig":
        return cls(
            base_url=settings.ollama_base_url,
            model_name=settings.ollama_model,
            temperature=float(settings.agent_temperature),
            timeout_seconds=int(settings.agent_request_timeout_seconds),
            max_retries=int(settings.agent_max_retries),
        )


class OllamaClient:
    """Lightweight HTTP client for Ollama chat endpoint.

    This client handles transport concerns only: payload, HTTP call, retries, and raw text extraction.
    It does not parse or validate business JSON content.
    """

    def __init__(
        self,
        config: OllamaClientConfig | None = None,
        session: requests.Session | None = None,
        retry_sleep_seconds: float = 0.2,
    ) -> None:
        self.config = config or OllamaClientConfig.from_settings()
        self.session = session or requests.Session()
        self.retry_sleep_seconds = retry_sleep_seconds

    @property
    def endpoint(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/api/chat"

    def build_chat_payload(
        self,
        messages: list[dict[str, str]],
        *,
        model_name: str,
        temperature: float,
    ) -> dict[str, Any]:
        return {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {"temperature": float(temperature)},
        }

    def _post_once(self, payload: dict[str, Any], timeout_seconds: int) -> tuple[dict[str, Any] | None, bool]:
        """Send one request and return `(response_json, retryable_error)`.

        `retryable_error=True` only for timeout/connection issues.
        """
        retryable_error = False

        try:
            response = self.session.post(self.endpoint, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            return response.json(), retryable_error
        except requests.Timeout:
            retryable_error = True
            logger.warning("Ollama request timed out after %ss", timeout_seconds)
        except requests.ConnectionError:
            retryable_error = True
            logger.warning("Ollama connection error to %s", self.endpoint)
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            logger.warning("Ollama HTTP error status=%s", status_code)
        except ValueError:
            logger.warning("Ollama response is not valid JSON")

        return None, retryable_error


    @staticmethod
    def extract_response_text(response_payload: dict[str, Any]) -> str | None:
        """Extract raw assistant text from Ollama transport JSON."""
        message = response_payload.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content

        # Fallback for endpoints that may return the legacy field name.
        legacy_content = response_payload.get("response")
        if isinstance(legacy_content, str):
            return legacy_content

        return None

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model_name: str | None = None,
        temperature: float | None = None,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
    ) -> str | None:
        """Call Ollama chat API and return raw text output, or None on failure."""
        resolved_model = model_name or self.config.model_name
        resolved_temperature = self.config.temperature if temperature is None else temperature
        resolved_timeout = self.config.timeout_seconds if timeout_seconds is None else timeout_seconds
        resolved_retries = self.config.max_retries if max_retries is None else max_retries

        payload = self.build_chat_payload(
            messages=messages,
            model_name=resolved_model,
            temperature=resolved_temperature,
        )

        attempts = max(1, int(resolved_retries) + 1)
        for attempt in range(1, attempts + 1):
            response_payload, retryable_error = self._post_once(payload, int(resolved_timeout))

            if response_payload is not None:
                raw_text = self.extract_response_text(response_payload)
                if raw_text is not None:
                    return raw_text
                logger.warning("Ollama response payload missing assistant content")
                return None

            # Retry only for timeout/connection errors.
            if retryable_error and attempt < attempts:
                time.sleep(self.retry_sleep_seconds)
                continue

            return None

        return None


def call_ollama_chat(
    messages: list[dict[str, str]],
    *,
    model_name: str | None = None,
    temperature: float | None = None,
    timeout_seconds: int | None = None,
    max_retries: int | None = None,
    base_url: str | None = None,
) -> str | None:
    """Compatibility wrapper around `OllamaClient.chat`."""
    config = OllamaClientConfig.from_settings()
    if base_url is not None:
        config = OllamaClientConfig(
            base_url=base_url,
            model_name=config.model_name,
            temperature=config.temperature,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    client = OllamaClient(config=config)
    return client.chat(
        messages=messages,
        model_name=model_name,
        temperature=temperature,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )
