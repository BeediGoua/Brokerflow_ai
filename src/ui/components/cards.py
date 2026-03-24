"""
Reusable card components for Streamlit.

These helper functions wrap common Streamlit widgets to display metrics
and information in a consistent style.
"""

import streamlit as st


def risk_card(risk_score: float, risk_class: str, completeness: float) -> None:
    """Display a set of metrics summarising the risk."""
    st.metric("Risk Score", f"{risk_score * 100:.1f}%")
    st.metric("Risk Class", risk_class)
    st.metric("Completeness", f"{completeness * 100:.1f}%")