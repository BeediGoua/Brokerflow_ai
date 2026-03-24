"""
Upload or manually enter a single application for scoring.

This page allows the user to input application details via a simple form
and instantly view the model prediction, alerts, recommendation and
summary.  It does not require the FastAPI server to be running as it
invokes the prediction code directly.
"""

import streamlit as st

from src.models.raw_runtime_loader import predict_application_real
from src.agents.note_parser import parse_note
from src.agents.reviewer import review_application, review_application_detailed
from src.agents.summary_writer import write_summary
from src.rules.recommendation import recommend_detailed


def display_result(result):
    st.subheader("Result")
    st.metric("Risk Score", f"{result['risk_score']*100:.1f}%")
    st.metric("Risk Class", result['risk_class'])
    st.metric("Completeness", f"{result['completeness']*100:.1f}%")
    st.write("**Top Factors:**")
    for feat, contrib in result['top_factors']:
        st.write(f"- {feat}: {contrib:+.2f}")


def main() -> None:
    st.title("Upload / Enter Application")
    with st.form(key="upload_form"):
        st.text("Enter the main details of the application.  Fields left blank will be imputed.")
        application_id = st.text_input("Application ID", value="APP10000")
        customer_id = st.text_input("Customer ID", value="CUST10000")
        snapshot_date = st.date_input("Snapshot Date").strftime("%Y-%m-%d")
        age = st.number_input("Age", min_value=18, max_value=100, value=35)
        monthly_income = st.number_input("Monthly Income", min_value=0.0, value=5000.0, step=100.0)
        existing_debt = st.number_input("Existing Debt", min_value=0.0, value=10000.0, step=500.0)
        requested_amount = st.number_input("Requested Amount", min_value=0.0, value=15000.0, step=500.0)
        requested_duration_months = st.number_input("Requested Duration (months)", min_value=1, max_value=120, value=36)
        years_in_job = st.number_input("Years in Job", min_value=0, max_value=40, value=5)
        income_stability_score = st.slider("Income Stability Score", min_value=0.0, max_value=1.0, value=0.5)
        prior_loans_count = st.number_input("Prior Loans Count", min_value=0, max_value=20, value=2)
        prior_late_payments = st.number_input("Prior Late Payments", min_value=0, max_value=20, value=0)
        has_prior_default = st.checkbox("Has Prior Default")
        free_text_note = st.text_area("Free Text Note", value="steady income; previous loans paid")
        submit = st.form_submit_button("Score Application")
    if submit:
        # Build application dictionary
        app_dict = {
            "application_id": application_id,
            "customer_id": customer_id,
            "snapshot_date": snapshot_date,
            "age": age,
            "monthly_income": monthly_income,
            "existing_debt": existing_debt,
            "requested_amount": requested_amount,
            "requested_duration_months": requested_duration_months,
            "years_in_job": years_in_job,
            "income_stability_score": income_stability_score,
            "prior_loans_count": prior_loans_count,
            "prior_late_payments": prior_late_payments,
            "has_prior_default": 1 if has_prior_default else 0,
            "free_text_note": free_text_note,
        }
        # Predict
        result = predict_application_real(app_dict)
        # Parse note
        parsed = parse_note(app_dict["free_text_note"])
        # No documents in this demo
        docs = []
        alerts = review_application(app_dict, parsed, docs)
        alert_items = review_application_detailed(app_dict, parsed, docs)
        severity_rank = {"none": 0, "low": 1, "medium": 2, "high": 3}
        derived_severity = "none"
        for item in alert_items:
            sev = str(item.get("severity", "low")).lower()
            if sev in severity_rank and severity_rank[sev] > severity_rank[derived_severity]:
                derived_severity = sev

        decision = recommend_detailed(
            risk_score=result["risk_score"],
            threshold=result.get("threshold_used", 0.5),
            completeness=result["completeness"],
            alerts=alerts,
            alert_severity=derived_severity,
        )
        rec = decision.action
        summary = write_summary(result["risk_class"], result["risk_score"], result["top_factors"], rec, alerts)
        # Display
        display_result(result)
        st.subheader("Alerts")
        if alerts:
            for alert in alerts:
                st.error(alert)
        else:
            st.success("No alerts detected.")
        st.subheader("Recommendation")
        st.write(f"**{rec}**")
        st.caption(
            f"Severity={decision.alert_severity} | Bucket={decision.completeness_bucket} | "
            f"Threshold={result.get('threshold_used', 0.5):.3f}"
        )
        st.subheader("Summary")
        st.write(summary)


if __name__ == "__main__":
    main()