"""
Batch dashboard for scoring multiple applications.

This page allows the user to upload a CSV of applications with the same
schema as the synthetic dataset.  It scores each application using the
baseline model and displays aggregated results including a histogram of
risk scores and counts per class.
"""

import streamlit as st
import pandas as pd
import numpy as np

from src.models.raw_runtime_loader import predict_application_real
from src.config.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    st.title("Batch Dashboard")
    st.markdown(
        """
        Upload a CSV file of applications to score them in bulk.  The file
        should include at least the columns defined in the data dictionary.
        """
    )
    uploaded = st.file_uploader("Choose CSV file", type="csv")
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            return
        # Preprocess and score each row
        results = []
        for _, row in df.iterrows():
            app_dict = row.to_dict()
            try:
                res = predict_application_real(app_dict)
                results.append({
                    "application_id": app_dict.get("application_id", ""),
                    "risk_score": res["risk_score"],
                    "risk_class": res["risk_class"],
                    "completeness": res["completeness"],
                    "threshold_used": res.get("threshold_used", 0.5),
                })
            except Exception as exc:
                logger.error(f"Failed to score application {app_dict.get('application_id')}: {exc}")
        if results:
            results_df = pd.DataFrame(results)
            st.subheader("Aggregate Metrics")
            st.write(results_df.describe())
            st.subheader("Risk Class Counts")
            counts = results_df["risk_class"].value_counts()
            st.bar_chart(counts)
            st.subheader("Risk Score Distribution")
            hist_counts, bin_edges = np.histogram(results_df["risk_score"], bins=20, range=(0.0, 1.0))
            hist_df = pd.DataFrame({
                "bin_left": bin_edges[:-1],
                "count": hist_counts,
            }).set_index("bin_left")
            st.bar_chart(hist_df)
            st.subheader("Detailed Results")
            st.dataframe(results_df)


if __name__ == "__main__":
    main()