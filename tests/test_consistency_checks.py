"""Simple tests for extended deterministic consistency checks."""

from __future__ import annotations

from src.rules.consistency_checks import check_inconsistency_items


def test_income_loan_ratio_alert_is_emitted() -> None:
    app = {
        "requested_amount": 50000,
        "monthly_income": 3000,
    }
    parsed_note = {}

    items = check_inconsistency_items(app, parsed_note, documents=[])
    assert any(item["code"] == "INC_INCOME_LOAN_RATIO" for item in items)


def test_employment_income_mismatch_alert_is_emitted() -> None:
    app = {
        "employment_status": "unemployed",
        "monthly_income": 1200,
    }
    parsed_note = {}

    items = check_inconsistency_items(app, parsed_note, documents=[])
    assert any(item["code"] == "INC_EMPLOYMENT_INCOME_MISMATCH" for item in items)


def test_high_debt_burden_alert_is_emitted() -> None:
    app = {
        "debt_to_income_ratio": 0.75,
    }
    parsed_note = {}

    items = check_inconsistency_items(app, parsed_note, documents=[])
    assert any(item["code"] == "RISK_HIGH_DEBT_BURDEN" for item in items)


def test_ambiguous_context_alert_is_emitted() -> None:
    app = {}
    parsed_note = {"mentions_ambiguous_context": True}

    items = check_inconsistency_items(app, parsed_note, documents=[])
    assert any(item["code"] == "AMB_NOTE_CONTEXT_UNCLEAR" for item in items)
