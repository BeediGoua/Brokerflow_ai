"""
Chart helper functions.
"""

import streamlit as st
import pandas as pd


def risk_class_bar(counts: pd.Series) -> None:
    """Display a bar chart of risk class counts."""
    st.bar_chart(counts)


def score_histogram(scores: pd.Series, bins: int = 20) -> None:
    """Display a histogram of risk scores."""
    import numpy as np
    hist, bin_edges = np.histogram(scores, bins=bins)
    chart_data = pd.DataFrame({
        'bins': bin_edges[:-1],
        'counts': hist,
    })
    st.bar_chart(chart_data.set_index('bins'))