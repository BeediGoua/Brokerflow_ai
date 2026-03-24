"""
Demo pre‑scored cases.

This page loads a synthetic dataset and allows the user to select an
application to view the model prediction, alerts, recommendation and
summary.  It demonstrates how the scoring pipeline works on multiple
examples without manually entering values.
"""

import streamlit as st
import pandas as pd

from src.data.generate_synthetic_cases import generate_datasets
from src.models.raw_runtime_loader import predict_application_real
from src.agents.note_parser import parse_note
from src.agents.reviewer import review_application, review_application_detailed
from src.agents.summary_writer import write_summary
from src.rules.recommendation import recommend_detailed


def main() -> None:
    st.title("Case Result Explorer")
    st.markdown(
        """
        Select a synthetic application from the dropdown below to see how the
        model scores it and what recommendation the rules engine produces.
        """
    )
    # Generate or load sample data in memory
    apps, docs, reviews = generate_datasets(n_samples=100)
    app_ids = apps["application_id"].tolist()
    selection = st.selectbox("Select Application", options=app_ids)
    if selection:
        app_row = apps[apps["application_id"] == selection].iloc[0]
        app_dict = app_row.to_dict()
        result = predict_application_real(app_dict)
        parsed = parse_note(app_dict.get("free_text_note", ""))
        doc_list = []  # no docs for demo
        alerts = review_application(app_dict, parsed, doc_list)
        alert_items = review_application_detailed(app_dict, parsed, doc_list)
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
        st.subheader("Risk Score")
        st.metric("Score", f"{result['risk_score']*100:.1f}%")
        st.metric("Class", result['risk_class'])
        st.metric("Completeness", f"{result['completeness']*100:.1f}%")
        st.write("**Top Factors:**")
        for feat, contrib in result['top_factors']:
            st.write(f"- {feat}: {contrib:+.2f}")
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