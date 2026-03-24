"""
Streamlit main entrypoint.

This file sets the overall page configuration and serves as a landing page
when running ``streamlit run src/ui/app.py``.  Streamlit automatically
discovers page modules under the ``pages`` directory, so no further
navigation logic is needed here.
"""

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="BrokerFlow AI Demo", page_icon="🤖", layout="centered")
    st.title("BrokerFlow AI – Underwriting Copilot")
    st.markdown(
        """
        Welcome to the BrokerFlow AI demo application.  Use the sidebar to navigate
        between pages.  You can upload a single application, view a processed
        result or score a batch of applications via CSV.  See the README for
        setup instructions.
        """
    )


if __name__ == "__main__":
    main()