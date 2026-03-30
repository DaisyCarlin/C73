import streamlit as st
from datetime import datetime, timezone

st.set_page_config(
    page_title="Signal Console",
    page_icon="◉",
    layout="wide",
)

# ✅ FIXED PAGE PATHS (MATCH YOUR FILES)
PAGE_PATHS = {
    "launch": "pages/1_Orbital_Launch_Monitor.py",
    "satellite": "pages/3_Satellite_Activity.py",
    "strategic": "pages/Strategic_Insights.py",
}

# ================================
# DATA
# ================================

STATUS_CARDS = [
    {"title": "Platform Status", "value": "Operational", "meta": "All systems online", "tone": "green"},
    {"title": "Launch Monitor", "value": "Live", "meta": "Tracking active missions", "tone": "blue"},
    {"title": "Satellite Monitor", "value": "Active", "meta": "Orbital tracking stable", "tone": "blue"},
    {"title": "Strategic Insights", "value": "Watch", "meta": "Notable patterns detected", "tone": "amber"},
]

PREVIEW_CARDS = [
    {
        "eyebrow": "Launch Activity",
        "title": "Launch cadence concentrated in key providers",
        "lines": [
            "Upcoming launches clustered across a small set of operators.",
            "Sustained orbital deployment tempo observed.",
        ],
        "tone": "blue",
    },
    {
        "eyebrow": "Satellite Activity",
        "title": "Persistent watchlist density across orbital layers",
        "lines": [
            "Tracked objects show continued strategic positioning.",
            "Coverage suggests long-term monitoring behaviour.",
        ],
        "tone": "blue",
    },
    {
        "eyebrow": "Strategic Insight",
        "title": "Orbital behaviour reflects sustained activity patterns",
        "lines": [
            "Signal strength driven by cumulative activity, not isolated events.",
            "Cross-domain orbital pressure remains elevated.",
        ],
        "tone": "amber",
    },
]

MODULE_CARDS = [
    {
        "title": "Launch Intelligence",
        "description": "Monitor upcoming launches and recent missions.",
        "bullets": ["Upcoming launches", "Recent missions", "Provider trends"],
        "key": "launch",
    },
    {
        "title": "Satellite Watch",
        "description": "Track orbital activity and satellite positioning.",
        "bullets": ["Tracked satellites", "Orbital activity", "Watchlists"],
        "key": "satellite",
    },
    {
        "title": "Strategic Insights",
        "description": "Analyse patterns and orbital behaviour.",
        "bullets": ["Trend analysis", "Pattern detection", "Strategic signals"],
        "key": "strategic",
    },
]

# ================================
# STYLING
# ================================

st.markdown("""
<style>
body {color: white;}
.card {
    padding: 20px;
    border-radius: 16px;
    background: rgba(20,25,35,0.9);
    border: 1px solid rgba(255,255,255,0.05);
}
.title {font-size: 36px; font-weight: 700;}
.subtitle {color: #9fb3c8; font-size: 14px;}
.section {margin-top: 40px;}
</style>
""", unsafe_allow_html=True)

# ================================
# HERO
# ================================

current_time = datetime.now(timezone.utc).strftime("%d %b %Y • %H:%M UTC")

st.markdown(f"""
<div class="card">
    <div class="title">Signal Console</div>
    <div class="subtitle">Open-source orbital intelligence platform</div>
    <br>
    Monitor launches, satellite activity, and strategic orbital patterns from one workspace.
    <br><br>
    <b>System Time:</b> {current_time}
</div>
""", unsafe_allow_html=True)

# ================================
# STATUS
# ================================

st.markdown('<div class="section"></div>', unsafe_allow_html=True)
cols = st.columns(4)

for col, card in zip(cols, STATUS_CARDS):
    with col:
        st.markdown(f"""
        <div class="card">
            <div class="subtitle">{card['title']}</div>
            <div style="font-size:22px;font-weight:700;">{card['value']}</div>
            <div class="subtitle">{card['meta']}</div>
        </div>
        """, unsafe_allow_html=True)

# ================================
# PREVIEW
# ================================

st.markdown('<div class="section"></div>', unsafe_allow_html=True)
st.markdown("## Intelligence Snapshot")

cols = st.columns(3)

for col, card in zip(cols, PREVIEW_CARDS):
    with col:
        lines = "<br>".join(card["lines"])
        st.markdown(f"""
        <div class="card">
            <div class="subtitle">{card['eyebrow']}</div>
            <b>{card['title']}</b><br><br>
            {lines}
        </div>
        """, unsafe_allow_html=True)

# ================================
# MODULES
# ================================

st.markdown('<div class="section"></div>', unsafe_allow_html=True)
st.markdown("## Modules")

cols = st.columns(3)

for col, card in zip(cols, MODULE_CARDS):
    with col:
        bullets = "<br>".join([f"• {b}" for b in card["bullets"]])

        st.markdown(f"""
        <div class="card">
            <b>{card['title']}</b><br><br>
            {card['description']}<br><br>
            {bullets}
        </div>
        """, unsafe_allow_html=True)

        # ✅ FIXED LINK (NO ICON ERROR)
        st.page_link(
            PAGE_PATHS[card["key"]],
            label=f"Open {card['title']}",
        )

# ================================
# PURPOSE
# ================================

st.markdown('<div class="section"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="card">
    <div class="subtitle">Platform Purpose</div>
    Signal Console provides a command-level overview of orbital activity,
    enabling rapid understanding before deep analysis.
</div>
""", unsafe_allow_html=True)