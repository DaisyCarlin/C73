import streamlit as st
from datetime import datetime, timezone

st.set_page_config(
    page_title="Signal Console",
    page_icon="◉",
    layout="wide",
)

# =========================================================
# CONFIG
# Update these to match your actual Streamlit page filenames
# =========================================================
PAGE_PATHS = {
    "launch": "pages/Launch_Intelligence.py",
    "satellite": "pages/Satellite_Watch.py",
    "strategic": "pages/Strategic_Insights.py",
}

STATUS_CARDS = [
    {
        "title": "Platform Status",
        "value": "Operational",
        "meta": "All services online",
        "tone": "green",
    },
    {
        "title": "Launch Monitor",
        "value": "Live",
        "meta": "Tracking current launch cycle",
        "tone": "blue",
    },
    {
        "title": "Satellite Monitor",
        "value": "Active",
        "meta": "Watchlists and orbital feeds updating",
        "tone": "blue",
    },
    {
        "title": "Strategic Insights",
        "value": "Watch",
        "meta": "Notable orbital patterns flagged",
        "tone": "amber",
    },
]

PREVIEW_CARDS = [
    {
        "eyebrow": "Launch Activity Preview",
        "title": "Launch cadence remains concentrated in major providers",
        "lines": [
            "Upcoming launch windows remain clustered around a small set of high-frequency operators.",
            "Recent mission tempo suggests sustained orbital deployment pressure rather than isolated activity.",
        ],
        "tag": "Open module",
        "tone": "blue",
    },
    {
        "eyebrow": "Satellite Activity Preview",
        "title": "Watchlist movement highlights sustained orbital persistence",
        "lines": [
            "Tracked objects continue to show meaningful watchlist density across strategic orbital layers.",
            "Coverage focus suggests persistent monitoring value rather than one-off event observation.",
        ],
        "tag": "View page",
        "tone": "blue",
    },
    {
        "eyebrow": "Strategic Insight Preview",
        "title": "Orbital behavior is best read as pattern, not headline",
        "lines": [
            "Platform synthesis indicates that launch tempo, orbital presence, and asset concentration should be interpreted together.",
            "The most useful signal is often cumulative pressure across time, geography, and mission type.",
        ],
        "tag": "Review insights",
        "tone": "amber",
    },
]

MODULE_CARDS = [
    {
        "title": "Launch Intelligence",
        "description": "Monitor upcoming launches, recent missions, and launch-pattern changes across the orbital environment.",
        "bullets": [
            "Upcoming launch windows",
            "Recent launch activity",
            "Provider and mission pattern tracking",
        ],
        "key": "launch",
        "tone": "blue",
    },
    {
        "title": "Satellite Watch",
        "description": "Track satellite presence, watchlists, and orbital activity layers from a single operational workspace.",
        "bullets": [
            "Watchlisted orbital objects",
            "Satellite activity views",
            "Persistent monitoring snapshots",
        ],
        "key": "satellite",
        "tone": "blue",
    },
    {
        "title": "Strategic Insights",
        "description": "Translate raw orbital signals into higher-level strategic interpretation and notable pattern detection.",
        "bullets": [
            "Cross-module signal synthesis",
            "Strategic pattern summaries",
            "Notable orbital developments",
        ],
        "key": "strategic",
        "tone": "amber",
    },
]


def inject_styles():
    st.markdown(
        """
        <style>
            :root {
                --bg-0: #04070d;
                --bg-1: #08111d;
                --bg-2: #0c1725;
                --panel: rgba(11, 20, 32, 0.84);
                --panel-strong: rgba(10, 18, 30, 0.94);
                --stroke: rgba(126, 154, 184, 0.18);
                --stroke-strong: rgba(126, 154, 184, 0.28);

                --text-main: #edf4ff;
                --text-soft: #8fa5bf;
                --text-muted: #6d8298;

                --blue: #4ea1ff;
                --blue-soft: rgba(78, 161, 255, 0.16);

                --green: #45d483;
                --green-soft: rgba(69, 212, 131, 0.16);

                --amber: #ffbe55;
                --amber-soft: rgba(255, 190, 85, 0.16);

                --red: #ff5f5f;
                --red-soft: rgba(255, 95, 95, 0.16);
            }

            .stApp {
                background:
                    radial-gradient(circle at 12% 0%, rgba(78, 161, 255, 0.10), transparent 24%),
                    radial-gradient(circle at 88% 10%, rgba(69, 212, 131, 0.05), transparent 20%),
                    linear-gradient(180deg, #06101b 0%, #04070d 100%);
                color: var(--text-main);
            }

            .block-container {
                max-width: 1380px;
                padding-top: 2rem;
                padding-bottom: 2rem;
            }

            .home-section-label {
                font-size: 0.72rem;
                letter-spacing: 0.16em;
                text-transform: uppercase;
                color: var(--text-muted);
                margin-bottom: 0.65rem;
            }

            .hero-shell {
                position: relative;
                overflow: hidden;
                border: 1px solid var(--stroke);
                border-radius: 24px;
                padding: 1.55rem 1.55rem 1.4rem 1.55rem;
                background:
                    linear-gradient(180deg, rgba(15, 27, 43, 0.92) 0%, rgba(8, 14, 22, 0.96) 100%);
                box-shadow:
                    inset 0 1px 0 rgba(255,255,255,0.03),
                    0 0 0 1px rgba(255,255,255,0.02),
                    0 24px 60px rgba(0,0,0,0.34);
            }

            .hero-shell::before {
                content: "";
                position: absolute;
                inset: 0;
                background:
                    radial-gradient(circle at top left, rgba(78, 161, 255, 0.16), transparent 30%),
                    linear-gradient(90deg, rgba(78, 161, 255, 0.06), transparent 35%, transparent 65%, rgba(69, 212, 131, 0.04));
                pointer-events: none;
            }

            .hero-topline {
                position: relative;
                z-index: 1;
                display: inline-flex;
                align-items: center;
                gap: 0.55rem;
                border: 1px solid rgba(126, 154, 184, 0.18);
                background: rgba(255,255,255,0.02);
                color: var(--text-soft);
                border-radius: 999px;
                padding: 0.42rem 0.8rem;
                font-size: 0.74rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .status-dot {
                width: 0.52rem;
                height: 0.52rem;
                border-radius: 50%;
                display: inline-block;
                box-shadow: 0 0 12px currentColor;
            }

            .status-green { color: var(--green); background: var(--green); }
            .status-blue { color: var(--blue); background: var(--blue); }
            .status-amber { color: var(--amber); background: var(--amber); }
            .status-red { color: var(--red); background: var(--red); }

            .hero-grid {
                position: relative;
                z-index: 1;
                display: grid;
                grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.65fr);
                gap: 1rem;
                align-items: end;
                margin-top: 1rem;
            }

            .hero-title {
                margin: 0;
                font-size: clamp(2.2rem, 4vw, 3.4rem);
                line-height: 0.98;
                font-weight: 700;
                color: var(--text-main);
                letter-spacing: -0.04em;
            }

            .hero-subtitle {
                margin-top: 0.6rem;
                font-size: 0.95rem;
                color: #b6c8dc;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }

            .hero-copy {
                margin-top: 1rem;
                max-width: 52rem;
                color: var(--text-soft);
                font-size: 1rem;
                line-height: 1.6;
            }

            .hero-meta {
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
                border-left: 1px solid rgba(126, 154, 184, 0.14);
                padding-left: 1rem;
                min-height: 100%;
                justify-content: end;
            }

            .hero-meta-card {
                border: 1px solid rgba(126, 154, 184, 0.15);
                background: rgba(255,255,255,0.025);
                border-radius: 18px;
                padding: 0.9rem 1rem;
            }

            .hero-meta-label {
                color: var(--text-muted);
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                margin-bottom: 0.35rem;
            }

            .hero-meta-value {
                color: var(--text-main);
                font-size: 1.15rem;
                font-weight: 600;
            }

            .hero-meta-caption {
                color: var(--text-soft);
                font-size: 0.85rem;
                margin-top: 0.25rem;
            }

            .panel-card {
                position: relative;
                overflow: hidden;
                min-height: 132px;
                border: 1px solid var(--stroke);
                background:
                    linear-gradient(180deg, rgba(12, 20, 32, 0.92) 0%, rgba(8, 14, 22, 0.98) 100%);
                border-radius: 20px;
                padding: 1rem 1rem 0.95rem 1rem;
                box-shadow:
                    inset 0 1px 0 rgba(255,255,255,0.02),
                    0 14px 38px rgba(0,0,0,0.22);
            }

            .panel-card::after {
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.10), transparent);
                opacity: 0.5;
            }

            .tone-blue { box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 14px 38px rgba(0,0,0,0.22), 0 0 0 1px rgba(78, 161, 255, 0.03); }
            .tone-green { box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 14px 38px rgba(0,0,0,0.22), 0 0 0 1px rgba(69, 212, 131, 0.03); }
            .tone-amber { box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 14px 38px rgba(0,0,0,0.22), 0 0 0 1px rgba(255, 190, 85, 0.03); }
            .tone-red { box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 14px 38px rgba(0,0,0,0.22), 0 0 0 1px rgba(255, 95, 95, 0.03); }

            .panel-top {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 0.8rem;
                margin-bottom: 0.65rem;
            }

            .panel-label {
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.11em;
                font-size: 0.72rem;
            }

            .panel-value {
                color: var(--text-main);
                font-weight: 700;
                font-size: 1.22rem;
                margin-top: 0.2rem;
                line-height: 1.05;
            }

            .panel-meta {
                color: var(--text-soft);
                font-size: 0.9rem;
                line-height: 1.45;
            }

            .tone-pill {
                display: inline-flex;
                align-items: center;
                gap: 0.38rem;
                border-radius: 999px;
                padding: 0.35rem 0.62rem;
                font-size: 0.7rem;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                border: 1px solid transparent;
                white-space: nowrap;
            }

            .pill-blue  { background: var(--blue-soft); border-color: rgba(78,161,255,0.20); color: #91c4ff; }
            .pill-green { background: var(--green-soft); border-color: rgba(69,212,131,0.20); color: #8de1b4; }
            .pill-amber { background: var(--amber-soft); border-color: rgba(255,190,85,0.20); color: #ffd18a; }
            .pill-red   { background: var(--red-soft); border-color: rgba(255,95,95,0.20); color: #ffadad; }

            .section-header {
                display: flex;
                align-items: end;
                justify-content: space-between;
                gap: 1rem;
                margin: 0.15rem 0 0.9rem 0;
            }

            .section-title {
                font-size: 1.22rem;
                font-weight: 650;
                color: var(--text-main);
                margin: 0;
                letter-spacing: -0.02em;
            }

            .section-copy {
                color: var(--text-soft);
                font-size: 0.94rem;
                margin: 0.2rem 0 0 0;
                max-width: 60rem;
            }

            .preview-card {
                min-height: 210px;
            }

            .preview-eyebrow {
                color: var(--text-muted);
                font-size: 0.72rem;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                margin-bottom: 0.6rem;
            }

            .preview-title {
                color: var(--text-main);
                font-size: 1.05rem;
                font-weight: 650;
                line-height: 1.35;
                margin-bottom: 0.85rem;
            }

            .preview-line {
                color: var(--text-soft);
                font-size: 0.92rem;
                line-height: 1.5;
                margin-bottom: 0.5rem;
            }

            .preview-cta {
                margin-top: 1rem;
                color: var(--text-main);
                font-size: 0.82rem;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
            }

            .preview-cta span {
                color: var(--text-muted);
            }

            .module-card {
                min-height: 250px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                margin-bottom: 0.7rem;
            }

            .module-title {
                color: var(--text-main);
                font-size: 1.18rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                margin-bottom: 0.55rem;
            }

            .module-copy {
                color: var(--text-soft);
                font-size: 0.93rem;
                line-height: 1.55;
                margin-bottom: 1rem;
            }

            .module-list {
                list-style: none;
                padding: 0;
                margin: 0;
                display: grid;
                gap: 0.5rem;
            }

            .module-list li {
                display: flex;
                align-items: center;
                gap: 0.55rem;
                color: #c5d4e4;
                font-size: 0.9rem;
            }

            .module-list li::before {
                content: "";
                width: 0.34rem;
                height: 0.34rem;
                border-radius: 50%;
                background: var(--blue);
                box-shadow: 0 0 8px rgba(78,161,255,0.6);
                flex: 0 0 auto;
            }

            .module-footer {
                margin-top: 1.2rem;
                padding-top: 0.95rem;
                border-top: 1px solid rgba(126, 154, 184, 0.12);
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1rem;
            }

            .module-affordance {
                color: var(--text-main);
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }

            .purpose-panel {
                border: 1px solid var(--stroke);
                border-radius: 20px;
                background: linear-gradient(180deg, rgba(11, 19, 30, 0.92) 0%, rgba(8, 14, 22, 0.98) 100%);
                padding: 1.15rem 1.15rem 1.1rem 1.15rem;
            }

            .purpose-label {
                color: var(--text-muted);
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                margin-bottom: 0.45rem;
            }

            .purpose-text {
                color: var(--text-soft);
                font-size: 0.96rem;
                line-height: 1.65;
                max-width: 70rem;
            }

            div[data-testid="stPageLink"] {
                width: 100%;
            }

            div[data-testid="stPageLink"] a {
                width: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                text-decoration: none !important;
                border-radius: 14px;
                border: 1px solid rgba(126, 154, 184, 0.16);
                background: rgba(255,255,255,0.03);
                color: var(--text-main) !important;
                min-height: 2.8rem;
                font-weight: 600;
                letter-spacing: 0.01em;
                transition: all 0.18s ease;
            }

            div[data-testid="stPageLink"] a:hover {
                border-color: rgba(126, 154, 184, 0.30);
                background: rgba(255,255,255,0.05);
                transform: translateY(-1px);
                box-shadow: 0 8px 22px rgba(0,0,0,0.18);
            }

            div[data-testid="stPageLink"] p {
                color: var(--text-main) !important;
                font-size: 0.94rem !important;
                font-weight: 600 !important;
                margin: 0 !important;
            }

            @media (max-width: 980px) {
                .hero-grid {
                    grid-template-columns: 1fr;
                }

                .hero-meta {
                    border-left: none;
                    padding-left: 0;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def tone_pill(tone: str, label: str) -> str:
    pill_class = {
        "blue": "pill-blue",
        "green": "pill-green",
        "amber": "pill-amber",
        "red": "pill-red",
    }.get(tone, "pill-blue")

    dot_class = {
        "blue": "status-blue",
        "green": "status-green",
        "amber": "status-amber",
        "red": "status-red",
    }.get(tone, "status-blue")

    return f"""
        <div class="tone-pill {pill_class}">
            <span class="status-dot {dot_class}"></span>
            {label}
        </div>
    """


def render_hero():
    current_utc = datetime.now(timezone.utc).strftime("%d %b %Y • %H:%M UTC")

    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-topline">
                <span class="status-dot status-green"></span>
                Command Home • Internal Workspace
            </div>

            <div class="hero-grid">
                <div>
                    <h1 class="hero-title">Signal Console</h1>
                    <div class="hero-subtitle">Open-source orbital intelligence platform</div>
                    <div class="hero-copy">
                        Monitor launches, satellite activity, and strategic orbital patterns from one
                        operational workspace built for fast situational understanding and clear navigation.
                    </div>
                </div>

                <div class="hero-meta">
                    <div class="hero-meta-card">
                        <div class="hero-meta-label">Workspace posture</div>
                        <div class="hero-meta-value">Live orbital monitoring environment</div>
                        <div class="hero-meta-caption">Designed for overview first, module depth second.</div>
                    </div>
                    <div class="hero-meta-card">
                        <div class="hero-meta-label">System time</div>
                        <div class="hero-meta-value">{current_utc}</div>
                        <div class="hero-meta-caption">Signals, previews, and routing from a unified front door.</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_row():
    st.markdown('<div class="home-section-label">Overview</div>', unsafe_allow_html=True)

    cols = st.columns(4, gap="medium")
    for col, card in zip(cols, STATUS_CARDS):
        with col:
            st.markdown(
                f"""
                <div class="panel-card tone-{card['tone']}">
                    <div class="panel-top">
                        <div>
                            <div class="panel-label">{card['title']}</div>
                            <div class="panel-value">{card['value']}</div>
                        </div>
                        {tone_pill(card['tone'], card['value'])}
                    </div>
                    <div class="panel-meta">{card['meta']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_preview_section():
    st.markdown(
        """
        <div class="section-header">
            <div>
                <h2 class="section-title">Intelligence Snapshot</h2>
                <p class="section-copy">
                    Concise previews from the platform’s three core modules. Enough to orient the user,
                    not enough to replace the deeper pages.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3, gap="medium")
    for col, card in zip(cols, PREVIEW_CARDS):
        with col:
            lines_html = "".join([f'<div class="preview-line">{line}</div>' for line in card["lines"]])
            st.markdown(
                f"""
                <div class="panel-card preview-card tone-{card['tone']}">
                    <div class="preview-eyebrow">{card['eyebrow']}</div>
                    <div class="preview-title">{card['title']}</div>
                    {lines_html}
                    <div class="preview-cta">{card['tag']} <span>→</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_module_navigation():
    st.markdown(
        """
        <div class="section-header">
            <div>
                <h2 class="section-title">Modules</h2>
                <p class="section-copy">
                    Enter the core workspaces for deeper operational detail.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3, gap="medium")
    for col, card in zip(cols, MODULE_CARDS):
        with col:
            bullets = "".join([f"<li>{item}</li>" for item in card["bullets"]])

            st.markdown(
                f"""
                <div class="panel-card module-card tone-{card['tone']}">
                    <div>
                        <div class="module-title">{card['title']}</div>
                        <div class="module-copy">{card['description']}</div>
                        <ul class="module-list">
                            {bullets}
                        </ul>
                    </div>
                    <div class="module-footer">
                        <div class="module-affordance">Open module</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.page_link(
                PAGE_PATHS[card["key"]],
                label=f"Go to {card['title']}",
            )


def render_purpose():
    st.markdown(
        """
        <div class="purpose-panel">
            <div class="purpose-label">Platform Purpose</div>
            <div class="purpose-text">
                Signal Console is a command-style orbital intelligence workspace built to help users
                move from quick orientation to deeper analysis. The home screen gives a fast operational
                read on launches, satellites, and strategic orbital patterns, then routes the user into
                the modules where real depth lives.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


inject_styles()
render_hero()
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
render_status_row()
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
render_preview_section()
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
render_module_navigation()
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
render_purpose()