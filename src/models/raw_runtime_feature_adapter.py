"""Feature adapter from API payloads to raw-runtime model features.

The calibrated model trained in notebooks expects a specific set of numeric
and one-hot segment features.  This module builds those features from the API
schema (which is still synthetic-demo oriented), with conservative fallbacks.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def _coerce_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, str) and value.strip() == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_bool_int(value) -> int:
    if isinstance(value, bool):
        return int(value)
    return int(_coerce_float(value, default=0.0) > 0)


def _coalesce_float(app: Dict, keys: List[str], default: float = 0.0) -> float:
    for key in keys:
        if key in app and app[key] not in (None, ""):
            return _coerce_float(app[key], default=default)
    return default


def _compute_completeness(app: Dict) -> float:
    # Keep completeness simple and stable for API usage.
    required = [
        "application_id",
        "customer_id",
        "requested_amount",
        "requested_duration_months",
        "age",
        "employment_status",
    ]
    present = 0
    for key in required:
        if app.get(key) not in (None, ""):
            present += 1
    return present / len(required)


def build_raw_runtime_feature_frame(
    app_dict: Dict,
    feature_cols: List[str],
) -> Tuple[pd.DataFrame, float, List[str]]:
    """Build a single-row feature frame aligned to selected raw-model columns."""
    loanamount = _coalesce_float(app_dict, ["loanamount", "requested_amount"], default=0.0)
    if loanamount <= 0:
        loanamount = max(_coalesce_float(app_dict, ["monthly_income"], default=0.0) * 0.5, 1.0)

    termdays = _coalesce_float(app_dict, ["termdays"], default=0.0)
    if termdays <= 0:
        # Convert months to days for compatibility with raw-data termdays.
        termdays = max(_coalesce_float(app_dict, ["requested_duration_months"], default=1.0) * 30.0, 1.0)

    totaldue = _coalesce_float(app_dict, ["totaldue"], default=0.0)
    if totaldue <= 0:
        totaldue = loanamount * 1.15

    num_prev_loans = _coalesce_float(app_dict, ["num_prev_loans", "prior_loans_count"], default=0.0)
    prior_late = _coalesce_float(app_dict, ["prior_late_payments"], default=0.0)

    max_late_days = _coalesce_float(app_dict, ["max_late_days"], default=prior_late * 7.0)
    ever_late_flag = _coalesce_float(app_dict, ["ever_late_flag"], default=float(max_late_days > 0))
    ever_late_30d_flag = _coalesce_float(app_dict, ["ever_late_30d_flag"], default=float(max_late_days > 30))
    late_payment_rate = _coalesce_float(
        app_dict,
        ["late_payment_rate"],
        default=(prior_late / max(num_prev_loans, 1.0)),
    )

    avg_prev_totaldue_to_loanamount = _coalesce_float(
        app_dict,
        ["avg_prev_totaldue_to_loanamount"],
        default=1.2,
    )

    loanamount_safe = max(loanamount, 1e-6)
    due_vs_loan_ratio = totaldue / loanamount_safe

    bank_account_type = str(app_dict.get("bank_account_type", "")).strip().lower()
    is_savings_account = float(bank_account_type == "savings")
    customer_age_approx = _coalesce_float(app_dict, ["customer_age_approx", "age"], default=0.0)

    base = {
        "loanamount": loanamount,
        "termdays": termdays,
        "longitude_gps": _coalesce_float(app_dict, ["longitude_gps"], default=0.0),
        "latitude_gps": _coalesce_float(app_dict, ["latitude_gps"], default=0.0),
        "num_prev_loans": num_prev_loans,
        "late_payment_rate": late_payment_rate,
        "max_late_days": max_late_days,
        "ever_late_flag": ever_late_flag,
        "ever_late_30d_flag": ever_late_30d_flag,
        "avg_prev_totaldue_to_loanamount": avg_prev_totaldue_to_loanamount,
        "due_vs_loan_ratio": due_vs_loan_ratio,
        "is_savings_account": is_savings_account,
        "customer_age_approx": customer_age_approx,
    }

    seg_loanamount = "small"
    if loanamount > 30000:
        seg_loanamount = "large"
    elif loanamount > 10000:
        seg_loanamount = "medium"

    seg_termdays = "short"
    if termdays > 60:
        seg_termdays = "long"
    elif termdays > 30:
        seg_termdays = "mid"

    seg_pricing_ratio = "low_cost"
    if due_vs_loan_ratio > 1.35:
        seg_pricing_ratio = "high_cost"
    elif due_vs_loan_ratio > 1.20:
        seg_pricing_ratio = "standard"

    seg_age = "young"
    if customer_age_approx > 45:
        seg_age = "senior"
    elif customer_age_approx > 35:
        seg_age = "mid_career"
    elif customer_age_approx > 25:
        seg_age = "early_career"

    seg_late_behavior = "on_time"
    if max_late_days > 30:
        seg_late_behavior = "severe_delay"
    elif max_late_days > 7:
        seg_late_behavior = "moderate_delay"
    elif max_late_days > 0:
        seg_late_behavior = "minor_delay"

    segment_features = {
        "seg_loanamount_large": float(seg_loanamount == "large"),
        "seg_loanamount_medium": float(seg_loanamount == "medium"),
        "seg_termdays_mid": float(seg_termdays == "mid"),
        "seg_pricing_ratio_low_cost": float(seg_pricing_ratio == "low_cost"),
        "seg_pricing_ratio_standard": float(seg_pricing_ratio == "standard"),
        "seg_age_early_career": float(seg_age == "early_career"),
        "seg_age_young": float(seg_age == "young"),
        "seg_late_behavior_moderate_delay": float(seg_late_behavior == "moderate_delay"),
    }

    full = {**base, **segment_features}
    row = pd.DataFrame([full])

    missing_feature_cols = [c for c in feature_cols if c not in row.columns]
    for col in missing_feature_cols:
        row[col] = 0.0

    X = row[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    completeness = _compute_completeness(app_dict)
    return X, completeness, missing_feature_cols
