"""
Table helper functions for Streamlit.
"""

import streamlit as st
import pandas as pd


def data_table(df: pd.DataFrame) -> None:
    """Display a dataframe in Streamlit."""
    st.dataframe(df)