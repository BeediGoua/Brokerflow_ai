"""Simple unit tests for Ollama client transport behavior."""

from __future__ import annotations

from types import SimpleNamespace

import requests

from src.agents.ollama_client import OllamaClient, OllamaClientConfig


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(response=SimpleNamespace(status_code=self.status_code))

    def json(self) -> dict:
        return self._payload


class FakeSessionSuccess:
    def __init__(self):
        self.calls = 0

    def post(self, endpoint, json=None, timeout=None):
        self.calls += 1
        return FakeResponse({"message": {"content": "hello"}})


class FakeSessionTimeoutThenSuccess:
    def __init__(self):
        self.calls = 0

    def post(self, endpoint, json=None, timeout=None):
        self.calls += 1
        if self.calls == 1:
            raise requests.Timeout("timeout")
        return FakeResponse({"message": {"content": "ok after retry"}})


class FakeSessionHttpError:
    def __init__(self):
        self.calls = 0

    def post(self, endpoint, json=None, timeout=None):
        self.calls += 1
        return FakeResponse({}, status_code=500)


def _config(max_retries: int = 1) -> OllamaClientConfig:
    return OllamaClientConfig(
        base_url="http://localhost:11434",
        model_name="qwen2.5:3b-instruct",
        temperature=0.2,
        timeout_seconds=12,
        max_retries=max_retries,
    )


def test_build_chat_payload_has_expected_fields() -> None:
    client = OllamaClient(config=_config(), session=FakeSessionSuccess())

    payload = client.build_chat_payload(
        messages=[{"role": "user", "content": "hi"}],
        model_name="qwen2.5:3b-instruct",
        temperature=0.2,
    )

    assert payload["model"] == "qwen2.5:3b-instruct"
    assert payload["stream"] is False
    assert payload["options"]["temperature"] == 0.2


def test_chat_retries_once_on_timeout_then_succeeds() -> None:
    fake_session = FakeSessionTimeoutThenSuccess()
    client = OllamaClient(config=_config(max_retries=1), session=fake_session, retry_sleep_seconds=0)

    output = client.chat(messages=[{"role": "user", "content": "hello"}])

    assert output == "ok after retry"
    assert fake_session.calls == 2


def test_chat_returns_none_on_http_error_without_retry() -> None:
    fake_session = FakeSessionHttpError()
    client = OllamaClient(config=_config(max_retries=3), session=fake_session, retry_sleep_seconds=0)

    output = client.chat(messages=[{"role": "user", "content": "hello"}])

    assert output is None
    assert fake_session.calls == 1
