from folium.plugins import Fullscreen, MousePosition
from streamlit_folium import st_folium

st.set_page_config(page_title="Orbital Launch Monitor", layout="wide")
st.set_page_config(page_title="Orbital Intelligence Watchboard", layout="wide")

UPCOMING_LIMIT = 15
RECENT_LIMIT = 60
        """
        <style>
            :root {
                --bg-0: #07111f;
                --bg-1: #0d1b2a;
                --stroke: rgba(130, 161, 191, 0.22);
                --text-main: #e8f1fb;
                --text-soft: #91a9c3;
                --bg-0: #0c110d;
                --bg-1: #151b16;
                --panel: rgba(20, 27, 22, 0.94);
                --stroke: rgba(146, 162, 130, 0.24);
                --stroke-strong: rgba(182, 197, 154, 0.36);
                --text-main: #e8ede2;
                --text-soft: #a2ad98;
                --text-dim: #7f8d78;
                --intel: #bcc99a;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 28%),
                    radial-gradient(circle at top right, rgba(88, 166, 255, 0.12), transparent 26%),
                    linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 100%);
                    radial-gradient(circle at top left, rgba(188, 201, 154, 0.08), transparent 24%),
                    radial-gradient(circle at top right, rgba(120, 195, 187, 0.05), transparent 22%),
                    linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 52%, #111713 100%);
                color: var(--text-main);
                font-family: "Aptos", "Segoe UI", sans-serif;
                font-family: "Bahnschrift", "Aptos", "Segoe UI", sans-serif;
                position: relative;
            }

            .stApp::before {
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                background:
                    linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
                background-size: 28px 28px;
                mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.28), transparent 88%);
                z-index: 0;
            }

            .block-container {
                padding-top: 1.15rem;
                padding-bottom: 2rem;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(9, 19, 32, 0.97), rgba(9, 19, 32, 0.92));
                background:
                    linear-gradient(180deg, rgba(12, 18, 14, 0.98), rgba(18, 25, 20, 0.96)),
                    linear-gradient(90deg, rgba(188, 201, 154, 0.04), transparent);
                border-right: 1px solid var(--stroke);
            }

                color: var(--text-main);
            }

            [data-testid="stSidebar"] h3 {
                margin-bottom: 0.35rem;
                text-transform: uppercase;
                letter-spacing: 0.18rem;
                font-size: 0.78rem;
                color: var(--intel);
            }

            [data-testid="stSidebar"] button {
                background: linear-gradient(180deg, rgba(30, 40, 31, 0.94), rgba(22, 29, 24, 0.96));
                border: 1px solid var(--stroke-strong);
                border-radius: 12px;
                color: var(--text-main);
                font-weight: 700;
                letter-spacing: 0.06rem;
                text-transform: uppercase;
            }

            [data-testid="stSidebar"] [data-baseweb="input"] input,
            [data-testid="stSidebar"] [data-baseweb="select"] > div,
            [data-testid="stSidebar"] [data-baseweb="tag"] {
                background: rgba(22, 29, 24, 0.98);
                border-color: var(--stroke) !important;
                color: var(--text-main);
            }

            .sidebar-note {
                margin: 0 0 1rem 0;
                padding: 0.8rem 0.9rem;
                border-radius: 14px;
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(25, 33, 27, 0.98), rgba(18, 24, 20, 0.98));
                color: var(--text-soft);
                font-size: 0.9rem;
            }

            .hero-card {
                border: 1px solid var(--stroke);
                background: linear-gradient(145deg, rgba(10, 21, 35, 0.92), rgba(15, 31, 49, 0.86));
                border-radius: 22px;
                padding: 1.35rem 1.5rem;
                box-shadow: 0 18px 40px rgba(4, 9, 18, 0.26);
                margin-bottom: 1rem;
                position: relative;
                overflow: hidden;
                border: 1px solid var(--stroke-strong);
                background:
                    linear-gradient(180deg, rgba(22, 28, 23, 0.96), rgba(17, 23, 19, 0.98)),
                    linear-gradient(90deg, rgba(188, 201, 154, 0.05), transparent 48%);
                border-radius: 18px;
                padding: 1.4rem 1.55rem 1.25rem 1.55rem;
                box-shadow: 0 20px 44px rgba(0, 0, 0, 0.34);
                margin-bottom: 0.95rem;
            }

            .hero-card::after {
                content: "";
                position: absolute;
                top: 0;
                right: 0;
                width: 260px;
                height: 100%;
                background:
                    linear-gradient(135deg, rgba(188, 201, 154, 0.12), transparent 62%),
                    repeating-linear-gradient(
                        180deg,
                        rgba(255, 255, 255, 0.02) 0,
                        rgba(255, 255, 255, 0.02) 1px,
                        transparent 1px,
                        transparent 16px
                    );
                opacity: 0.65;
            }

            .hero-kicker {
                letter-spacing: 0.16rem;
                font-size: 0.72rem;
                position: relative;
                z-index: 1;
                letter-spacing: 0.22rem;
                font-size: 0.74rem;
                font-weight: 700;
                color: #84d7ff;
                margin-bottom: 0.4rem;
                color: var(--intel);
                margin-bottom: 0.45rem;
                text-transform: uppercase;
                font-family: "Consolas", "Aptos Mono", monospace;
            }

            .hero-title {
                font-size: 2.2rem;
                position: relative;
                z-index: 1;
                font-size: 2.35rem;
                line-height: 1.05;
                font-weight: 700;
                margin: 0;
                color: var(--text-main);
                text-transform: uppercase;
                letter-spacing: 0.04rem;
            }

            .hero-copy {
                margin: 0.55rem 0 0 0;
                max-width: 60rem;
                position: relative;
                z-index: 1;
                margin: 0.7rem 0 0 0;
                max-width: 56rem;
                color: var(--text-soft);
                font-size: 0.98rem;
                font-size: 0.99rem;
                line-height: 1.5;
            }

            .hero-meta {
                position: relative;
                z-index: 1;
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
                margin-top: 0.95rem;
            }

            .hero-pill {
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                padding: 0.42rem 0.72rem;
                border-radius: 999px;
                background: rgba(188, 201, 154, 0.08);
                border: 1px solid rgba(188, 201, 154, 0.18);
                color: var(--text-main);
                font-size: 0.8rem;
                font-weight: 700;
            }

            .metric-card {
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(12, 24, 39, 0.9), rgba(14, 32, 50, 0.76));
                border-radius: 20px;
                padding: 1rem 1rem 0.95rem 1rem;
                background: linear-gradient(180deg, rgba(23, 30, 25, 0.94), rgba(17, 23, 19, 0.98));
                border-radius: 16px;
                padding: 0.95rem 1rem;
                min-height: 120px;
                box-shadow: 0 12px 28px rgba(4, 9, 18, 0.24);
                box-shadow: 0 14px 28px rgba(0, 0, 0, 0.22);
            }

            .metric-label {
                font-size: 0.8rem;
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08rem;
                color: var(--text-soft);
                letter-spacing: 0.14rem;
                color: var(--text-dim);
                margin-bottom: 0.45rem;
                font-family: "Consolas", "Aptos Mono", monospace;
            }

            .metric-value {
                font-size: 2rem;
                font-size: 2.05rem;
                font-weight: 700;
                line-height: 1;
                margin-bottom: 0.35rem;
                color: var(--text-main);
                font-family: "Consolas", "Aptos Mono", monospace;
            }

            .metric-detail {
                font-size: 0.92rem;
                font-size: 0.9rem;
                color: var(--text-soft);
                line-height: 1.35;
            }

            .accent-bar {
                width: 54px;
                height: 4px;
                width: 100%;
                height: 3px;
                border-radius: 999px;
                margin-bottom: 0.8rem;
                margin-bottom: 0.78rem;
            }

            .panel-card {
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(10, 23, 37, 0.9), rgba(14, 31, 49, 0.82));
                border-radius: 20px;
                padding: 1rem 1rem 0.8rem 1rem;
                box-shadow: 0 12px 28px rgba(4, 9, 18, 0.22);
                background: linear-gradient(180deg, rgba(24, 31, 26, 0.94), rgba(18, 24, 20, 0.98));
                border-radius: 16px;
                padding: 1rem 1rem 0.9rem 1rem;
                box-shadow: 0 14px 28px rgba(0, 0, 0, 0.2);
            }

            .panel-kicker {
                font-size: 0.72rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.14rem;
                color: var(--intel);
                margin-bottom: 0.32rem;
                font-family: "Consolas", "Aptos Mono", monospace;
            }

            .panel-title {
                font-size: 1rem;
                font-size: 1.02rem;
                font-weight: 700;
                margin-bottom: 0.2rem;
                margin-bottom: 0.22rem;
                color: var(--text-main);
            }

            .panel-copy {
                color: var(--text-soft);
                font-size: 0.92rem;
                margin-bottom: 0.8rem;
                margin-bottom: 0.75rem;
                line-height: 1.45;
            }

            .legend-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.45rem;
            }

            .legend-chip {
                display: inline-flex;
                align-items: center;
                gap: 0.42rem;
                padding: 0.33rem 0.62rem;
                border-radius: 999px;
                border: 1px solid var(--stroke);
                background: rgba(255, 255, 255, 0.02);
                color: var(--text-main);
                font-size: 0.8rem;
                font-weight: 700;
            }

            .legend-dot {
                width: 9px;
                height: 9px;
                border-radius: 999px;
                box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.04);
            }

            .stTabs [data-baseweb="tab-list"] {
            .brief-grid {
                display: grid;
                gap: 0.6rem;
            }

            .brief-row {
                display: grid;
                gap: 0.18rem;
                padding-bottom: 0.55rem;
                border-bottom: 1px solid rgba(146, 162, 130, 0.12);
            }

            .brief-row:last-child {
                border-bottom: none;
                padding-bottom: 0;
            }

            .brief-label {
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 0.12rem;
                color: var(--text-dim);
                font-family: "Consolas", "Aptos Mono", monospace;
            }

            .brief-value {
                color: var(--text-main);
                font-size: 0.92rem;
                line-height: 1.35;
            }

            .status-strip {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 0.8rem;
                margin: 0.35rem 0 1rem 0;
            }

            .status-item {
                border-radius: 14px;
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(24, 31, 26, 0.92), rgba(18, 24, 20, 0.96));
                padding: 0.8rem 0.9rem;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
            }

            .status-key {
                margin-bottom: 0.35rem;
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.12rem;
                color: var(--text-dim);
                font-family: "Consolas", "Aptos Mono", monospace;
            }

            .status-value {
                font-size: 0.96rem;
                color: var(--text-main);
                line-height: 1.35;
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 0.45rem;
                padding: 0.38rem;
                border-radius: 14px;
                border: 1px solid var(--stroke);
                background: rgba(19, 26, 21, 0.88);
            }

            .stTabs [data-baseweb="tab"] {
                border-radius: 999px;
                background: rgba(15, 31, 49, 0.7);
                border-radius: 10px;
                background: rgba(28, 36, 30, 0.88);
                border: 1px solid var(--stroke);
                color: var(--text-main);
                padding-left: 1rem;
                padding-right: 1rem;
                height: 42px;
                text-transform: uppercase;
                letter-spacing: 0.08rem;
                font-size: 0.78rem;
                font-weight: 700;
            }

            .stTabs [aria-selected="true"] {
                background: rgba(188, 201, 154, 0.12);
                border-color: var(--stroke-strong);
            }

            .stDataFrame, div[data-testid="stTable"] {
                border-radius: 18px;
                border-radius: 16px;
                overflow: hidden;
                border: 1px solid var(--stroke);
                background: rgba(18, 24, 20, 0.96);
            }

            div[data-testid="stAlert"] {
                border-radius: 14px;
                border: 1px solid var(--stroke);
                background: rgba(20, 27, 22, 0.94);
            }

            .source-chip {
                display: inline-block;
                padding: 0.25rem 0.55rem;
                padding: 0.28rem 0.58rem;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 700;
                color: #dff4ff;
                background: rgba(56, 189, 248, 0.16);
                border: 1px solid rgba(56, 189, 248, 0.28);
                color: var(--text-main);
                background: rgba(188, 201, 154, 0.08);
                border: 1px solid rgba(188, 201, 154, 0.18);
                margin-right: 0.35rem;
                margin-bottom: 0.35rem;
                text-decoration: none;
            }

            .source-chip:hover {
                border-color: var(--intel);
                color: #f7fbf2;
            }

            .leaflet-popup-content-wrapper,
            .leaflet-popup-tip {
                background: #151b16;
                color: var(--text-main);
                border: 1px solid var(--stroke);
                box-shadow: 0 16px 30px rgba(0, 0, 0, 0.28);
            }

            .leaflet-control-layers,
            .leaflet-control-zoom a,
            .leaflet-bar a,
            .leaflet-control-scale-line {
                background: rgba(18, 24, 20, 0.96) !important;
                color: var(--text-main) !important;
                border-color: var(--stroke) !important;
            }

            .leaflet-control-attribution {
                background: rgba(14, 19, 16, 0.82) !important;
                color: var(--text-soft) !important;
            }

            @media (max-width: 900px) {
                .hero-title {
                    font-size: 1.95rem;
                }

                .status-strip {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
def source_links_html(source_keys):
    links = []
    for source in source_objects(source_keys):
        links.append(f'<a class="source-chip" href="{source["url"]}" target="_blank">{html.escape(source["title"])}</a>')
        links.append(
            f'<a class="source-chip" href="{source["url"]}" target="_blank" rel="noopener noreferrer">'
            f'{html.escape(source["title"])}</a>'
        )
    return "".join(links)


def summarize_selected_providers(providers) -> str:
    if not providers:
        return "All providers"
    if len(providers) <= 2:
        return ", ".join(providers)
    return f"{providers[0]}, {providers[1]} +{len(providers) - 2}"


def build_detail_rows_html(rows) -> str:
    return "".join(
        f"""
        <div class="brief-row">
            <div class="brief-label">{html.escape(label)}</div>
            <div class="brief-value">{html.escape(value)}</div>
        </div>
        """
        for label, value in rows
    )


def looks_sensitive(row: pd.Series) -> bool:
    name = safe_text(row.get("name")).lower()
    mission_type = safe_text(row.get("mission_type")).lower()
        f"""
        <div class="metric-card">
            <div class="accent-bar" style="background:{accent};"></div>
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-detail">{detail}</div>
            <div class="metric-label">{html.escape(title)}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
            <div class="metric-detail">{html.escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_strip(search_query: str, providers, active_layers, marker_count: int, map_theme: str):
    search_value = search_query or "No text filter"
    layer_value = ", ".join(active_layers) if active_layers else "No layers visible"
    st.markdown(
        f"""
        <div class="status-strip">
            <div class="status-item">
                <div class="status-key">Search Scope</div>
                <div class="status-value">{html.escape(search_value)}</div>
            </div>
            <div class="status-item">
                <div class="status-key">Providers</div>
                <div class="status-value">{html.escape(summarize_selected_providers(providers))}</div>
            </div>
            <div class="status-item">
                <div class="status-key">Visible Layers</div>
                <div class="status-value">{html.escape(layer_value)}</div>
            </div>
            <div class="status-item">
                <div class="status-key">Map Picture</div>
                <div class="status-value">{marker_count:,} markers | {html.escape(map_theme)} theme</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_filters(df: pd.DataFrame, search_query: str, providers):
    filtered = df.copy()
    if filtered.empty:

def build_popup_html(row):
    return f"""
        <div style="min-width: 260px; font-family: Segoe UI, sans-serif;">
            <div style="font-size: 15px; font-weight: 700; color: #09111f; margin-bottom: 6px;">
        <div style="min-width: 260px; font-family: Bahnschrift, Segoe UI, sans-serif; color: #e8ede2;">
            <div style="font-size: 10px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: #bcc99a; margin-bottom: 6px;">
                Launch Marker
            </div>
            <div style="font-size: 15px; font-weight: 700; color: #f4f7ef; margin-bottom: 8px;">
                {html.escape(safe_text(row.get('name') or 'Unknown launch'))}
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:12px;">
                <tr><td style="padding:4px 0; color:#5a6d85;">Provider</td><td style="padding:4px 0;">{html.escape(safe_text(row.get('provider') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#5a6d85;">Rocket</td><td style="padding:4px 0;">{html.escape(safe_text(row.get('rocket') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#5a6d85;">Mission</td><td style="padding:4px 0;">{html.escape(safe_text(row.get('mission_type') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#5a6d85;">Time</td><td style="padding:4px 0;">{html.escape(format_time(row.get('net')))}</td></tr>
                <tr><td style="padding:4px 0; color:#5a6d85;">Location</td><td style="padding:4px 0;">{html.escape(safe_text(row.get('location_name') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#5a6d85;">Map layer</td><td style="padding:4px 0;">{html.escape(safe_text(row.get('map_layer') or 'Launch'))}</td></tr>
                <tr><td style="padding:4px 0; color:#8f9d88;">Provider</td><td style="padding:4px 0; color:#e8ede2;">{html.escape(safe_text(row.get('provider') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#8f9d88;">Rocket</td><td style="padding:4px 0; color:#e8ede2;">{html.escape(safe_text(row.get('rocket') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#8f9d88;">Mission</td><td style="padding:4px 0; color:#e8ede2;">{html.escape(safe_text(row.get('mission_type') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#8f9d88;">Time</td><td style="padding:4px 0; color:#e8ede2;">{html.escape(format_time(row.get('net')))}</td></tr>
                <tr><td style="padding:4px 0; color:#8f9d88;">Location</td><td style="padding:4px 0; color:#e8ede2;">{html.escape(safe_text(row.get('location_name') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#8f9d88;">Layer</td><td style="padding:4px 0; color:#e8ede2;">{html.escape(safe_text(row.get('map_layer') or 'Launch'))}</td></tr>
            </table>
        </div>
    """
inject_styles()

st.markdown(
    """
    f"""
    <div class="hero-card">
        <div class="hero-kicker">LIVE ORBITAL OPERATIONS</div>
        <h1 class="hero-title">Orbital Launch Monitor</h1>
        <div class="hero-kicker">Open-Source Orbital Intelligence Picture</div>
        <h1 class="hero-title">Orbital Intelligence Watchboard</h1>
        <p class="hero-copy">
            A professional launch watchboard for upcoming activity, recent failures, publicly signaled sensitive missions,
            and official-document context on why a launch profile may be strategically sensitive.
            A clear analyst workspace for monitoring launch activity, failure watch, and public indicators of strategically
            sensitive missions. The interface is tuned for fast scan, consistent labels, and source-backed context rather
            than decorative dashboard chrome.
        </p>
        <div class="hero-meta">
            <span class="hero-pill">Public launch feeds</span>
            <span class="hero-pill">Official NRO and USSF references</span>
            <span class="hero-pill">{CACHE_TTL_SECONDS // 60}-minute cache window</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Launch Controls")
    st.markdown("### Analyst Controls")
    st.markdown(
        """
        <div class="sidebar-note">
            Refine the open-source launch picture, then focus the map and tables on the missions that matter.
        </div>
        """,
        unsafe_allow_html=True,
    )
    refresh_clicked = st.button("Refresh launch feeds", use_container_width=True)
    if refresh_clicked:
        get_upcoming_launches.clear()
        st.rerun()

    search_query = st.text_input(
        "Search launches",
        placeholder="Launch, provider, rocket, mission, or location",
        "Search picture",
        placeholder="Mission, provider, vehicle, role, or site",
    ).strip()

    provider_filter = st.multiselect(
        default=[],
    )

    st.markdown("### Map Layers")
    st.markdown("### Layer Visibility")
    st.caption("Control which mission categories are shown on the operational map.")
    show_upcoming = st.toggle("Upcoming launches", value=True)
    show_failures = st.toggle("Recent failures", value=True)
    show_sensitive = st.toggle("Sensitive launches", value=True)
    filtered_sensitive_df if show_sensitive else pd.DataFrame(),
)

active_layers = []
if show_upcoming:
    active_layers.append("Upcoming")
if show_failures:
    active_layers.append("Failures")
if show_sensitive:
    active_layers.append("Sensitive")

render_status_strip(search_query, provider_filter, active_layers, len(map_df), map_theme)

metric_columns = st.columns(4)
with metric_columns[0]:
    render_metric_card(
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-kicker">Operational Picture</div>
            <div class="panel-title">Launch Site Map</div>
            <div class="panel-copy">
                Upcoming launches are cyan, recent failures are amber, and sensitive launch profiles are red.
                A geospatial view of the current launch picture. Colors are restrained and consistent so analysts can
                distinguish category first and read details second.
            </div>
            <div class="legend-row">
                <span class="legend-chip"><span class="legend-dot" style="background:{upcoming};"></span>Upcoming</span>
                <span class="legend-chip"><span class="legend-dot" style="background:{failure};"></span>Recent failure</span>
                <span class="legend-chip"><span class="legend-dot" style="background:{sensitive};"></span>Sensitive profile</span>
            </div>
        </div>
        """,
        """.format(
            upcoming=STATUS_COLORS["Upcoming"],
            failure=STATUS_COLORS["Recent failure"],
            sensitive=STATUS_COLORS["Sensitive"],
        ),
        unsafe_allow_html=True,
    )

            st_folium(launch_map, use_container_width=True, height=720)

with side_col:
    st.markdown("#### Next scheduled launch")
    st.markdown("#### Next launch window")
    if filtered_upcoming_df.empty:
        st.info("No upcoming launch matches the current filters.")
    else:
        st.markdown(
            f"""
            <div class="panel-card">
                <div class="panel-kicker">Priority Queue</div>
                <div class="panel-title">{html.escape(safe_text(next_launch.get("name") or "Unknown launch"))}</div>
                <div class="panel-copy">
                    {html.escape(format_time(next_launch.get("net")))}<br>
                    {html.escape(safe_text(next_launch.get("provider") or "Unknown provider"))}<br>
                    {html.escape(safe_text(next_launch.get("rocket") or "Unknown rocket"))}<br>
                    {html.escape(safe_text(next_launch.get("location_name") or "Unknown location"))}
                <div class="brief-grid">
                    {build_detail_rows_html([
                        ("Time (UTC)", format_time(next_launch.get("net"))),
                        ("Provider", safe_text(next_launch.get("provider") or "Unknown provider")),
                        ("Vehicle", safe_text(next_launch.get("rocket") or "Unknown rocket")),
                        ("Location", safe_text(next_launch.get("location_name") or "Unknown location")),
                    ])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("#### Official context basis")
    st.markdown("#### Analytic basis")
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-kicker">Method Note</div>
            <div class="panel-title">Why a launch may be sensitive</div>
            <div class="panel-copy">
                The explanations in this section are tied to official NRO, U.S. Space Force, Space Systems Command,
                and launch-program mission material rather than generic guesswork.
                and launch-program mission material. Flags are based on public metadata and source-backed inference,
                not on classified payload disclosure.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Mission context below is best-effort, but each explanation is backed by official program or mission references linked in the cards.")
    st.caption("Mission context is best-effort, but every explanation is anchored to official program or mission references linked in the cards.")

tab_upcoming, tab_failed, tab_sensitive, tab_context = st.tabs(
    ["Upcoming Launches", "Recent Failures", "Sensitive Missions", "Official Mission Context"]
    ["Launch Queue", "Failure Watch", "Sensitive Profiles", "Official Context"]
)

with tab_upcoming:
    st.markdown("### Upcoming Launches")
    st.markdown("### Launch Queue")
    if launch_error:
        st.warning("The upstream upcoming-launch feed is temporarily unavailable.")
    elif filtered_upcoming_df.empty:
        st.dataframe(display_launch_table(filtered_upcoming_df), use_container_width=True, hide_index=True)

with tab_failed:
    st.markdown("### Recent Failed Launches")
    st.markdown("### Failure Watch")
    if recent_launch_error:
        st.warning("The recent-launch feed is temporarily unavailable.")
    elif filtered_failed_df.empty:
        st.dataframe(display_launch_table(filtered_failed_df), use_container_width=True, hide_index=True)

with tab_sensitive:
    st.markdown("### Publicly Signaled Sensitive Launches")
    st.caption("This table only uses public naming, mission labels, and launch metadata to flag launches that look government, military, or national-security linked.")
    st.markdown("### Sensitive Profiles")
    st.caption("This table uses public mission naming, role labels, and launch metadata to flag profiles that appear government, military, or national-security linked.")
    if recent_launch_error:
        st.warning("Sensitive launch detection depends on the recent-launch feed, which is temporarily unavailable.")
    elif filtered_sensitive_df.empty:
        st.dataframe(display_launch_table(filtered_sensitive_df), use_container_width=True, hide_index=True)

with tab_context:
    st.markdown("### Official Mission Context")
    st.caption("Possible reasons a launch may be sensitive, paired with official mission and program references.")
    st.markdown("### Official Context")
    st.caption("Possible reasons a launch may be sensitive, paired with official mission and program references for fast analyst review.")
    if recent_launch_error:
        st.warning("Mission context is unavailable because the recent-launch feed could not be loaded.")
    elif filtered_sensitive_df.empty:
            st.markdown(
                f"""
                <div class="panel-card">
                    <div class="panel-kicker">Source-Backed Assessment</div>
                    <div class="panel-title">{html.escape(row['Launch'])}</div>
                    <div class="panel-copy">
                        <strong>Likely role:</strong> {html.escape(row['Likely Role'])}<br>

st.markdown("---")
st.caption(
    f"Loaded {len(filtered_upcoming_df):,} upcoming launches, {len(filtered_failed_df):,} recent failures, and "
    f"{len(filtered_sensitive_df):,} sensitive launch profiles under the current filters."
    f"Current picture: {len(filtered_upcoming_df):,} upcoming launches, {len(filtered_failed_df):,} recent failures, "
    f"and {len(filtered_sensitive_df):,} sensitive profiles under the active filters."
)
