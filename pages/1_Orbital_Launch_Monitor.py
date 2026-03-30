import html
import time

import folium
import pandas as pd
import requests
import streamlit as st
from folium.features import DivIcon
from folium.plugins import Fullscreen, MousePosition
from streamlit_folium import st_folium

st.set_page_config(page_title="Orbital Launch Monitor", layout="wide")

UPCOMING_LIMIT = 15
RECENT_LIMIT = 60
REQUEST_TIMEOUT = 45
REQUEST_RETRIES = 3
CACHE_TTL_SECONDS = 300

MAP_THEMES = {
    "Light": {
        "tiles": "CartoDB positron",
        "attr": None,
    },
    "Radar": {
        "tiles": "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        "attr": "&copy; OpenStreetMap contributors &copy; CARTO",
    },
    "Dark": {
        "tiles": "CartoDB dark_matter",
        "attr": None,
    },
}

STATUS_COLORS = {
    "Upcoming": "#72b7b0",
    "Recent failure": "#d9a24b",
    "Sensitive": "#d36b5f",
}

OFFICIAL_SOURCES = {
    "nro_launch": {
        "title": "NRO launch overview",
        "url": "https://www.nro.gov/Launch/",
        "summary": "NRO says its satellites support intelligence, global coverage, research, and disaster relief, and that it selects the launch vehicle needed to reach the intended orbit.",
    },
    "nrol_101": {
        "title": "NRO NROL-101 official launch page",
        "url": "https://www.nro.gov/Launches/launch-nrol-101/",
        "summary": "NRO says NROL-101 carried a national security payload supporting the agency's overhead reconnaissance mission and providing intelligence to policymakers, the Intelligence Community, and DoD.",
    },
    "nrol_82": {
        "title": "NRO NROL-82 official launch page",
        "url": "https://www.nro.gov/Launches/launch-nrol-82/",
        "summary": "NRO says NROL-82 carried a national security payload that supports the agency's intelligence mission and used the heavy-lift Delta IV Heavy.",
    },
    "nrol_151": {
        "title": "NRO NROL-151 official launch page",
        "url": "https://www.nro.gov/Launches/launch-nrol-151/",
        "summary": "NRO says Electron provides dedicated access to orbit for small satellites and describes Rocket Lab's U.S. pad as tailored for government small-satellite missions.",
    },
    "nrol_87": {
        "title": "NRO NROL-87 official launch page",
        "url": "https://www.nro.gov/Launches/launch-nrol-87/",
        "summary": "NRO says NROL-87 flew as a National Security Space Launch aboard Falcon 9 and carried a national security payload operated by the agency.",
    },
    "gps": {
        "title": "U.S. Space Force GPS fact sheet",
        "url": "https://www.spaceforce.mil/About-Us/Fact-Sheets/Article/2197765/global-positioning-system/",
        "summary": "The Space Force says GPS provides global positioning, navigation, and timing data and is used by military users, ships, aircraft, land vehicles, and precision-guided munitions.",
    },
    "milcom_pnt": {
        "title": "SSC Military Communications and PNT office",
        "url": "https://www.ssc.spaceforce.mil/Program-Offices/Military-Communications-and-Positioning",
        "summary": "Space Systems Command says MILCOM and PNT delivers military SATCOM, protected command-and-control links, and more secure, jam-resistant GPS capabilities.",
    },
    "vulcan_nssl": {
        "title": "SSC Vulcan NSSL certification release",
        "url": "https://www.ssc.spaceforce.mil/Newsroom/Article/4136016/u-s-space-force-ussf-certifies-united-launch-alliance-ula-vulcan-for-national-s",
        "summary": "SSC says National Security Space Launch certification exists to deliver the nation's most critical space-based systems with launch capacity, resiliency, and flexibility.",
    },
    "missile_tracking": {
        "title": "SSC missile warning and tracking launch award release",
        "url": "https://www.ssc.spaceforce.mil/Newsroom/Article/4374896/space-systems-command-awards-task-orders-to-launch-missile-warning-and-missile",
        "summary": "SSC says NSSL task orders support missile warning and missile tracking payloads, including tracking-layer and missile-defense space vehicles.",
    },
    "ussf_87": {
        "title": "SSC USSF-87 mission preparation release",
        "url": "https://www.ssc.spaceforce.mil/Newsroom/Article/4403552/space-systems-command-mission-partners-prepares-ussf-87-for-national-space-secu",
        "summary": "SSC says the USSF-87 primary payload, GSSAP, supports U.S. Space Command space surveillance operations in near-geosynchronous orbit.",
    },
    "space_capabilities": {
        "title": "U.S. Space Force space capabilities overview",
        "url": "https://www.spaceforce.mil/About-Us/About-Space-Force/Space-Capabilities/",
        "summary": "The Space Force says national space capabilities include secure communications, navigation, threat warning, surveillance, and launch support for military operations.",
    },
}

SENSITIVE_KEYWORDS = [
    "government",
    "national security",
    "military",
    "reconnaissance",
    "surveillance",
    "classified",
    "nrol",
    "nro",
    "ussf-",
    "gps",
    "wgs",
    "gssap",
    "missile warning",
    "missile tracking",
    "tracking layer",
    "satcom",
]

WATCHED_PROVIDERS = [
    "united launch alliance",
    "spacex",
    "rocket lab",
    "northrop grumman",
]


def inject_styles():
    st.markdown(
        """
        <style>
            :root {
                --bg-0: #0f1314;
                --bg-1: #14191b;
                --panel: #1a2022;
                --panel-2: #20282b;
                --sidebar: #121718;
                --stroke: #2c3538;
                --stroke-strong: #445156;
                --text-main: #edf1ee;
                --text-soft: #b7c0bb;
                --text-dim: #87928c;
                --intel: #a8b28b;
                --shadow: rgba(0, 0, 0, 0.24);
            }

            .stApp {
                background: linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 44%, #101516 100%);
                color: var(--text-main);
                font-family: "Segoe UI", "Aptos", sans-serif;
            }

            .block-container {
                padding-top: 1rem;
                padding-bottom: 2rem;
            }

            [data-testid="stSidebar"] {
                background: var(--sidebar);
                border-right: 1px solid var(--stroke);
            }

            [data-testid="stSidebar"] * {
                color: var(--text-main);
            }

            [data-testid="stSidebar"] h3 {
                margin-bottom: 0.35rem;
                text-transform: uppercase;
                letter-spacing: 0.14rem;
                font-size: 0.76rem;
                color: var(--intel);
                font-weight: 700;
            }

            [data-testid="stSidebar"] button {
                background: var(--panel-2);
                border: 1px solid var(--stroke-strong);
                border-radius: 10px;
                color: var(--text-main);
                font-weight: 700;
            }

            [data-testid="stSidebar"] button:hover {
                border-color: var(--intel);
            }

            [data-testid="stSidebar"] [data-baseweb="input"] input,
            [data-testid="stSidebar"] [data-baseweb="select"] > div,
            [data-testid="stSidebar"] [data-baseweb="tag"] {
                background: var(--panel);
                border-color: var(--stroke) !important;
                color: var(--text-main);
            }

            .sidebar-note {
                margin: 0 0 1rem 0;
                padding: 0.8rem 0.9rem;
                border-radius: 10px;
                border: 1px solid var(--stroke);
                background: var(--panel);
                color: var(--text-soft);
                font-size: 0.9rem;
                line-height: 1.45;
            }

            .hero-card {
                border: 1px solid var(--stroke);
                border-left: 4px solid var(--intel);
                background: var(--panel);
                border-radius: 12px;
                padding: 1.1rem 1.2rem;
                box-shadow: 0 14px 30px var(--shadow);
                margin-bottom: 1rem;
            }

            .hero-kicker {
                letter-spacing: 0.14rem;
                font-size: 0.72rem;
                font-weight: 700;
                color: var(--intel);
                margin-bottom: 0.3rem;
                text-transform: uppercase;
                font-family: "Consolas", "Aptos Mono", monospace;
            }

            .hero-title {
                font-size: 2rem;
                line-height: 1.08;
                font-weight: 700;
                margin: 0;
                color: var(--text-main);
            }

            .hero-copy {
                margin: 0.55rem 0 0 0;
                max-width: 62rem;
                color: var(--text-soft);
                font-size: 0.97rem;
                line-height: 1.48;
            }

            .hero-meta {
                margin-top: 0.8rem;
                color: var(--text-dim);
                font-size: 0.84rem;
            }

            .hero-meta strong {
                color: var(--text-main);
                font-weight: 600;
            }

            .metric-card {
                border: 1px solid var(--stroke);
                background: var(--panel);
                border-radius: 12px;
                padding: 0.9rem 0.95rem;
                min-height: 112px;
                box-shadow: 0 12px 24px rgba(0, 0, 0, 0.16);
            }

            .metric-label {
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.1rem;
                color: var(--text-dim);
                margin-bottom: 0.4rem;
                font-family: "Consolas", "Aptos Mono", monospace;
            }

            .metric-value {
                font-size: 1.9rem;
                font-weight: 700;
                line-height: 1;
                margin-bottom: 0.3rem;
                color: var(--text-main);
                font-family: "Segoe UI", "Aptos", sans-serif;
            }

            .metric-detail {
                font-size: 0.88rem;
                color: var(--text-soft);
                line-height: 1.35;
            }

            .accent-bar {
                width: 42px;
                height: 4px;
                border-radius: 999px;
                margin-bottom: 0.7rem;
            }

            .panel-card {
                border: 1px solid var(--stroke);
                background: var(--panel);
                border-radius: 12px;
                padding: 1rem 1rem 0.9rem 1rem;
                box-shadow: 0 12px 24px rgba(0, 0, 0, 0.16);
            }

            .panel-kicker {
                font-size: 0.72rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.1rem;
                color: var(--intel);
                margin-bottom: 0.32rem;
                font-family: "Consolas", "Aptos Mono", monospace;
            }

            .panel-title {
                font-size: 1rem;
                font-weight: 700;
                margin-bottom: 0.22rem;
                color: var(--text-main);
            }

            .panel-copy {
                color: var(--text-soft);
                font-size: 0.92rem;
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
                padding: 0.3rem 0.6rem;
                border-radius: 999px;
                border: 1px solid var(--stroke);
                background: var(--panel-2);
                color: var(--text-main);
                font-size: 0.8rem;
                font-weight: 600;
            }

            .legend-dot {
                width: 9px;
                height: 9px;
                border-radius: 999px;
                box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.04);
            }

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
                gap: 0.75rem;
                margin: 0.2rem 0 1rem 0;
            }

            .status-item {
                border-radius: 10px;
                border: 1px solid var(--stroke);
                background: var(--panel);
                padding: 0.78rem 0.88rem;
            }

            .status-key {
                margin-bottom: 0.35rem;
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.1rem;
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
                border-radius: 12px;
                border: 1px solid var(--stroke);
                background: var(--panel);
            }

            .stTabs [data-baseweb="tab"] {
                border-radius: 10px;
                background: transparent;
                border: 1px solid var(--stroke);
                color: var(--text-main);
                padding-left: 1rem;
                padding-right: 1rem;
                height: 42px;
                letter-spacing: 0.02rem;
                font-size: 0.84rem;
                font-weight: 600;
            }

            .stTabs [aria-selected="true"] {
                background: var(--panel-2);
                border-color: var(--stroke-strong);
            }

            .stDataFrame, div[data-testid="stTable"] {
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid var(--stroke);
                background: var(--panel);
            }

            div[data-testid="stAlert"] {
                border-radius: 10px;
                border: 1px solid var(--stroke);
                background: var(--panel);
            }

            .source-chip {
                display: inline-block;
                padding: 0.28rem 0.56rem;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 600;
                color: var(--text-main);
                background: var(--panel-2);
                border: 1px solid var(--stroke);
                margin-right: 0.35rem;
                margin-bottom: 0.35rem;
                text-decoration: none;
            }

            .source-chip:hover {
                border-color: var(--stroke-strong);
                color: var(--text-main);
            }

            .leaflet-popup-content-wrapper,
            .leaflet-popup-tip {
                background: var(--panel);
                color: var(--text-main);
                border: 1px solid var(--stroke);
                box-shadow: 0 16px 30px rgba(0, 0, 0, 0.2);
            }

            .leaflet-control-layers,
            .leaflet-control-zoom a,
            .leaflet-bar a,
            .leaflet-control-scale-line {
                background: var(--panel) !important;
                color: var(--text-main) !important;
                border-color: var(--stroke) !important;
            }

            .leaflet-control-attribution {
                background: rgba(15, 19, 20, 0.88) !important;
                color: var(--text-soft) !important;
            }

            @media (max-width: 900px) {
                .hero-title {
                    font-size: 1.7rem;
                }

                .status-strip {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_text(value):
    return "" if value is None else str(value).strip()


def clean_time_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if not df.empty and col in df.columns:
        df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    return df


def format_time(value):
    if pd.isna(value):
        return "Unknown"
    return pd.to_datetime(value, utc=True).strftime("%Y-%m-%d %H:%M UTC")


def fetch_json_with_retry(url: str, timeout: int = REQUEST_TIMEOUT, retries: int = REQUEST_RETRIES):
    last_error = None
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            last_error = error
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise last_error


def build_launch_rows(raw_results) -> pd.DataFrame:
    rows = []
    for item in raw_results:
        pad = item.get("pad") or {}
        location = pad.get("location") or {}
        mission = item.get("mission") or {}
        rocket = item.get("rocket") or {}
        configuration = rocket.get("configuration") or {}
        provider = item.get("launch_service_provider") or {}
        status = item.get("status") or {}

        rows.append(
            {
                "name": item.get("name"),
                "net": item.get("net"),
                "status": status.get("name"),
                "provider": provider.get("name"),
                "rocket": configuration.get("name"),
                "mission_type": mission.get("type"),
                "mission_description": mission.get("description"),
                "location_name": location.get("name"),
                "pad_name": pad.get("name"),
                "country_code": location.get("country_code"),
                "lat": pd.to_numeric(pad.get("latitude"), errors="coerce"),
                "lon": pd.to_numeric(pad.get("longitude"), errors="coerce"),
            }
        )
    return pd.DataFrame(rows)


def add_source(source_keys, key):
    if key not in source_keys:
        source_keys.append(key)


def source_objects(source_keys):
    return [OFFICIAL_SOURCES[key] for key in source_keys if key in OFFICIAL_SOURCES]


def source_links_html(source_keys):
    links = []
    for source in source_objects(source_keys):
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
    mission_description = safe_text(row.get("mission_description")).lower()
    provider = safe_text(row.get("provider")).lower()
    rocket = safe_text(row.get("rocket")).lower()

    text = " ".join([name, mission_type, mission_description, provider, rocket])
    if any(keyword in text for keyword in SENSITIVE_KEYWORDS):
        return True

    if any(provider_name in provider for provider_name in WATCHED_PROVIDERS):
        watched_pattern = (
            "government",
            "military",
            "national security",
            "reconnaissance",
            "surveillance",
            "classified",
            "nrol",
            "nro",
            "gps",
            "wgs",
            "gssap",
            "missile",
        )
        return any(token in text for token in watched_pattern)

    return False


def assess_sensitive_launch(row: pd.Series) -> dict:
    name = safe_text(row.get("name"))
    mission_type = safe_text(row.get("mission_type"))
    mission_description = safe_text(row.get("mission_description"))
    provider = safe_text(row.get("provider"))
    rocket = safe_text(row.get("rocket"))
    location_name = safe_text(row.get("location_name"))

    text = " ".join([name, mission_type, mission_description, provider, rocket, location_name]).lower()

    likely_role = "Government or national security mission"
    why_sensitive = (
        "Official U.S. Space Force material says national security launches deliver critical space-based systems "
        "for secure communications, navigation, surveillance, and threat warning, so payload details are often kept broad."
    )
    vehicle_context = ""
    source_keys = ["space_capabilities"]

    if "nrol" in text or "nro" in text:
        likely_role = "Reconnaissance or intelligence support mission"
        why_sensitive = (
            "NRO launch pages say NROL missions carry national security payloads that support the agency's "
            "overhead reconnaissance mission and provide intelligence to senior policymakers, the Intelligence Community, and DoD."
        )
        add_source(source_keys, "nrol_101")
        add_source(source_keys, "nrol_82")
        add_source(source_keys, "nro_launch")
    elif any(token in text for token in ["gps", "positioning", "navigation", "timing"]):
        likely_role = "Positioning, navigation, and timing mission"
        why_sensitive = (
            "The U.S. Space Force says GPS provides global position, navigation, and timing data and is used by "
            "military users, ships, aircraft, land vehicles, and precision-guided munitions, which makes mission details operationally sensitive."
        )
        add_source(source_keys, "gps")
        add_source(source_keys, "milcom_pnt")
    elif any(token in text for token in ["wgs", "satcom", "communications", "communication"]):
        likely_role = "Protected military communications mission"
        why_sensitive = (
            "Space Systems Command says its MILCOM and PNT office develops and sustains military SATCOM, including "
            "protected command-and-control links, anti-jam communications, and wideband military communications capacity."
        )
        add_source(source_keys, "milcom_pnt")
    elif any(token in text for token in ["gssap", "space surveillance", "space situational awareness"]):
        likely_role = "Space surveillance or space domain awareness mission"
        why_sensitive = (
            "SSC mission material says GSSAP supports U.S. Space Command space surveillance operations in near-geosynchronous orbit, "
            "so payload performance and on-orbit behavior are more sensitive than a routine civil mission."
        )
        add_source(source_keys, "ussf_87")
        add_source(source_keys, "vulcan_nssl")
    elif any(token in text for token in ["missile warning", "missile tracking", "tracking layer", "f2", "dsp"]):
        likely_role = "Missile warning or missile tracking mission"
        why_sensitive = (
            "Space Force documents describe these launch orders as part of missile warning and missile tracking architectures, "
            "including tracking-layer and missile-defense spacecraft, which are strategically sensitive mission areas."
        )
        add_source(source_keys, "missile_tracking")
    elif any(token in text for token in ["reconnaissance", "surveillance", "classified", "national security", "military"]):
        likely_role = "Government or national security mission"
        why_sensitive = (
            "The public mission labels point to a defense or intelligence role. Official Space Force material says national security "
            "launch exists to deploy critical space-based systems for warfighters, intelligence users, and strategic decision makers."
        )
        add_source(source_keys, "vulcan_nssl")

    if "electron" in text or "rocket lab" in text:
        vehicle_context = (
            "Rocket Lab's Electron has official NRO use for dedicated small-satellite launches. NROL-151 describes "
            "dedicated access to orbit for small satellites and a U.S. launch pad tailored for government small-satellite missions."
        )
        add_source(source_keys, "nrol_151")
    elif "falcon 9" in text or "spacex" in text:
        vehicle_context = (
            "Falcon 9 has official national security pedigree. NROL-87 shows Falcon 9 carrying an NRO national security payload under the National Security Space Launch framework."
        )
        add_source(source_keys, "nrol_87")
    elif "atlas v" in text:
        vehicle_context = (
            "Atlas V has official NRO mission history. NROL-101 used Atlas V for a national security payload supporting overhead reconnaissance."
        )
        add_source(source_keys, "nrol_101")
    elif "delta iv" in text:
        vehicle_context = (
            "Delta IV Heavy served the heavy-lift end of classified launch. NROL-82 shows it carrying a major national security payload for the NRO mission set."
        )
        add_source(source_keys, "nrol_82")
    elif "vulcan" in text or "united launch alliance" in text or "ula" in text:
        vehicle_context = (
            "Vulcan is certified for National Security Space Launch missions. SSC says that certification adds resiliency and flexibility for the nation's most critical space-based systems."
        )
        add_source(source_keys, "vulcan_nssl")

    official_basis = " | ".join(source["title"] for source in source_objects(source_keys)[:3])
    return {
        "likely_role": likely_role,
        "why_sensitive": why_sensitive,
        "vehicle_context": vehicle_context,
        "official_basis": official_basis,
        "source_keys": source_keys,
    }


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_upcoming_launches():
    url = f"https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit={UPCOMING_LIMIT}&mode=detailed"
    raw = fetch_json_with_retry(url)["results"]
    df = build_launch_rows(raw)
    df = clean_time_col(df, "net")
    if not df.empty:
        df = df.sort_values("net")
    return df


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_recent_launches():
    url = f"https://ll.thespacedevs.com/2.2.0/launch/previous/?limit={RECENT_LIMIT}&mode=detailed"
    raw = fetch_json_with_retry(url)["results"]
    df = build_launch_rows(raw)
    df = clean_time_col(df, "net")
    if not df.empty:
        df = df.sort_values("net", ascending=False)
    return df


def render_metric_card(title, value, detail, accent):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="accent-bar" style="background:{accent};"></div>
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
                <div class="status-key">Filter</div>
                <div class="status-value">{html.escape(search_value)}</div>
            </div>
            <div class="status-item">
                <div class="status-key">Provider Scope</div>
                <div class="status-value">{html.escape(summarize_selected_providers(providers))}</div>
            </div>
            <div class="status-item">
                <div class="status-key">Visible Layers</div>
                <div class="status-value">{html.escape(layer_value)}</div>
            </div>
            <div class="status-item">
                <div class="status-key">Map Summary</div>
                <div class="status-value">{marker_count:,} markers | {html.escape(map_theme)} theme</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_filters(df: pd.DataFrame, search_query: str, providers):
    filtered = df.copy()
    if filtered.empty:
        return filtered

    if providers:
        filtered = filtered[filtered["provider"].isin(providers)]

    if search_query:
        search_text = search_query.lower()
        filtered = filtered[
            filtered["name"].fillna("").str.lower().str.contains(search_text, na=False)
            | filtered["provider"].fillna("").str.lower().str.contains(search_text, na=False)
            | filtered["rocket"].fillna("").str.lower().str.contains(search_text, na=False)
            | filtered["mission_type"].fillna("").str.lower().str.contains(search_text, na=False)
            | filtered["location_name"].fillna("").str.lower().str.contains(search_text, na=False)
        ]

    return filtered.reset_index(drop=True)


def build_launch_icon_html(color):
    return f"""
        <div style="position: relative; width: 28px; height: 28px; transform: translate(-14px, -14px);">
            <div style="
                position:absolute;
                inset: 4px;
                background: #171d1f;
                border: 2px solid {color};
                border-radius: 4px;
                transform: rotate(45deg);
                box-shadow: 0 10px 18px rgba(0,0,0,0.22);
            "></div>
            <div style="
                position:absolute;
                left:50%;
                top:50%;
                width:8px;
                height:8px;
                margin-left:-4px;
                margin-top:-4px;
                background:{color};
                border-radius:999px;
                box-shadow: 0 0 0 3px rgba(255,255,255,0.06);
            "></div>
            <div style="
                position:absolute;
                left:50%;
                top:50%;
                width:20px;
                height:20px;
                margin-left:-10px;
                margin-top:-10px;
                border:1px solid rgba(255,255,255,0.08);
                border-radius:999px;
            "></div>
        </div>
    """


def build_popup_html(row):
    return f"""
        <div style="min-width: 260px; font-family: Segoe UI, sans-serif; color: #edf1ee;">
            <div style="font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #a8b28b; margin-bottom: 6px;">
                Launch Summary
            </div>
            <div style="font-size: 15px; font-weight: 700; color: #edf1ee; margin-bottom: 8px; line-height:1.3;">
                {html.escape(safe_text(row.get('name') or 'Unknown launch'))}
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:12px;">
                <tr><td style="padding:4px 0; color:#87928c;">Provider</td><td style="padding:4px 0; color:#edf1ee;">{html.escape(safe_text(row.get('provider') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#87928c;">Vehicle</td><td style="padding:4px 0; color:#edf1ee;">{html.escape(safe_text(row.get('rocket') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#87928c;">Mission type</td><td style="padding:4px 0; color:#edf1ee;">{html.escape(safe_text(row.get('mission_type') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#87928c;">Time</td><td style="padding:4px 0; color:#edf1ee;">{html.escape(format_time(row.get('net')))}</td></tr>
                <tr><td style="padding:4px 0; color:#87928c;">Location</td><td style="padding:4px 0; color:#edf1ee;">{html.escape(safe_text(row.get('location_name') or 'Unknown'))}</td></tr>
                <tr><td style="padding:4px 0; color:#87928c;">Category</td><td style="padding:4px 0; color:#edf1ee;">{html.escape(safe_text(row.get('map_layer') or 'Launch'))}</td></tr>
            </table>
        </div>
    """


def build_map_dataframe(upcoming_df, failed_df, sensitive_df):
    frames = []

    if not upcoming_df.empty:
        upcoming_map = upcoming_df.copy()
        upcoming_map["map_layer"] = "Upcoming"
        upcoming_map["map_color"] = STATUS_COLORS["Upcoming"]
        frames.append(upcoming_map)

    if not failed_df.empty:
        failed_map = failed_df.copy()
        failed_map["map_layer"] = "Recent failure"
        failed_map["map_color"] = STATUS_COLORS["Recent failure"]
        frames.append(failed_map)

    if not sensitive_df.empty:
        sensitive_map = sensitive_df.copy()
        sensitive_map["map_layer"] = "Sensitive"
        sensitive_map["map_color"] = STATUS_COLORS["Sensitive"]
        frames.append(sensitive_map)

    if not frames:
        return pd.DataFrame()

    map_df = pd.concat(frames, ignore_index=True)
    map_df = map_df.dropna(subset=["lat", "lon"]).copy()
    map_df = map_df.drop_duplicates(subset=["name", "net", "map_layer"])
    return map_df.reset_index(drop=True)


def create_launch_map(map_df: pd.DataFrame, map_theme: str):
    if map_df.empty:
        return None

    center_lat = map_df["lat"].mean()
    center_lon = map_df["lon"].mean()

    launch_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=2,
        control_scale=True,
        prefer_canvas=True,
        tiles=None,
    )

    for theme_name, theme_config in MAP_THEMES.items():
        folium.TileLayer(
            tiles=theme_config["tiles"],
            attr=theme_config["attr"],
            name=theme_name,
            show=theme_name == map_theme,
        ).add_to(launch_map)

    Fullscreen(position="topright").add_to(launch_map)
    MousePosition(
        position="bottomright",
        separator=" | ",
        lng_first=False,
        num_digits=2,
        prefix="Lat / Lon",
    ).add_to(launch_map)

    for layer_name in ["Upcoming", "Recent failure", "Sensitive"]:
        layer_rows = map_df[map_df["map_layer"] == layer_name]
        if layer_rows.empty:
            continue

        layer_group = folium.FeatureGroup(name=layer_name, show=True)
        for _, row in layer_rows.iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                tooltip=f"{safe_text(row.get('name'))} | {layer_name}",
                popup=folium.Popup(build_popup_html(row), max_width=360),
                icon=DivIcon(html=build_launch_icon_html(row["map_color"])),
            ).add_to(layer_group)
        layer_group.add_to(launch_map)

    folium.LayerControl(collapsed=True).add_to(launch_map)
    return launch_map


def display_launch_table(df: pd.DataFrame):
    if df.empty:
        return df

    display_df = df[
        ["name", "net", "status", "provider", "rocket", "mission_type", "location_name"]
    ].copy()
    display_df["net"] = display_df["net"].apply(format_time)
    display_df = display_df.rename(
        columns={
            "name": "Launch",
            "net": "Time (UTC)",
            "status": "Status",
            "provider": "Provider",
            "rocket": "Rocket",
            "mission_type": "Mission Type",
            "location_name": "Location",
        }
    )
    return display_df


inject_styles()

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-kicker">Operational Launch Intelligence</div>
        <h1 class="hero-title">Orbital Launch Monitor</h1>
        <p class="hero-copy">
            Monitor upcoming launches, recent failures, and publicly signaled sensitive missions in a briefing-style
            interface designed for quick scan, clear labels, and source-backed context.
        </p>
        <div class="hero-meta">
            <strong>Sources:</strong> public launch feeds and official program references
            &nbsp;&nbsp;|&nbsp;&nbsp;
            <strong>Refresh window:</strong> {CACHE_TTL_SECONDS // 60} minutes
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

launch_error = None
recent_launch_error = None

try:
    launches_df = get_upcoming_launches()
except Exception as error:
    launches_df = pd.DataFrame()
    launch_error = str(error)

try:
    recent_launches_df = get_recent_launches()
except Exception as error:
    recent_launches_df = pd.DataFrame()
    recent_launch_error = str(error)

failed_launches_df = pd.DataFrame()
sensitive_launches_df = pd.DataFrame()

if not recent_launches_df.empty:
    now_utc = pd.Timestamp.utcnow()
    failed_mask = (
        recent_launches_df["status"]
        .fillna("")
        .str.lower()
        .str.contains("failure", na=False)
    )
    failed_launches_df = recent_launches_df[failed_mask].copy()
    failed_launches_df = failed_launches_df[
        failed_launches_df["net"] >= now_utc - pd.Timedelta(days=30)
    ].copy()

    sensitive_mask = recent_launches_df.apply(looks_sensitive, axis=1)
    sensitive_launches_df = recent_launches_df[sensitive_mask].copy()
    sensitive_launches_df = sensitive_launches_df[
        sensitive_launches_df["net"] >= now_utc - pd.Timedelta(days=120)
    ].copy()

all_providers = sorted(
    {
        provider
        for provider in pd.concat(
            [
                launches_df.get("provider", pd.Series(dtype=str)),
                recent_launches_df.get("provider", pd.Series(dtype=str)),
            ],
            ignore_index=True,
        ).dropna()
        if safe_text(provider)
    }
)

with st.sidebar:
    st.markdown("### Filters")
    st.markdown(
        """
        <div class="sidebar-note">
            Narrow the launch picture by mission, provider, and category, then review the map and tables for the current operating view.
        </div>
        """,
        unsafe_allow_html=True,
    )
    refresh_clicked = st.button("Refresh launch feeds", use_container_width=True)
    if refresh_clicked:
        get_upcoming_launches.clear()
        get_recent_launches.clear()
        st.rerun()

    search_query = st.text_input(
        "Search",
        placeholder="Mission, provider, vehicle, role, or site",
    ).strip()

    provider_filter = st.multiselect(
        "Providers",
        options=all_providers,
        default=[],
    )

    st.markdown("### Map Layers")
    st.caption("Choose which mission categories appear on the map.")
    show_upcoming = st.toggle("Upcoming launches", value=True)
    show_failures = st.toggle("Recent failures", value=True)
    show_sensitive = st.toggle("Sensitive launches", value=True)
    map_theme = st.selectbox("Map theme", options=list(MAP_THEMES.keys()), index=1)

filtered_upcoming_df = apply_filters(launches_df, search_query, provider_filter)
filtered_failed_df = apply_filters(failed_launches_df, search_query, provider_filter)
filtered_sensitive_df = apply_filters(sensitive_launches_df, search_query, provider_filter)

map_df = build_map_dataframe(
    filtered_upcoming_df if show_upcoming else pd.DataFrame(),
    filtered_failed_df if show_failures else pd.DataFrame(),
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
        "Upcoming launches",
        f"{len(filtered_upcoming_df):,}",
        "Filtered view of the live upcoming schedule",
        STATUS_COLORS["Upcoming"],
    )
with metric_columns[1]:
    render_metric_card(
        "Recent failures",
        f"{len(filtered_failed_df):,}",
        "Previous 30 days with failure status in public data",
        STATUS_COLORS["Recent failure"],
    )
with metric_columns[2]:
    render_metric_card(
        "Sensitive launches",
        f"{len(filtered_sensitive_df):,}",
        "Publicly signaled government, military, or national security profiles",
        STATUS_COLORS["Sensitive"],
    )
with metric_columns[3]:
    if launch_error and recent_launch_error:
        render_metric_card("Feed status", "Degraded", "Upcoming and recent feeds both had upstream issues", "#d36b5f")
    elif launch_error or recent_launch_error:
        render_metric_card("Feed status", "Partial", "One of the two launch feeds is degraded", "#d9a24b")
    else:
        render_metric_card("Feed status", "Online", "Upcoming and recent launch feeds loaded successfully", "#65b67d")

st.markdown("")

map_col, side_col = st.columns([3.1, 1.15], gap="large")

with map_col:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-kicker">Map View</div>
            <div class="panel-title">Operational Map</div>
            <div class="panel-copy">
                Launch sites plotted by category for the active filter set. Marker colors indicate upcoming activity,
                recent failures, and sensitive mission profiles.
            </div>
            <div class="legend-row">
                <span class="legend-chip"><span class="legend-dot" style="background:{upcoming};"></span>Upcoming</span>
                <span class="legend-chip"><span class="legend-dot" style="background:{failure};"></span>Recent failure</span>
                <span class="legend-chip"><span class="legend-dot" style="background:{sensitive};"></span>Sensitive</span>
            </div>
        </div>
        """.format(
            upcoming=STATUS_COLORS["Upcoming"],
            failure=STATUS_COLORS["Recent failure"],
            sensitive=STATUS_COLORS["Sensitive"],
        ),
        unsafe_allow_html=True,
    )

    if launch_error and recent_launch_error:
        st.error("Launch map is unavailable because both upstream feeds are currently degraded.")
    elif map_df.empty:
        st.info("No launch sites match the current filters.")
    else:
        launch_map = create_launch_map(map_df, map_theme)
        if launch_map is None:
            st.info("No coordinates are available for the filtered launch records.")
        else:
            st_folium(launch_map, use_container_width=True, height=720)

with side_col:
    st.markdown("#### Next scheduled launch")
    if filtered_upcoming_df.empty:
        st.info("No upcoming launch matches the current filters.")
    else:
        next_launch = filtered_upcoming_df.sort_values("net").iloc[0]
        st.markdown(
            f"""
            <div class="panel-card">
                <div class="panel-kicker">Launch Brief</div>
                <div class="panel-title">{html.escape(safe_text(next_launch.get("name") or "Unknown launch"))}</div>
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

    st.markdown("#### Assessment method")
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-kicker">Method</div>
            <div class="panel-title">Why a launch may be sensitive</div>
            <div class="panel-copy">
                The explanations in this section are tied to official NRO, U.S. Space Force, Space Systems Command,
                and launch-program mission material. Flags are based on public metadata and source-backed inference,
                not on classified payload disclosure.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Mission context is best-effort, and each explanation is anchored to official program or mission references linked in the cards.")

tab_upcoming, tab_failed, tab_sensitive, tab_context = st.tabs(
    ["Upcoming", "Failures", "Sensitive", "Context"]
)

with tab_upcoming:
    st.markdown("### Upcoming launches")
    if launch_error:
        st.warning("The upstream upcoming-launch feed is temporarily unavailable.")
    elif filtered_upcoming_df.empty:
        st.info("No upcoming launches match the current filters.")
    else:
        st.dataframe(display_launch_table(filtered_upcoming_df), use_container_width=True, hide_index=True)

with tab_failed:
    st.markdown("### Recent failures")
    if recent_launch_error:
        st.warning("The recent-launch feed is temporarily unavailable.")
    elif filtered_failed_df.empty:
        st.success("No failed launches were found in the last 30 days for the current filters.")
    else:
        st.dataframe(display_launch_table(filtered_failed_df), use_container_width=True, hide_index=True)

with tab_sensitive:
    st.markdown("### Sensitive missions")
    st.caption("This table uses public mission naming, role labels, and launch metadata to flag launches that appear government, military, or national-security linked.")
    if recent_launch_error:
        st.warning("Sensitive launch detection depends on the recent-launch feed, which is temporarily unavailable.")
    elif filtered_sensitive_df.empty:
        st.info("No publicly signaled sensitive launches match the current filters.")
    else:
        st.dataframe(display_launch_table(filtered_sensitive_df), use_container_width=True, hide_index=True)

with tab_context:
    st.markdown("### Official mission context")
    st.caption("Possible reasons a launch may be sensitive, paired with official mission and program references for review.")
    if recent_launch_error:
        st.warning("Mission context is unavailable because the recent-launch feed could not be loaded.")
    elif filtered_sensitive_df.empty:
        st.info("No sensitive launch profiles are available for context right now.")
    else:
        context_rows = filtered_sensitive_df.head(min(8, len(filtered_sensitive_df))).copy()
        context_records = []
        for _, row in context_rows.iterrows():
            assessment = assess_sensitive_launch(row)
            context_records.append(
                {
                    "Launch": safe_text(row.get("name")),
                    "Time (UTC)": format_time(row.get("net")),
                    "Provider": safe_text(row.get("provider")),
                    "Rocket": safe_text(row.get("rocket")),
                    "Likely Role": assessment["likely_role"],
                    "Why It Could Be Sensitive": assessment["why_sensitive"],
                    "Vehicle Context": assessment["vehicle_context"],
                    "Official Basis": assessment["official_basis"],
                    "sources": assessment["source_keys"],
                }
            )

        context_df = pd.DataFrame(context_records)
        summary_df = context_df[
            ["Launch", "Time (UTC)", "Provider", "Rocket", "Likely Role", "Official Basis"]
        ].copy()
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        for _, row in context_df.iterrows():
            st.markdown(
                f"""
                <div class="panel-card">
                    <div class="panel-kicker">Assessment</div>
                    <div class="panel-title">{html.escape(row['Launch'])}</div>
                    <div class="panel-copy">
                        <strong>Likely role:</strong> {html.escape(row['Likely Role'])}<br>
                        <strong>Why it could be sensitive:</strong> {html.escape(row['Why It Could Be Sensitive'])}<br>
                        <strong>Launch vehicle context:</strong> {html.escape(row['Vehicle Context'] or 'No extra vehicle-specific note applied for this launch.')}<br>
                        <strong>Official basis:</strong> {html.escape(row['Official Basis'])}
                    </div>
                    {source_links_html(row['sources'])}
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("---")
st.caption(
    f"Current picture: {len(filtered_upcoming_df):,} upcoming launches, {len(filtered_failed_df):,} recent failures, "
    f"and {len(filtered_sensitive_df):,} sensitive missions under the active filters."
)
