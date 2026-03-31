# app.py

import streamlit as st

st.set_page_config(
    page_title="C7 Console",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide the first page in Streamlit's sidebar nav ("app")
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] > ul > li:first-child {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Optional: keep this page visually minimal
st.title("C7 Console")
st.caption("Global orbital and strategic intelligence platform.")

st.markdown(
    """
    This is the hidden entry page for the app.

    Use the sidebar to open:
    - Home
    - Orbital Launch Monitor
    - Satellite Activity
    - Strategic Insights
    """
)