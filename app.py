import streamlit as st

st.set_page_config(page_title="Signal Console", layout="wide")


def inject_styles():
    st.markdown(
        """
        <style>
            :root {
                --bg-0: #07111f;
                --bg-1: #0d1b2a;
                --panel: rgba(10, 23, 37, 0.88);
                --panel-2: rgba(13, 28, 44, 0.88);
                --stroke: rgba(130, 161, 191, 0.20);
                --text-main: #e8f1fb;
                --text-soft: #90a9c3;
                --text-faint: #6f88a3;
                --cyan: #38bdf8;
                --blue: #60a5fa;
                --green: #39d98a;
                --amber: #fbbf24;
                --red: #fb7185;
                --violet: #8b5cf6;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(56, 189, 248, 0.14), transparent 30%),
                    radial-gradient(circle at top right, rgba(96, 165, 250, 0.10), transparent 26%),
                    linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 100%);
                color: var(--text-main);
                font-family: "Aptos", "Segoe UI", sans-serif;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(8, 18, 31, 0.98), rgba(8, 18, 31, 0.94));
                border-right: 1px solid var(--stroke);
            }

            [data-testid="stSidebar"] * {
                color: var(--text-main);
            }

            .block-container {
                padding-top: 1.6rem;
                padding-bottom: 2rem;
                max-width: 1450px;
            }

            .hero-shell {
                border: 1px solid var(--stroke);
                background: linear-gradient(145deg, rgba(8, 18, 31, 0.95), rgba(13, 28, 44, 0.92));
                border-radius: 24px;
                padding: 1.4rem 1.4rem 1.25rem 1.4rem;
                box-shadow: 0 18px 40px rgba(4, 9, 18, 0.28);
                margin-bottom: 1rem;
            }

            .hero-topline {
                display: inline-block;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.16rem;
                text-transform: uppercase;
                color: #84d7ff;
                margin-bottom: 0.55rem;
            }

            .hero-title {
                font-size: 2.6rem;
                line-height: 1.02;
                font-weight: 800;
                margin: 0;
                color: var(--text-main);
            }

            .hero-copy {
                margin: 0.65rem 0 0 0;
                max-width: 58rem;
                color: var(--text-soft);
                font-size: 1rem;
                line-height: 1.55;
            }

            .hero-divider {
                margin-top: 1rem;
                height: 1px;
                background: linear-gradient(90deg, rgba(130,161,191,0.24), rgba(130,161,191,0.02));
            }

            .metric-card {
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(11, 23, 37, 0.92), rgba(14, 30, 48, 0.82));
                border-radius: 20px;
                padding: 1rem 1rem 0.95rem 1rem;
                min-height: 132px;
                box-shadow: 0 12px 28px rgba(4, 9, 18, 0.22);
            }

            .metric-accent {
                width: 56px;
                height: 4px;
                border-radius: 999px;
                margin-bottom: 0.85rem;
            }

            .metric-label {
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.09rem;
                color: var(--text-soft);
                margin-bottom: 0.42rem;
                font-weight: 700;
            }

            .metric-value {
                font-size: 2.05rem;
                font-weight: 800;
                line-height: 1;
                margin-bottom: 0.38rem;
                color: var(--text-main);
            }

            .metric-detail {
                font-size: 0.93rem;
                line-height: 1.45;
                color: var(--text-soft);
            }

            .section-label {
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.1rem;
                font-weight: 800;
                color: #8fdcff;
                margin: 0.25rem 0 0.75rem 0.1rem;
            }

            .panel-card {
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(10, 23, 37, 0.92), rgba(13, 28, 44, 0.84));
                border-radius: 20px;
                padding: 1.05rem 1.05rem 0.95rem 1.05rem;
                box-shadow: 0 12px 28px rgba(4, 9, 18, 0.22);
                min-height: 220px;
            }

            .panel-card-tight {
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(10, 23, 37, 0.92), rgba(13, 28, 44, 0.84));
                border-radius: 20px;
                padding: 1.05rem 1.05rem 0.95rem 1.05rem;
                box-shadow: 0 12px 28px rgba(4, 9, 18, 0.22);
            }

            .panel-title {
                font-size: 1.06rem;
                font-weight: 800;
                margin-bottom: 0.3rem;
                color: var(--text-main);
            }

            .panel-copy {
                color: var(--text-soft);
                font-size: 0.93rem;
                line-height: 1.5;
                margin-bottom: 0.8rem;
            }

            .status-chip {
                display: inline-block;
                padding: 0.28rem 0.68rem;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 800;
                color: #f7fbff;
                margin-bottom: 0.8rem;
            }

            .list-line {
                color: var(--text-soft);
                font-size: 0.93rem;
                line-height: 1.45;
                margin-bottom: 0.48rem;
            }

            .insight-card {
                border: 1px solid rgba(123, 180, 255, 0.18);
                background: linear-gradient(180deg, rgba(12, 25, 40, 0.92), rgba(16, 33, 52, 0.86));
                border-radius: 18px;
                padding: 0.9rem 0.95rem;
                min-height: 122px;
                box-shadow: 0 10px 24px rgba(4, 9, 18, 0.20);
            }

            .insight-kicker {
                font-size: 0.76rem;
                font-weight: 800;
                letter-spacing: 0.08rem;
                text-transform: uppercase;
                color: #8fdcff;
                margin-bottom: 0.4rem;
            }

            .insight-line {
                color: var(--text-main);
                font-weight: 700;
                font-size: 0.96rem;
                line-height: 1.42;
                margin-bottom: 0.38rem;
            }

            .insight-sub {
                color: var(--text-soft);
                font-size: 0.88rem;
                line-height: 1.4;
            }

            .nav-line {
                color: var(--text-main);
                font-size: 0.94rem;
                font-weight: 700;
                margin-bottom: 0.52rem;
            }

            .footer-note {
                color: var(--text-faint);
                font-size: 0.88rem;
                margin-top: 0.3rem;
            }

            hr {
                border: none !important;
                height: 1px !important;
                background: linear-gradient(90deg, rgba(130,161,191,0.28), rgba(130,161,191,0.02)) !important;
                margin: 1.15rem 0 0.8rem 0 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title, value, detail, accent):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-accent" style="background:{accent};"></div>
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_module_card(title, status, status_color, summary, detail_lines):
    lines_html = "".join(f'<div class="list-line">{line}</div>' for line in detail_lines)
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="status-chip" style="background:{status_color};">{status}</div>
            <div class="panel-title">{title}</div>
            <div class="panel-copy">{summary}</div>
            {lines_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_card(kicker, main_line, sub_line):
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-kicker">{kicker}</div>
            <div class="insight-line">{main_line}</div>
            <div class="insight-sub">{sub_line}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


inject_styles()

st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-topline">OPEN-SOURCE ORBITAL INTELLIGENCE PLATFORM</div>
        <h1 class="hero-title">Signal Console</h1>
        <p class="hero-copy">
            A monitoring console for orbital launches, satellite activity, and strategic pattern detection.
            Built to turn open-source space signals into a cleaner analyst workspace for tracking launch cadence,
            mission sensitivity, orbital behaviour, and geopolitical movement.
        </p>
        <div class="hero-divider"></div>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown("")
st.markdown('<div class="section-label">Platform Modules</div>', unsafe_allow_html=True)

module_columns = st.columns(3, gap="large")
with module_columns[0]:
    render_module_card(
        "Orbital Launch Monitor",
        "Operational",
        "#38bdf8",
        "Tracks global launch schedules, recent failures, and publicly signaled sensitive missions in one cleaner operational view.",
        [
            "Upcoming launch schedule and launch-site context",
            "Recent failure tracking and disruption visibility",
            "Mission sensitivity notes tied to public metadata and operator context",
        ],
    )
with module_columns[1]:
    render_module_card(
        "Satellite Activity Monitor",
        "Operational",
        "#8b5cf6",
        "Follows satellites, operators, and orbital patterns to help identify notable behaviour, strategic assets, and watchlist movement.",
        [
            "Watchlist-based satellite and operator monitoring",
            "Orbital activity views for notable or strategically relevant assets",
            "Event-ready layer for re-entry, decay, or mission-pattern tracking",
        ],
    )
with module_columns[2]:
    render_module_card(
        "Strategic Insights",
        "Operational",
        "#fbbf24",
        "Converts launch and orbital activity into higher-level signals so the platform feels like an intelligence product, not just a dashboard.",
        [
            "Launch cadence change by country or operator",
            "Mission-type concentration and sensitivity trend detection",
            "Narrative takeaways for geopolitical and space-security context",
        ],
    )





