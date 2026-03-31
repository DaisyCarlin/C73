import streamlit as st
from datetime import datetime, timezone

st.set_page_config(
    page_title="Signal Console",
    page_icon="◉",
    layout="wide",
)

PAGE_PATHS = {
    "launch": "pages/1_Orbital_Launch_Monitor.py",
    "satellite": "pages/3_Satellite_Activity.py",
    "strategic": "pages/Strategic_Insights.py",
}

current_time = datetime.now(timezone.utc).strftime("%d %b %Y • %H:%M UTC")

# --------------------------------
# TODAY'S HIGHLIGHTS
# --------------------------------

HIGHLIGHT_CARDS = [
    {
        "eyebrow": "Launch Signal",
        "title": "China has multiple state-linked launches in the current watch window.",
        "lines": [
            "Public mission naming and launch patterns suggest state-linked or dual-use activity.",
            "This points to continued strategic launch tempo rather than routine-only traffic.",
        ],
        "tone": "amber",
    },
    {
        "eyebrow": "Satellite Signal",
        "title": "Sensitive orbital systems remain concentrated among a small number of state actors.",
        "lines": [
            "Military, reconnaissance, and strategic support layers still dominate the sensitive picture.",
            "That suggests orbital power remains heavily concentrated, not broadly distributed.",
        ],
        "tone": "red",
    },
    {
        "eyebrow": "Strategic Signal",
        "title": "Launch movement and orbital scale are not being led by the same actor.",
        "lines": [
            "One country may be accelerating in launches while another still holds the widest orbital footprint.",
            "That split suggests short-term activity and long-term presence are diverging.",
        ],
        "tone": "blue",
    },
]

MODULE_CARDS = [
    {
        "title": "Launch Intelligence",
        "description": "Track upcoming launches, recent mission outcomes, and state-linked launch signals.",
        "bullets": ["Upcoming launches", "Recent failures", "Sensitive mission watch"],
        "key": "launch",
    },
    {
        "title": "Satellite Watch",
        "description": "Monitor live orbital infrastructure and identify strategic or military-linked systems.",
        "bullets": ["Orbital footprint", "Strategic assets", "Sensitive layer tracking"],
        "key": "satellite",
    },
    {
        "title": "Strategic Insights",
        "description": "Turn launch and orbital data into a clearer geopolitical read of what matters.",
        "bullets": ["Key signals", "Country shifts", "Cross-page strategic read"],
        "key": "strategic",
    },
]

# --------------------------------
# STYLES
# --------------------------------

st.markdown(
    """
<style>
    :root {
        --bg-0: #07111f;
        --bg-1: #0d1b2a;
        --stroke: rgba(130, 161, 191, 0.22);
        --text-main: #e8f1fb;
        --text-soft: #91a9c3;
        --blue: #58a6ff;
        --cyan: #38bdf8;
        --amber: #ff9e3d;
        --red: #ff5f6d;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(56,189,248,.16), transparent 28%),
            radial-gradient(circle at top right, rgba(88,166,255,.12), transparent 26%),
            linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 100%);
        color: var(--text-main);
        font-family: "Aptos", "Segoe UI", sans-serif;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(9,19,32,.97), rgba(9,19,32,.92));
        border-right: 1px solid var(--stroke);
    }

    [data-testid="stSidebar"] * {
        color: var(--text-main);
    }

    .hero-card,
    .panel-card,
    .highlight-card,
    .module-card,
    .purpose-card {
        border: 1px solid var(--stroke);
        border-radius: 22px;
        background: linear-gradient(180deg, rgba(10,23,37,.92), rgba(14,31,49,.84));
        box-shadow: 0 16px 34px rgba(4,9,18,.22);
    }

    .hero-card {
        padding: 1.45rem 1.6rem;
        margin-bottom: 1rem;
    }

    .hero-kicker {
        letter-spacing: .16rem;
        font-size: .72rem;
        font-weight: 700;
        color: #84d7ff;
        margin-bottom: .45rem;
        text-transform: uppercase;
    }

    .hero-title {
        font-size: 2.45rem;
        line-height: 1.02;
        font-weight: 760;
        margin: 0;
        color: var(--text-main);
    }

    .hero-copy,
    .panel-copy,
    .highlight-copy,
    .module-copy,
    .purpose-copy {
        color: var(--text-soft);
        font-size: .96rem;
        line-height: 1.6;
    }

    .panel-header {
        margin: 1.25rem 0 .8rem 0;
    }

    .panel-title {
        color: var(--text-main);
        font-size: 1.08rem;
        font-weight: 730;
        margin-bottom: .18rem;
    }

    .highlight-card,
    .module-card {
        padding: 1rem 1rem 1rem 1rem;
        min-height: 235px;
    }

    .highlight-eyebrow {
        font-size: .76rem;
        font-weight: 760;
        text-transform: uppercase;
        letter-spacing: .12rem;
        margin-bottom: .55rem;
    }

    .highlight-title {
        font-size: 1.06rem;
        font-weight: 760;
        color: var(--text-main);
        line-height: 1.45;
        margin-bottom: .65rem;
    }

    .highlight-line {
        color: #c2d4e6;
        font-size: .92rem;
        line-height: 1.55;
        margin-bottom: .45rem;
    }

    .tone-blue .highlight-eyebrow { color: var(--cyan); }
    .tone-amber .highlight-eyebrow { color: var(--amber); }
    .tone-red .highlight-eyebrow { color: var(--red); }

    .accent-bar {
        width: 58px;
        height: 4px;
        border-radius: 999px;
        margin-bottom: .8rem;
    }

    .tone-blue .accent-bar { background: var(--cyan); }
    .tone-amber .accent-bar { background: var(--amber); }
    .tone-red .accent-bar { background: var(--red); }

    .module-title {
        color: var(--text-main);
        font-size: 1.08rem;
        font-weight: 760;
        margin-bottom: .55rem;
    }

    .module-bullet {
        color: #c2d4e6;
        font-size: .92rem;
        line-height: 1.55;
        margin: .18rem 0;
    }

    .purpose-card {
        padding: 1rem 1rem .95rem 1rem;
        margin-top: 1.2rem;
    }

    .purpose-label {
        font-size: .78rem;
        font-weight: 760;
        letter-spacing: .1rem;
        text-transform: uppercase;
        color: #84d7ff;
        margin-bottom: .4rem;
    }

    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: .45rem;
        margin-top: .9rem;
    }

    .chip {
        display: inline-block;
        padding: .28rem .62rem;
        border-radius: 999px;
        font-size: .76rem;
        font-weight: 700;
        color: #dff4ff;
        background: rgba(56,189,248,.14);
        border: 1px solid rgba(56,189,248,.24);
    }

    div[data-testid="stPageLink"] a {
        width: 100%;
        display: inline-block;
        padding: .72rem .95rem;
        border-radius: 14px;
        border: 1px solid rgba(88,166,255,.24);
        background: rgba(88,166,255,.12);
        color: #e8f1fb !important;
        text-decoration: none !important;
        font-weight: 700;
        margin-top: .65rem;
    }

    div[data-testid="stPageLink"] a:hover {
        border-color: rgba(88,166,255,.42);
        background: rgba(88,166,255,.18);
    }
</style>
""",
    unsafe_allow_html=True,
)

# --------------------------------
# HERO
# --------------------------------

st.markdown(
    f"""
<div class="hero-card">
    <div class="hero-kicker">Command Home</div>
    <div class="hero-title">Signal Console</div>
    <div class="hero-copy" style="margin-top:.75rem;">
        Open-source orbital intelligence workspace focused on launches, satellite activity,
        and the sensitive signals that matter most.
    </div>
    <div class="chip-row">
        <span class="chip">System Time: {current_time}</span>
        <span class="chip">Launch + Satellite + Strategic View</span>
        <span class="chip">Sensitive-Focused Readout</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# --------------------------------
# TODAY'S HIGHLIGHTS
# --------------------------------

st.markdown(
    """
<div class="panel-header">
    <div class="panel-title">Today’s Highlights</div>
    <div class="panel-copy">
        The most gripping sensitive signals pulled from across the platform.
    </div>
</div>
""",
    unsafe_allow_html=True,
)

highlight_cols = st.columns(3, gap="large")

for col, card in zip(highlight_cols, HIGHLIGHT_CARDS):
    with col:
        st.markdown(
            f"""
        <div class="highlight-card tone-{card['tone']}">
            <div class="accent-bar"></div>
            <div class="highlight-eyebrow">{card['eyebrow']}</div>
            <div class="highlight-title">{card['title']}</div>
            <div class="highlight-line">{card['lines'][0]}</div>
            <div class="highlight-line">{card['lines'][1]}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

# --------------------------------
# MODULES
# --------------------------------

st.markdown(
    """
<div class="panel-header">
    <div class="panel-title">Modules</div>
    <div class="panel-copy">
        Move from the command view into the live launch page, the satellite page, or the combined strategic readout.
    </div>
</div>
""",
    unsafe_allow_html=True,
)

module_cols = st.columns(3, gap="large")

for col, card in zip(module_cols, MODULE_CARDS):
    with col:
        bullets_html = "".join([f"<div class='module-bullet'>• {b}</div>" for b in card["bullets"]])

        st.markdown(
            f"""
        <div class="module-card">
            <div class="module-title">{card['title']}</div>
            <div class="module-copy">{card['description']}</div>
            <div style="margin-top:.85rem;">
                {bullets_html}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.page_link(
            PAGE_PATHS[card["key"]],
            label=f"Open {card['title']}",
        )

# --------------------------------
# PURPOSE
# --------------------------------

st.markdown(
    """
<div class="purpose-card">
    <div class="purpose-label">Platform Purpose</div>
    <div class="purpose-copy">
        Signal Console is designed to give a fast, high-impact read of sensitive orbital activity before a deeper dive.
        The home page should tell the user what is most striking right now, then route them straight into the relevant module.
    </div>
</div>
""",
    unsafe_allow_html=True,
)