import streamlit as st

st.set_page_config(
    page_title="C7 Console",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide the default first nav item from the sidebar
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

# Automatically send the user straight to Home
st.switch_page("pages/0_Home.py")