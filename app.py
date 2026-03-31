with st.sidebar:
    st.markdown("### Signal Console")
    st.page_link("pages/0_Home.py", label="Home")
    st.page_link("pages/1_Orbital_Launch_Monitor.py", label="Launch Intelligence")
    st.page_link("pages/2_Satellite_Activity.py", label="Satellite Watch")
    st.page_link("pages/3_Strategic_Insights.py", label="Strategic Insights")

import streamlit as st

st.set_page_config(
    page_title="Signal Console",
    page_icon="◉",
    layout="wide",
)

st.switch_page("pages/0_Home.py")

