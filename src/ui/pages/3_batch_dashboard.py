"""
Batch dashboard for scoring multiple applications.

This page allows the user to upload a CSV of applications with the same
schema as the synthetic dataset.  It scores each application using the
baseline model and displays aggregated results including a histogram of
risk scores and counts per class.
"""

import streamlit as st
import pandas as pd

from src.data.preprocess import preprocess_applications
from src.features.build_features import add_engineered_features
from src.features.completeness import completeness_score
from src.models.predict import predict_application, risk_class_from_score, _select_feature_columns
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
                res = predict_application(app_dict)
                results.append({
                    "application_id": app_dict.get("application_id", ""),
                    "risk_score": res["risk_score"],
                    "risk_class": res["risk_class"],
                    "completeness": res["completeness"],
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
            st.histogram(results_df["risk_score"], bins=20)
            st.subheader("Detailed Results")
            st.dataframe(results_df)


if __name__ == "__main__":
    main()