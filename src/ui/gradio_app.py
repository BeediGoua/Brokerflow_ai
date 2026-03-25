"""Gradio interface for BrokerFlow API scoring.

This UI sends a JSON application payload to the local FastAPI app using
TestClient, so users can test scoring without starting a separate server.
"""

from __future__ import annotations

import json
from typing import Any

import gradio as gr
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.data.generate_synthetic_cases import generate_datasets


_client = TestClient(create_app())


BROKER_CASES = {
    "clean_profile": {
        "free_text_note": "Stable job and stable income. Previous loans paid on time.",
        "prior_late_payments": 0,
        "has_prior_default": 0,
        "documents": [
            {
                "document_type": "income_proof",
                "is_required": True,
                "is_provided": True,
            }
        ],
    },
    "urgent_missing_docs": {
        "free_text_note": "Urgent need, please approve fast. Missing documents for now.",
        "prior_late_payments": 2,
        "has_prior_default": 1,
        "documents": [
            {
                "document_type": "income_proof",
                "is_required": True,
                "is_provided": False,
            },
            {
                "document_type": "bank_statement",
                "is_required": True,
                "is_provided": False,
            },
        ],
    },
    "employment_contradiction": {
        "employment_status": "unemployed",
        "free_text_note": "Client has a stable job and steady salary.",
        "documents": [
            {
                "document_type": "id_proof",
                "is_required": True,
                "is_provided": True,
            }
        ],
    },
    "negation_history": {
        "prior_late_payments": 3,
        "free_text_note": "No late payments at all, previous loans paid without delay.",
        "documents": [
            {
                "document_type": "income_proof",
                "is_required": True,
                "is_provided": True,
            }
        ],
    },
    "ambiguous_context": {
        "free_text_note": "Maybe there were a few delays, perhaps not impossible to verify later.",
        "documents": [
            {
                "document_type": "income_proof",
                "is_required": True,
                "is_provided": True,
            }
        ],
    },
}


def _clean_for_json(value: Any) -> Any:
    """Convert NaN-like values to None for JSON compatibility."""
    # Minimal conversion without adding a pandas dependency here.
    if isinstance(value, float) and value != value:
        return None
    if isinstance(value, dict):
        return {k: _clean_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean_for_json(v) for v in value]
    return value


def build_sample_payload() -> str:
    apps, _, _ = generate_datasets(n_samples=1)
    payload = apps.iloc[0].to_dict()
    payload.pop("target_risk_flag", None)
    payload = _clean_for_json(payload)
    payload["documents"] = [
        {
            "document_id": "DOC-SAMPLE-income",
            "application_id": str(payload.get("application_id", "APP-SAMPLE")),
            "document_type": "income_proof",
            "is_required": True,
            "is_provided": False,
            "document_quality_score": None,
            "extracted_text": None,
            "extraction_confidence": None,
        }
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _enrich_documents(application_id: str, docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for i, doc in enumerate(docs, start=1):
        normalized.append(
            {
                "document_id": f"DOC-{application_id}-{i}",
                "application_id": application_id,
                "document_type": doc.get("document_type", "unknown_document"),
                "is_required": bool(doc.get("is_required", True)),
                "is_provided": bool(doc.get("is_provided", False)),
                "document_quality_score": doc.get("document_quality_score"),
                "extracted_text": doc.get("extracted_text"),
                "extraction_confidence": doc.get("extraction_confidence"),
            }
        )
    return normalized


def build_broker_case_payload(case_name: str) -> str:
    base = json.loads(build_sample_payload())
    selected = BROKER_CASES.get(case_name, BROKER_CASES["clean_profile"])
    for key, value in selected.items():
        if key == "documents":
            continue
        base[key] = value

    app_id = str(base.get("application_id", "APP-SAMPLE"))
    base["documents"] = _enrich_documents(app_id, selected.get("documents", []))
    return json.dumps(base, ensure_ascii=False, indent=2)


def score_payload(payload_text: str, api_route: str) -> tuple[str, dict[str, Any], str]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        return (
            f"Invalid JSON input: {exc}",
            {},
            "Provide a valid JSON object for the application payload.",
        )

    if not isinstance(payload, dict):
        return ("Payload must be a JSON object.", {}, "Top-level JSON must be an object.")

    response = _client.post(api_route, json=payload)
    if response.status_code != 200:
        detail = ""
        try:
            detail = json.dumps(response.json(), ensure_ascii=False)
        except Exception:
            detail = response.text
        return (
            f"Request failed ({response.status_code})",
            {},
            detail,
        )

    result = response.json()
    summary = (
        f"Recommendation: {result.get('recommendation', 'n/a')}\n"
        f"Risk score: {result.get('risk_score', 'n/a')}\n"
        f"Risk class: {result.get('risk_class', 'n/a')}\n"
        f"Alerts: {len(result.get('alerts', []))}"
    )
    return ("Scoring completed.", result, summary)


def run_broker_suite(api_route: str) -> tuple[str, list[list[Any]], dict[str, Any]]:
    rows: list[list[Any]] = []
    raw_outputs: dict[str, Any] = {}

    for case_name in BROKER_CASES:
        payload = json.loads(build_broker_case_payload(case_name))
        response = _client.post(api_route, json=payload)
        if response.status_code != 200:
            rows.append([case_name, "error", "n/a", "n/a", response.status_code])
            raw_outputs[case_name] = {"status": response.status_code, "body": response.text}
            continue

        body = response.json()
        rows.append(
            [
                case_name,
                body.get("recommendation", "n/a"),
                body.get("risk_score", "n/a"),
                len(body.get("alerts", [])),
                body.get("decision_alert_severity", "n/a"),
            ]
        )
        raw_outputs[case_name] = body

    return ("Broker suite executed.", rows, raw_outputs)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="BrokerFlow Gradio Demo") as demo:
        gr.Markdown("# BrokerFlow AI - Gradio Scoring Demo")
        gr.Markdown(
            "Use broker scenarios or paste your own JSON payload. "
            "This uses FastAPI TestClient internally (no separate API server required)."
        )

        with gr.Row():
            api_route = gr.Dropdown(
                label="Endpoint",
                choices=["/v1/score", "/v2/score"],
                value="/v2/score",
            )

        with gr.Row():
            broker_case = gr.Dropdown(
                label="Broker test case",
                choices=list(BROKER_CASES.keys()),
                value="clean_profile",
            )
            load_case_btn = gr.Button("Load broker case")
            run_suite_btn = gr.Button("Run full broker suite")

        payload_box = gr.Code(
            label="Application Payload JSON",
            value=build_broker_case_payload("clean_profile"),
            language="json",
            lines=24,
        )

        with gr.Row():
            score_btn = gr.Button("Score payload", variant="primary")
            sample_btn = gr.Button("Load new sample")

        status_out = gr.Textbox(label="Status")
        quick_summary_out = gr.Textbox(label="Quick Result Summary")
        result_out = gr.JSON(label="Raw API Output")
        suite_status_out = gr.Textbox(label="Suite Status")
        suite_table_out = gr.Dataframe(
            headers=["case", "recommendation", "risk_score", "alerts_count", "severity"],
            datatype=["str", "str", "number", "number", "str"],
            label="Broker Suite Results",
        )
        suite_raw_out = gr.JSON(label="Broker Suite Raw Outputs")

        score_btn.click(
            fn=score_payload,
            inputs=[payload_box, api_route],
            outputs=[status_out, result_out, quick_summary_out],
        )
        sample_btn.click(fn=build_sample_payload, inputs=[], outputs=[payload_box])
        load_case_btn.click(fn=build_broker_case_payload, inputs=[broker_case], outputs=[payload_box])
        run_suite_btn.click(
            fn=run_broker_suite,
            inputs=[api_route],
            outputs=[suite_status_out, suite_table_out, suite_raw_out],
        )

    return demo


def main() -> None:
    app = build_app()
    app.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
