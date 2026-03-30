mport html
from datetime import datetime, timezone

import streamlit as st


st.set_page_config(page_title="Signal Console", layout="wide")


PAGE_TARGETS = {
    "launch": "pages/Launch_Intelligence.py",
    "satellite": "pages/Satellite_Watch.py",
    "strategic": "pages/Strategic_Insights.py",
}

STATUS_CARDS = [
    {
        "label": "Platform status",
        "value": "ONLINE",
        "detail": "Core workspace, watchlists, and routing are healthy.",
        "accent": "#39d98a",
    },
    {
        "label": "Launch monitor",
        "value": "LIVE",
        "detail": "Upcoming windows and sensitive mission screening are active.",
        "accent": "#38bdf8",
    },
    {
        "label": "Satellite monitor",
        "value": "LIVE",
        "detail": "Regional orbital sweeps and pass tracking are ready.",
        "accent": "#58a6ff",
    },
    {
        "label": "Strategic insights",
        "value": "WATCH",
        "detail": "Analyst narratives and notable-event scoring are current.",
        "accent": "#f2cc60",
    },
]

PREVIEW_CARDS = [
    {
        "title": "Launch Activity Preview",
        "chip": "Launches",
        "accent": "#38bdf8",
        "lines": [
            "Near-term launch tempo is building across commercial and state operators.",
            "One national-security mission profile remains elevated for analyst review.",
        ],
        "action": "Open launch intelligence ->",
        "target": PAGE_TARGETS["launch"],
    },
    {
        "title": "Satellite Activity Preview",
        "chip": "Satellites",
        "accent": "#58a6ff",
        "lines": [
            "LEO traffic density remains strongest over Europe and North America in the current sweep.",
            "Military catalogue passes are still the highest-priority watch class.",
        ],
        "action": "Open satellite watch ->",
        "target": PAGE_TARGETS["satellite"],
    },
    {
        "title": "Strategic Insight Preview",
        "chip": "Insights",
        "accent": "#f2cc60",
        "lines": [
            "Recent event logging clusters around surveillance posture and resilient PNT themes.",
            "Analyst attention is centered on selective signaling rather than broad instability.",
        ],
        "action": "Open strategic insights ->",
        "target": PAGE_TARGETS["strategic"],
    },
]

MODULE_CARDS = [
    {
        "title": "Launch Intelligence",
        "summary": "Track launch cadence, sensitive missions, and operational disruptions from one clean watchboard.",
        "bullets": [
            "Upcoming launch windows and site mapping",
            "Recent failures, delays, and anomaly review",
            "Sensitive mission screening with official context",
        ],
        "accent": "#38bdf8",
        "action": "Enter launch intelligence",
        "target": PAGE_TARGETS["launch"],
    },
    {
        "title": "Satellite Watch",
        "summary": "Monitor regional orbital activity, category-specific passes, and platform movement across regimes.",
        "bullets": [
            "Regional sweeps for active satellites",
            "Orbit regime, category, and pass filters",
            "Map-based tracking for high-interest objects",
        ],
        "accent": "#58a6ff",
        "action": "Enter satellite watch",
        "target": PAGE_TARGETS["satellite"],
    },
    {
        "title": "Strategic Insights",
        "summary": "Move from raw signals to narrative understanding with country trends, event filters, and analyst framing.",
        "bullets": [
            "Country-level trend comparisons",
            "Sensitive-event filters and summary scoring",
            "Narrative insights for rapid analyst orientation",
        ],
        "accent": "#f2cc60",
        "action": "Enter strategic insights",
        "target": PAGE_TARGETS["strategic"],
    },
]


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg-0: #060b12;
                --bg-1: #0a121c;
                --bg-2: #101a27;
                --panel-0: rgba(10, 18, 28, 0.88);
                --panel-1: rgba(15, 26, 39, 0.92);
                --panel-2: rgba(18, 32, 48, 0.96);
                --stroke: rgba(116, 144, 171, 0.20);
                --stroke-strong: rgba(129, 164, 199, 0.34);
                --text-main: #f4f7fb;
                --text-soft: #95a8be;
                --text-dim: #71859a;
                --green: #39d98a;
                --blue: #38bdf8;
                --blue-2: #58a6ff;
                --amber: #f2cc60;
                --red: #ff6b6b;
                --shadow: rgba(2, 8, 18, 0.46);
            }

            html, body, [class*="css"]  {
                font-family: "Aptos", "Segoe UI Variable", "Segoe UI", sans-serif;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(56, 189, 248, 0.12), transparent 24%),
                    radial-gradient(circle at 85% 10%, rgba(88, 166, 255, 0.10), transparent 20%),
                    radial-gradient(circle at 50% 0%, rgba(57, 217, 138, 0.05), transparent 28%),
                    linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 45%, #0d1723 100%);
                color: var(--text-main);
            }

            .stApp::before {
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                background-image:
                    linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
                background-size: 120px 120px;
                mask-image: linear-gradient(180deg, rgba(0,0,0,0.34), transparent 78%);
                opacity: 0.22;
            }

            [data-testid="stHeader"] {
                background: transparent;
            }

            .block-container {
                max-width: 1340px;
                padding-top: 1.2rem;
                padding-bottom: 3rem;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(8, 14, 24, 0.98), rgba(10, 18, 28, 0.94));
                border-right: 1px solid var(--stroke);
            }

            [data-testid="stSidebar"] * {
                color: var(--text-main);
            }

            .hero-card,
            .hero-side-card,
            .status-card,
            .preview-card,
            .module-card,
            .purpose-card {
                border: 1px solid var(--stroke);
                box-shadow: 0 24px 46px var(--shadow);
            }

            .hero-card,
            .hero-side-card {
                min-height: 100%;
                border-radius: 24px;
                background:
                    linear-gradient(150deg, rgba(15, 27, 41, 0.98), rgba(8, 16, 25, 0.96)),
                    linear-gradient(180deg, var(--panel-0), var(--panel-1));
            }

            .hero-card {
                padding: 1.65rem 1.7rem;
                position: relative;
                overflow: hidden;
            }

            .hero-card::after {
                content: "";
                position: absolute;
                width: 220px;
                height: 220px;
                right: -48px;
                top: -72px;
                background: radial-gradient(circle, rgba(56, 189, 248, 0.22), transparent 68%);
                pointer-events: none;
            }

            .hero-side-card {
                padding: 1.2rem 1.25rem;
            }

            .eyebrow {
                font-family: "Consolas", "Aptos Mono", monospace;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.18rem;
                text-transform: uppercase;
                color: #7ed6ff;
                margin-bottom: 0.7rem;
            }

            .hero-title {
                font-family: "Bahnschrift", "Aptos Display", "Segoe UI Variable", sans-serif;
                font-size: 3rem;
                line-height: 0.96;
                font-weight: 700;
                margin: 0;
                color: var(--text-main);
                max-width: 10ch;
            }

            .hero-descriptor {
                margin-top: 0.8rem;
                font-size: 1.02rem;
                color: #dbe9f7;
                font-weight: 600;
                letter-spacing: 0.01rem;
            }

            .hero-copy {
                margin: 0.75rem 0 1rem 0;
                max-width: 58rem;
                font-size: 0.98rem;
                line-height: 1.6;
                color: var(--text-soft);
            }

            .tag-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
                margin-top: 1rem;
            }

            .tag-chip {
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                padding: 0.45rem 0.72rem;
                border-radius: 999px;
                border: 1px solid rgba(126, 214, 255, 0.16);
                background: rgba(10, 23, 36, 0.74);
                color: #d7e9f7;
                font-size: 0.82rem;
                font-weight: 600;
            }

            .tag-dot {
                width: 8px;
                height: 8px;
                border-radius: 999px;
                background: currentColor;
                box-shadow: 0 0 16px currentColor;
            }

            .side-title {
                font-size: 0.95rem;
                font-weight: 700;
                color: var(--text-main);
                margin-bottom: 0.2rem;
            }

            .side-copy {
                font-size: 0.88rem;
                line-height: 1.5;
                color: var(--text-soft);
                margin-bottom: 1rem;
            }

            .side-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                padding: 0.72rem 0;
                border-top: 1px solid rgba(129, 164, 199, 0.12);
            }

            .side-row:first-of-type {
                border-top: 0;
                padding-top: 0.15rem;
            }

            .side-label {
                font-family: "Consolas", "Aptos Mono", monospace;
                font-size: 0.76rem;
                letter-spacing: 0.08rem;
                text-transform: uppercase;
                color: var(--text-dim);
            }

            .side-value {
                font-size: 0.88rem;
                font-weight: 700;
                color: var(--text-main);
                text-align: right;
            }

            .section-head {
                margin: 1.55rem 0 0.95rem 0;
            }

            .section-label {
                font-family: "Consolas", "Aptos Mono", monospace;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.18rem;
                text-transform: uppercase;
                color: #87d8ff;
                margin-bottom: 0.35rem;
            }

            .section-title {
                font-family: "Bahnschrift", "Aptos Display", "Segoe UI Variable", sans-serif;
                font-size: 1.45rem;
                font-weight: 700;
                color: var(--text-main);
                margin: 0;
            }

            .section-copy {
                margin-top: 0.35rem;
                font-size: 0.93rem;
                line-height: 1.55;
                color: var(--text-soft);
                max-width: 56rem;
            }

            .status-card {
                border-radius: 18px;
                background: linear-gradient(180deg, rgba(13, 24, 36, 0.96), rgba(11, 20, 30, 0.92));
                padding: 1rem 1rem 0.95rem 1rem;
                min-height: 150px;
            }

            .status-topline {
                display: flex;
                align-items: center;
                gap: 0.55rem;
                margin-bottom: 0.85rem;
            }

            .status-dot {
                width: 10px;
                height: 10px;
                border-radius: 999px;
                box-shadow: 0 0 18px currentColor;
                flex: 0 0 auto;
            }

            .status-label {
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.1rem;
                color: var(--text-dim);
                font-weight: 700;
            }

            .status-value {
                font-family: "Bahnschrift", "Aptos Display", sans-serif;
                font-size: 1.75rem;
                font-weight: 700;
                line-height: 1;
                margin-bottom: 0.45rem;
                color: var(--text-main);
            }

            .status-detail {
                font-size: 0.92rem;
                line-height: 1.52;
                color: var(--text-soft);
            }

            .preview-card,
            .module-card,
            .purpose-card {
                background: linear-gradient(180deg, rgba(12, 22, 33, 0.96), rgba(11, 18, 28, 0.94));
            }

            .preview-card {
                border-radius: 20px;
                padding: 1rem 1rem 0.95rem 1rem;
                min-height: 228px;
                margin-bottom: 0.55rem;
            }

            .module-card {
                border-radius: 22px;
                padding: 1.15rem 1.15rem 1rem 1.15rem;
                min-height: 282px;
                margin-bottom: 0.55rem;
            }

            .purpose-card {
                border-radius: 22px;
                padding: 1.2rem 1.25rem;
            }

            .chip {
                display: inline-flex;
                align-items: center;
                padding: 0.28rem 0.62rem;
                border-radius: 999px;
                font-size: 0.74rem;
                font-weight: 700;
                letter-spacing: 0.06rem;
                text-transform: uppercase;
                color: #f7fbff;
                margin-bottom: 0.85rem;
            }

            .card-title {
                font-size: 1.02rem;
                font-weight: 700;
                color: var(--text-main);
                margin-bottom: 0.55rem;
            }

            .card-line {
                font-size: 0.92rem;
                line-height: 1.52;
                color: var(--text-soft);
                margin-bottom: 0.55rem;
            }

            .module-topline {
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 1rem;
                margin-bottom: 0.7rem;
            }

            .module-name {
                font-size: 1.08rem;
                font-weight: 700;
                color: var(--text-main);
            }

            .module-code {
                font-family: "Consolas", "Aptos Mono", monospace;
                font-size: 0.76rem;
                letter-spacing: 0.08rem;
                color: var(--text-dim);
                text-transform: uppercase;
            }

            .module-summary {
                font-size: 0.93rem;
                line-height: 1.58;
                color: var(--text-soft);
                margin-bottom: 0.9rem;
            }

            .module-item {
                position: relative;
                padding-left: 1rem;
                margin-bottom: 0.55rem;
                font-size: 0.9rem;
                line-height: 1.48;
                color: #dbe5ef;
            }

            .module-item::before {
                content: "";
                position: absolute;
                left: 0;
                top: 0.48rem;
                width: 6px;
                height: 6px;
                border-radius: 999px;
                background: currentColor;
                box-shadow: 0 0 12px currentColor;
            }

            .purpose-title {
                font-size: 1rem;
                font-weight: 700;
                color: var(--text-main);
                margin-bottom: 0.35rem;
            }

            .purpose-copy {
                font-size: 0.94rem;
                line-height: 1.6;
                color: var(--text-soft);
                max-width: 64rem;
                margin: 0;
            }

            div[data-testid="stPageLink"],
            div[data-testid="stButton"] {
                width: 100%;
            }

            div[data-testid="stPageLink"] a,
            a[data-testid="stPageLink-NavLink"],
            div[data-testid="stButton"] > button {
                width: 100%;
                min-height: 2.9rem;
                border-radius: 14px;
                border: 1px solid var(--stroke-strong);
                background: linear-gradient(180deg, rgba(18, 33, 49, 0.94), rgba(10, 20, 30, 0.98));
                color: var(--text-main);
                box-shadow: 0 14px 30px rgba(0, 0, 0, 0.22);
                text-decoration: none;
                transition: border-color 160ms ease, transform 160ms ease, background 160ms ease;
            }

            div[data-testid="stPageLink"] a:hover,
            a[data-testid="stPageLink-NavLink"]:hover,
            div[data-testid="stButton"] > button:hover {
                border-color: rgba(126, 214, 255, 0.48);
                background: linear-gradient(180deg, rgba(20, 38, 58, 0.98), rgba(12, 23, 34, 0.99));
                color: #ffffff;
                transform: translateY(-1px);
            }

            div[data-testid="stPageLink"] a p,
            a[data-testid="stPageLink-NavLink"] p,
            div[data-testid="stButton"] > button p {
                color: inherit;
                font-weight: 700;
                letter-spacing: 0.01rem;
            }

            @media (max-width: 980px) {
                .hero-title {
                    font-size: 2.45rem;
                }

                .preview-card,
                .module-card,
                .status-card {
                    min-height: 0;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_section_head(label: str, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-head">
            <div class="section-label">{html.escape(label)}</div>
            <h2 class="section-title">{html.escape(title)}</h2>
            <div class="section-copy">{html.escape(copy)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_card(label: str, value: str, detail: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-topline">
                <span class="status-dot" style="color:{accent}; background:{accent};"></span>
                <span class="status-label">{html.escape(label)}</span>
            </div>
            <div class="status-value">{html.escape(value)}</div>
            <div class="status-detail">{html.escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_preview_card(title: str, chip: str, accent: str, lines: list[str]) -> None:
    lines_html = "".join(f'<div class="card-line">{html.escape(line)}</div>' for line in lines)
    st.markdown(
        f"""
        <div class="preview-card">
            <div class="chip" style="background:{accent};">{html.escape(chip)}</div>
            <div class="card-title">{html.escape(title)}</div>
            {lines_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_module_card(title: str, summary: str, bullets: list[str], accent: str, code: str) -> None:
    bullet_html = "".join(
        f'<div class="module-item" style="color:{accent};"><span style="color:#dbe5ef;">{html.escape(bullet)}</span></div>'
        for bullet in bullets
    )
    st.markdown(
        f"""
        <div class="module-card">
            <div class="module-topline">
                <div class="module-name">{html.escape(title)}</div>
                <div class="module-code">{html.escape(code)}</div>
            </div>
            <div class="module-summary">{html.escape(summary)}</div>
            {bullet_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_action(label: str, target: str, key: str) -> None:
    if hasattr(st, "page_link"):
        st.page_link(target, label=label)
        return

    if st.button(label, key=key, use_container_width=True):
        if hasattr(st, "switch_page"):
            st.switch_page(target)
        else:
            st.session_state["signal_console_nav_fallback"] = True


inject_styles()

as_of_text = datetime.now(timezone.utc).strftime("%d %b %Y | %H:%M UTC")

hero_left, hero_right = st.columns([1.85, 1], gap="large")

with hero_left:
    st.markdown(
        """
        <div class="hero-card">
            <div class="eyebrow">Orbital Intelligence Workspace</div>
            <h1 class="hero-title">Signal Console</h1>
            <div class="hero-descriptor">Open-source orbital intelligence platform</div>
            <p class="hero-copy">
                Monitor launches, satellite activity, and strategic orbital patterns from one command workspace built for
                fast analyst orientation and deliberate module handoff.
            </p>
            <div class="tag-row">
                <span class="tag-chip" style="color:#39d98a;"><span class="tag-dot"></span>Platform online</span>
                <span class="tag-chip" style="color:#38bdf8;"><span class="tag-dot"></span>Launches</span>
                <span class="tag-chip" style="color:#58a6ff;"><span class="tag-dot"></span>Satellites</span>
                <span class="tag-chip" style="color:#f2cc60;"><span class="tag-dot"></span>Strategic insights</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with hero_right:
    st.markdown(
        f"""
        <div class="hero-side-card">
            <div class="eyebrow">Console Brief</div>
            <div class="side-title">Front-door view for the orbital stack</div>
            <div class="side-copy">Small, live-feeling previews point analysts into the right deeper workspace without turning the homepage into a dashboard.</div>
            <div class="side-row">
                <div class="side-label">Scope</div>
                <div class="side-value">Orbital only</div>
            </div>
            <div class="side-row">
                <div class="side-label">Modules</div>
                <div class="side-value">3 active pages</div>
            </div>
            <div class="side-row">
                <div class="side-label">Refresh</div>
                <div class="side-value">Preview cadence enabled</div>
            </div>
            <div class="side-row">
                <div class="side-label">As of</div>
                <div class="side-value">{html.escape(as_of_text)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.session_state.get("signal_console_nav_fallback"):
    st.info("Direct page routing is not available in this Streamlit runtime. Use the sidebar to open each module.")

render_section_head(
    "Overview",
    "Operational status at a glance",
    "A quick health read for the platform and the three primary orbital modules.",
)

status_columns = st.columns(4, gap="medium")
for column, card in zip(status_columns, STATUS_CARDS):
    with column:
        render_status_card(card["label"], card["value"], card["detail"], card["accent"])

render_section_head(
    "Live Preview",
    "Small signals before you go deeper",
    "These cards suggest where activity is building and give a fast path into the detailed pages.",
)

preview_columns = st.columns(3, gap="large")
for index, (column, card) in enumerate(zip(preview_columns, PREVIEW_CARDS), start=1):
    with column:
        render_preview_card(card["title"], card["chip"], card["accent"], card["lines"])
        render_page_action(card["action"], card["target"], f"preview_action_{index}")

render_section_head(
    "Modules",
    "Choose the workspace you need next",
    "Navigation-first cards route into the deeper modules with just enough context to guide the next click.",
)

module_columns = st.columns(3, gap="large")
for index, (column, card) in enumerate(zip(module_columns, MODULE_CARDS), start=1):
    with column:
        render_module_card(card["title"], card["summary"], card["bullets"], card["accent"], f"/0{index}")
        render_page_action(card["action"], card["target"], f"module_action_{index}")

st.markdown(
    """
    <div style="height: 1.15rem;"></div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="purpose-card">
        <div class="section-label" style="margin-bottom:0.5rem;">Platform purpose</div>
        <div class="purpose-title">One command home screen for orbital intelligence</div>
        <p class="purpose-copy">
            Signal Console consolidates open-source launch monitoring, satellite watch, and strategic interpretation into
            a single operational front door so analysts can orient fast, spot what matters, and enter the right module
            with minimal friction.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
