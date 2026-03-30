import html
import re
import time

import folium
import pandas as pd
import requests
import streamlit as st
from folium.features import DivIcon
from folium.plugins import Fullscreen, MousePosition
from streamlit_folium import st_folium

from utils.event_logger import log_event

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
    "Upcoming": "#38bdf8",
    "Recent failure": "#ffb454",
    "Sensitive": "#ff5f6d",
    "Online": "#39d98a",
}

OFFICIAL_SOURCES = {
    # ---------------------------
    # UNITED STATES
    # ---------------------------
    "us_nro_launch": {
        "title": "NRO launch overview",
        "url": "https://www.nro.gov/Launch/",
        "summary": "NRO says its satellites support intelligence, global coverage, research, and disaster relief, and that launch systems are selected for the mission orbit and payload profile.",
        "country_group": "United States",
    },
    "us_nrol_101": {
        "title": "NRO NROL-101 official launch page",
        "url": "https://www.nro.gov/Launches/launch-nrol-101/",
        "summary": "NRO says NROL-101 carried a national security payload supporting overhead reconnaissance and intelligence support to policymakers, the Intelligence Community, and DoD.",
        "country_group": "United States",
    },
    "us_nrol_82": {
        "title": "NRO NROL-82 official launch page",
        "url": "https://www.nro.gov/Launches/launch-nrol-82/",
        "summary": "NRO says NROL-82 carried a national security payload and flew on Delta IV Heavy.",
        "country_group": "United States",
    },
    "us_nrol_151": {
        "title": "NRO NROL-151 official launch page",
        "url": "https://www.nro.gov/Launches/launch-nrol-151/",
        "summary": "NRO says Electron provides dedicated access to orbit for small satellites and describes Rocket Lab's U.S. launch capability for government missions.",
        "country_group": "United States",
    },
    "us_nrol_87": {
        "title": "NRO NROL-87 official launch page",
        "url": "https://www.nro.gov/Launches/launch-nrol-87/",
        "summary": "NRO says NROL-87 carried a national security payload aboard Falcon 9 under a National Security Space Launch mission.",
        "country_group": "United States",
    },
    "us_gps": {
        "title": "U.S. Space Force GPS fact sheet",
        "url": "https://www.spaceforce.mil/About-Us/Fact-Sheets/Article/2197765/global-positioning-system/",
        "summary": "The Space Force says GPS provides global positioning, navigation, and timing for military and civil users.",
        "country_group": "United States",
    },
    "us_milcom_pnt": {
        "title": "SSC Military Communications and PNT office",
        "url": "https://www.ssc.spaceforce.mil/Program-Offices/Military-Communications-and-Positioning",
        "summary": "Space Systems Command says MILCOM and PNT delivers military SATCOM and more secure, jam-resistant PNT capability.",
        "country_group": "United States",
    },
    "us_vulcan_nssl": {
        "title": "SSC Vulcan NSSL certification release",
        "url": "https://www.ssc.spaceforce.mil/Newsroom/Article/4136016/u-s-space-force-ussf-certifies-united-launch-alliance-ula-vulcan-for-national-s",
        "summary": "SSC says NSSL certification supports the launch of critical national security space systems with resiliency and flexibility.",
        "country_group": "United States",
    },
    "us_missile_tracking": {
        "title": "SSC missile warning and tracking launch award release",
        "url": "https://www.ssc.spaceforce.mil/Newsroom/Article/4374896/space-systems-command-awards-task-orders-to-launch-missile-warning-and-missile",
        "summary": "SSC says these launch awards support missile warning and missile tracking payloads.",
        "country_group": "United States",
    },
    "us_ussf_87": {
        "title": "SSC USSF-87 mission preparation release",
        "url": "https://www.ssc.spaceforce.mil/Newsroom/Article/4403552/space-systems-command-mission-partners-prepares-ussf-87-for-national-space-secu",
        "summary": "SSC says the USSF-87 primary payload, GSSAP, supports U.S. Space Command space surveillance operations.",
        "country_group": "United States",
    },
    "us_space_capabilities": {
        "title": "U.S. Space Force space capabilities overview",
        "url": "https://www.spaceforce.mil/About-Us/About-Space-Force/Space-Capabilities/",
        "summary": "The Space Force says military space capabilities include communications, navigation, threat warning, surveillance, and launch support.",
        "country_group": "United States",
    },

    # ---------------------------
    # CHINA
    # ---------------------------
    "cn_programme": {
        "title": "CNSA: China's Space Program: A 2021 Perspective",
        "url": "https://www.cnsa.gov.cn/english/n6465645/n6465648/c6813088/content.html",
        "summary": "CNSA says China's space program serves scientific development, national rights and interests, and national security alongside peaceful use of outer space.",
        "country_group": "China",
    },
    "cn_english_home": {
        "title": "CNSA English portal",
        "url": "https://www.cnsa.gov.cn/english/",
        "summary": "Official English CNSA portal with mission and launch coverage.",
        "country_group": "China",
    },

    # ---------------------------
    # INDIA
    # ---------------------------
    "in_launch_missions": {
        "title": "ISRO Launch Missions",
        "url": "https://www.isro.gov.in/LaunchMissions.html",
        "summary": "Official ISRO launch mission page covering missions, launchers, satellites, and programme activity.",
        "country_group": "India",
    },
    "in_spacecraft_missions": {
        "title": "ISRO Spacecraft Missions",
        "url": "https://www.isro.gov.in/SpacecraftMissions.html",
        "summary": "Official ISRO page listing spacecraft and satellite missions.",
        "country_group": "India",
    },
    "in_launchers": {
        "title": "ISRO Launchers",
        "url": "https://www.isro.gov.in/Launchers.html",
        "summary": "ISRO says launch vehicles carry spacecraft to space and describes PSLV, GSLV, and LVM3.",
        "country_group": "India",
    },
    "in_pslv_c62": {
        "title": "ISRO PSLV-C62 / EOS-N1 Mission",
        "url": "https://www.isro.gov.in/Mission_PSLV_C62.html",
        "summary": "Official ISRO mission page for a recent PSLV Earth observation mission.",
        "country_group": "India",
    },

    # ---------------------------
    # JAPAN
    # ---------------------------
    "jp_missions": {
        "title": "JAXA Our Missions",
        "url": "https://global.jaxa.jp/",
        "summary": "Official JAXA English missions portal.",
        "country_group": "Japan",
    },
    "jp_h3": {
        "title": "JAXA H3 Launch Vehicle",
        "url": "https://global.jaxa.jp/projects/rockets/h3/",
        "summary": "JAXA describes H3 as Japan's new mainstay launch vehicle.",
        "country_group": "Japan",
    },
    "jp_tanegashima": {
        "title": "JAXA Tanegashima Space Center",
        "url": "https://global.jaxa.jp/about/centers/tnsc/index.html",
        "summary": "JAXA describes Tanegashima as Japan's major rocket launch complex.",
        "country_group": "Japan",
    },
    "jp_satellite_topics": {
        "title": "JAXA satellite mission topics",
        "url": "https://global.jaxa.jp/projects/sat/topics.html",
        "summary": "Official JAXA English satellite mission material.",
        "country_group": "Japan",
    },

    # ---------------------------
    # EUROPE / ESA
    # ---------------------------
    "eu_secure_comms": {
        "title": "ESA Pacis 3 – Secure Communications",
        "url": "https://www.esa.int/Applications/Connectivity_and_Secure_Communications/Pacis_3_Secure_Communications",
        "summary": "ESA says Pacis 3 works toward secure communications services for governments in Europe.",
        "country_group": "Europe",
    },
    "eu_iris2_support": {
        "title": "ESA support for EU secure communication satellites system",
        "url": "https://www.esa.int/About_Us/Corporate_news/ESA_to_support_the_development_of_EU_s_secure_communication_satellites_system",
        "summary": "ESA says the planned secure communications constellation will deliver resilient and secure communications for EU governments and others.",
        "country_group": "Europe",
    },
    "eu_govsatcom": {
        "title": "ESA pooling and sharing for secure government satcoms",
        "url": "https://www.esa.int/Applications/Connectivity_and_Secure_Communications/Pooling_and_sharing_for_secure_government_satcoms",
        "summary": "ESA describes secure government satcom arrangements for public-sector users.",
        "country_group": "Europe",
    },
    "eu_spainsat_ng": {
        "title": "ESA SpainSat NG secure communications article",
        "url": "https://www.esa.int/Applications/Connectivity_and_Secure_Communications/SpainSat_NG_programme_completed_as_second_secure_communications_satellite_launches",
        "summary": "ESA says SpainSat NG will serve the Spanish Armed Forces and allied government users.",
        "country_group": "Europe",
    },

    # ---------------------------
    # UNITED KINGDOM / ALLIED
    # ---------------------------
    "uk_space_command": {
        "title": "UK Space Command",
        "url": "https://www.gov.uk/government/organisations/uk-space-command",
        "summary": "Official UK government space command organisation page.",
        "country_group": "United Kingdom",
    },

    # ---------------------------
    # RUSSIA
    # ---------------------------
    "ru_roscosmos": {
        "title": "Roscosmos official portal",
        "url": "https://www.roscosmos.ru/",
        "summary": "Official Roscosmos portal covering Russian launch and space activity.",
        "country_group": "Russia",
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
    "secure communications",
    "govsatcom",
    "defence",
    "defense",
    "space domain awareness",
    "space surveillance",
    "warning",
    "yaogan",
    "gaofen",
    "beidou",
    "qzss",
    "quasi-zenith",
    "irnss",
    "navic",
    "kosmos",
    "soyuz",
]

WATCHED_PROVIDERS = [
    "united launch alliance",
    "spacex",
    "rocket lab",
    "northrop grumman",
    "arianespace",
    "mitsubishi heavy industries",
    "isro",
    "china aerospace science and technology",
    "casc",
    "expace",
    "roscosmos",
]

COUNTRY_CODE_TO_GROUP = {
    "US": "United States",
    "CN": "China",
    "IN": "India",
    "JP": "Japan",
    "FR": "Europe",
    "DE": "Europe",
    "IT": "Europe",
    "ES": "Europe",
    "GB": "United Kingdom",
    "UK": "United Kingdom",
    "RU": "Russia",
    "KZ": "Russia",
}

COUNTRY_NAME_HINTS = {
    "United States": [
        "united states",
        "usa",
        "cape canaveral",
        "vandenberg",
        "kennedy",
        "wallops",
        "nrol",
        "ussf",
        "nro",
        "gssap",
        "gps",
        "wgs",
    ],
    "China": [
        "china",
        "chinese",
        "taiyuan",
        "jiuquan",
        "wenchang",
        "xichang",
        "long march",
        "yaogan",
        "gaofen",
        "beidou",
        "shijian",
        "tjs",
    ],
    "India": [
        "india",
        "indian",
        "isro",
        "sriharikota",
        "satish dhawan",
        "pslv",
        "gslv",
        "lvm3",
        "navic",
        "irnss",
        "eos",
        "risat",
        "cartosat",
        "gsat",
    ],
    "Japan": [
        "japan",
        "japanese",
        "jaxa",
        "tanegashima",
        "uchinoura",
        "h3",
        "h-iia",
        "h-iib",
        "qzss",
        "quasi-zenith",
        "ibuki",
        "himawari",
    ],
    "Europe": [
        "europe",
        "esa",
        "ariane",
        "vega",
        "arianespace",
        "kourou",
        "guiana space centre",
        "govsatcom",
        "iris2",
        "spainsat",
    ],
    "United Kingdom": [
        "united kingdom",
        "britain",
        "british",
        "space command",
        "skynet",
    ],
    "Russia": [
        "russia",
        "russian",
        "soyuz",
        "kosmos",
        "roscosmos",
        "baikonur",
        "plesetsk",
        "angara",
        "progress",
    ],
}

GLOBAL_ROLE_PATTERNS = {
    "Reconnaissance or remote sensing mission": [
        "reconnaissance",
        "surveillance",
        "yaogan",
        "gaofen",
        "earth observation",
        "remote sensing",
        "cartosat",
        "risat",
        "kosmos",
    ],
    "Positioning, navigation, and timing mission": [
        "gps",
        "beidou",
        "navic",
        "irnss",
        "qzss",
        "quasi-zenith",
        "positioning",
        "navigation",
        "timing",
        "pnt",
    ],
    "Protected communications mission": [
        "satcom",
        "communications",
        "communication",
        "secure communications",
        "govsatcom",
        "skynet",
        "gsat",
        "wgs",
    ],
    "Missile warning or tracking mission": [
        "missile warning",
        "missile tracking",
        "tracking layer",
        "warning",
    ],
    "Space surveillance or space domain awareness mission": [
        "space surveillance",
        "space domain awareness",
        "gssap",
        "situational awareness",
    ],
    "Government or national security mission": [
        "government",
        "national security",
        "military",
        "defence",
        "defense",
        "classified",
    ],
}


def inject_styles():
    st.markdown(
        """
        <style>
            :root {
                --bg-0: #07111f;
                --bg-1: #0d1b2a;
                --bg-2: #0f2237;
                --card-0: rgba(10, 21, 35, 0.92);
                --card-1: rgba(15, 31, 49, 0.86);
                --stroke: rgba(130, 161, 191, 0.22);
                --text-main: #e8f1fb;
                --text-soft: #91a9c3;
                --blue: #38bdf8;
                --amber: #ffb454;
                --red: #ff5f6d;
                --green: #39d98a;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 28%),
                    radial-gradient(circle at top right, rgba(88, 166, 255, 0.12), transparent 26%),
                    linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 60%, #0a1524 100%);
                color: var(--text-main);
                font-family: "Aptos", "Segoe UI", sans-serif;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(9, 19, 32, 0.97), rgba(9, 19, 32, 0.92));
                border-right: 1px solid var(--stroke);
            }

            [data-testid="stSidebar"] * {
                color: var(--text-main);
            }

            .hero-card {
                border: 1px solid var(--stroke);
                background: linear-gradient(145deg, rgba(10, 21, 35, 0.96), rgba(15, 31, 49, 0.92));
                border-radius: 24px;
                padding: 1.5rem 1.6rem;
                box-shadow: 0 18px 40px rgba(4, 9, 18, 0.26);
                margin-bottom: 1rem;
            }

            .hero-kicker {
                letter-spacing: 0.16rem;
                font-size: 0.72rem;
                font-weight: 700;
                color: #84d7ff;
                margin-bottom: 0.4rem;
            }

            .hero-title {
                font-size: 2.25rem;
                line-height: 1.05;
                font-weight: 800;
                margin: 0;
                color: var(--text-main);
            }

            .hero-copy {
                margin: 0.65rem 0 0 0;
                max-width: 64rem;
                color: var(--text-soft);
                font-size: 0.98rem;
            }

            .signal-banner {
                border: 1px solid rgba(56, 189, 248, 0.26);
                background:
                    linear-gradient(135deg, rgba(15, 36, 58, 0.96), rgba(11, 23, 37, 0.94)),
                    radial-gradient(circle at left center, rgba(56, 189, 248, 0.15), transparent 40%);
                border-radius: 22px;
                padding: 1rem 1.2rem;
                box-shadow: 0 16px 38px rgba(4, 9, 18, 0.26);
                margin-bottom: 1rem;
            }

            .signal-kicker {
                font-size: 0.74rem;
                text-transform: uppercase;
                letter-spacing: 0.12rem;
                color: #8edfff;
                font-weight: 700;
                margin-bottom: 0.35rem;
            }

            .signal-title {
                font-size: 1.18rem;
                font-weight: 800;
                color: #eef7ff;
                margin-bottom: 0.25rem;
            }

            .signal-copy {
                font-size: 0.95rem;
                color: var(--text-soft);
                line-height: 1.5;
            }

            .insight-card {
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(12, 24, 39, 0.9), rgba(14, 32, 50, 0.76));
                border-radius: 20px;
                padding: 1rem 1rem 0.95rem 1rem;
                min-height: 130px;
                box-shadow: 0 12px 28px rgba(4, 9, 18, 0.24);
            }

            .insight-label {
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.09rem;
                color: #7ed6ff;
                margin-bottom: 0.45rem;
                font-weight: 700;
            }

            .insight-title {
                font-size: 1.02rem;
                font-weight: 800;
                line-height: 1.3;
                color: var(--text-main);
                margin-bottom: 0.35rem;
            }

            .insight-copy {
                font-size: 0.9rem;
                color: var(--text-soft);
                line-height: 1.45;
            }

            .metric-card {
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(12, 24, 39, 0.9), rgba(14, 32, 50, 0.76));
                border-radius: 20px;
                padding: 1rem 1rem 0.95rem 1rem;
                min-height: 124px;
                box-shadow: 0 12px 28px rgba(4, 9, 18, 0.24);
            }

            .metric-label {
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.08rem;
                color: var(--text-soft);
                margin-bottom: 0.45rem;
            }

            .metric-value {
                font-size: 2rem;
                font-weight: 800;
                line-height: 1;
                margin-bottom: 0.35rem;
                color: var(--text-main);
            }

            .metric-detail {
                font-size: 0.92rem;
                color: var(--text-soft);
                line-height: 1.4;
            }

            .accent-bar {
                width: 54px;
                height: 4px;
                border-radius: 999px;
                margin-bottom: 0.8rem;
            }

            .panel-card {
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(10, 23, 37, 0.9), rgba(14, 31, 49, 0.82));
                border-radius: 20px;
                padding: 1rem 1rem 0.9rem 1rem;
                box-shadow: 0 12px 28px rgba(4, 9, 18, 0.22);
                margin-bottom: 0.9rem;
            }

            .panel-title {
                font-size: 1rem;
                font-weight: 800;
                margin-bottom: 0.2rem;
                color: var(--text-main);
            }

            .panel-copy {
                color: var(--text-soft);
                font-size: 0.92rem;
                margin-bottom: 0.3rem;
                line-height: 1.5;
            }

            .event-card {
                border: 1px solid rgba(255, 95, 109, 0.20);
                background: linear-gradient(180deg, rgba(15, 28, 44, 0.96), rgba(12, 22, 36, 0.9));
                border-radius: 22px;
                padding: 1rem 1rem 0.95rem 1rem;
                box-shadow: 0 16px 34px rgba(4, 9, 18, 0.28);
                margin-bottom: 0.9rem;
            }

            .event-kicker {
                font-size: 0.74rem;
                text-transform: uppercase;
                letter-spacing: 0.1rem;
                color: #ff9aa4;
                font-weight: 700;
                margin-bottom: 0.4rem;
            }

            .event-title {
                font-size: 1.05rem;
                font-weight: 800;
                color: var(--text-main);
                margin-bottom: 0.5rem;
                line-height: 1.35;
            }

            .event-detail {
                color: var(--text-soft);
                font-size: 0.91rem;
                line-height: 1.5;
                margin-bottom: 0.22rem;
            }

            .badge {
                display: inline-block;
                padding: 0.28rem 0.62rem;
                border-radius: 999px;
                font-size: 0.74rem;
                font-weight: 800;
                margin-right: 0.35rem;
                margin-bottom: 0.35rem;
                border: 1px solid transparent;
            }

            .badge-blue {
                color: #dff7ff;
                background: rgba(56, 189, 248, 0.15);
                border-color: rgba(56, 189, 248, 0.24);
            }

            .badge-red {
                color: #ffe9ec;
                background: rgba(255, 95, 109, 0.14);
                border-color: rgba(255, 95, 109, 0.24);
            }

            .badge-amber {
                color: #fff2dc;
                background: rgba(255, 180, 84, 0.14);
                border-color: rgba(255, 180, 84, 0.24);
            }

            .badge-green {
                color: #e6fff1;
                background: rgba(57, 217, 138, 0.14);
                border-color: rgba(57, 217, 138, 0.24);
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 0.6rem;
            }

            .stTabs [data-baseweb="tab"] {
                border-radius: 999px;
                background: rgba(15, 31, 49, 0.7);
                border: 1px solid var(--stroke);
                color: var(--text-main);
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .stDataFrame, div[data-testid="stTable"] {
                border-radius: 18px;
                overflow: hidden;
                border: 1px solid var(--stroke);
            }

            .source-chip {
                display: inline-block;
                padding: 0.25rem 0.55rem;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 700;
                color: #dff4ff;
                background: rgba(56, 189, 248, 0.16);
                border: 1px solid rgba(56, 189, 248, 0.28);
                margin-right: 0.35rem;
                margin-bottom: 0.35rem;
                text-decoration: none;
            }

            .legend-row {
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
                margin-top: 0.4rem;
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
    if key in OFFICIAL_SOURCES and key not in source_keys:
        source_keys.append(key)


def source_objects(source_keys):
    return [OFFICIAL_SOURCES[key] for key in source_keys if key in OFFICIAL_SOURCES]


def source_links_html(source_keys):
    links = []
    for source in source_objects(source_keys):
        links.append(
            f'<a class="source-chip" href="{source["url"]}" target="_blank">{html.escape(source["title"])}</a>'
        )
    return "".join(links)


def text_contains_word(text: str, phrase: str) -> bool:
    phrase = safe_text(phrase).lower()
    text = safe_text(text).lower()
    if not phrase or not text:
        return False
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def infer_country_group(row: pd.Series) -> str:
    country_code = safe_text(row.get("country_code")).upper()
    if country_code in COUNTRY_CODE_TO_GROUP:
        return COUNTRY_CODE_TO_GROUP[country_code]

    name = safe_text(row.get("name"))
    provider = safe_text(row.get("provider"))
    rocket = safe_text(row.get("rocket"))
    mission_type = safe_text(row.get("mission_type"))
    mission_description = safe_text(row.get("mission_description"))
    location_name = safe_text(row.get("location_name"))
    pad_name = safe_text(row.get("pad_name"))

    text = " ".join(
        [name, provider, rocket, mission_type, mission_description, location_name, pad_name]
    ).lower()

    if "long march" in text or "yaogan" in text or "gaofen" in text or "beidou" in text:
        return "China"
    if "soyuz" in text or "kosmos" in text or "roscosmos" in text or "angara" in text:
        return "Russia"
    if "pslv" in text or "gslv" in text or "lvm3" in text or "isro" in text:
        return "India"
    if "jaxa" in text or "tanegashima" in text or "qzss" in text or "h3" in text:
        return "Japan"

    for country_group, hints in COUNTRY_NAME_HINTS.items():
        if any(text_contains_word(text, hint) for hint in hints):
            return country_group

    return "Other / Unclear"


def infer_likely_role(text: str) -> str:
    for role, patterns in GLOBAL_ROLE_PATTERNS.items():
        if any(pattern in text for pattern in patterns):
            return role
    return "Government or national security mission"


def looks_sensitive(row: pd.Series) -> bool:
    name = safe_text(row.get("name")).lower()
    mission_type = safe_text(row.get("mission_type")).lower()
    mission_description = safe_text(row.get("mission_description")).lower()
    provider = safe_text(row.get("provider")).lower()
    rocket = safe_text(row.get("rocket")).lower()
    location_name = safe_text(row.get("location_name")).lower()

    text = " ".join([name, mission_type, mission_description, provider, rocket, location_name])

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
            "beidou",
            "yaogan",
            "gaofen",
            "qzss",
            "navic",
            "govsatcom",
            "secure communications",
            "kosmos",
            "soyuz",
        )
        return any(token in text for token in watched_pattern)

    return False


def attach_country_sources(country_group: str, source_keys: list):
    if country_group == "United States":
        add_source(source_keys, "us_space_capabilities")
    elif country_group == "China":
        add_source(source_keys, "cn_programme")
        add_source(source_keys, "cn_english_home")
    elif country_group == "India":
        add_source(source_keys, "in_launch_missions")
        add_source(source_keys, "in_spacecraft_missions")
    elif country_group == "Japan":
        add_source(source_keys, "jp_missions")
        add_source(source_keys, "jp_tanegashima")
    elif country_group == "Europe":
        add_source(source_keys, "eu_secure_comms")
    elif country_group == "United Kingdom":
        add_source(source_keys, "uk_space_command")
    elif country_group == "Russia":
        add_source(source_keys, "ru_roscosmos")


def assess_sensitive_launch(row: pd.Series) -> dict:
    name = safe_text(row.get("name"))
    mission_type = safe_text(row.get("mission_type"))
    mission_description = safe_text(row.get("mission_description"))
    provider = safe_text(row.get("provider"))
    rocket = safe_text(row.get("rocket"))
    location_name = safe_text(row.get("location_name"))
    country_group = infer_country_group(row)

    text = " ".join([name, mission_type, mission_description, provider, rocket, location_name]).lower()

    likely_role = infer_likely_role(text)
    source_keys = []
    attach_country_sources(country_group, source_keys)

    why_sensitive = (
        "Public mission labels suggest a government, military, security, navigation, surveillance, or secure-communications role rather than a purely commercial or civil profile."
    )
    vehicle_context = ""

    if country_group == "United States":
        if "nrol" in text or "nro" in text:
            likely_role = "Reconnaissance or intelligence support mission"
            why_sensitive = (
                "Public naming strongly suggests an NRO-linked mission. Official NRO mission material describes NROL launches as national security payloads supporting overhead reconnaissance and intelligence support."
            )
            add_source(source_keys, "us_nrol_101")
            add_source(source_keys, "us_nrol_82")
            add_source(source_keys, "us_nro_launch")
        elif any(token in text for token in ["gps", "positioning", "navigation", "timing"]):
            likely_role = "Positioning, navigation, and timing mission"
            why_sensitive = (
                "Public mission labels suggest a PNT payload. Official U.S. Space Force material says GPS provides military and civil positioning, navigation, and timing support."
            )
            add_source(source_keys, "us_gps")
            add_source(source_keys, "us_milcom_pnt")
        elif any(token in text for token in ["wgs", "satcom", "communications", "communication"]):
            likely_role = "Protected communications mission"
            why_sensitive = (
                "Public naming suggests a protected communications or military SATCOM role. Official SSC material says MILCOM and PNT delivers military SATCOM and protected command-and-control links."
            )
            add_source(source_keys, "us_milcom_pnt")
        elif any(token in text for token in ["gssap", "space surveillance", "space situational awareness"]):
            likely_role = "Space surveillance or space domain awareness mission"
            why_sensitive = (
                "Public mission labels suggest a space surveillance function. SSC mission material says GSSAP supports U.S. Space Command space surveillance operations."
            )
            add_source(source_keys, "us_ussf_87")
            add_source(source_keys, "us_vulcan_nssl")
        elif any(token in text for token in ["missile warning", "missile tracking", "tracking layer", "dsp"]):
            likely_role = "Missile warning or tracking mission"
            why_sensitive = (
                "Public mission labels suggest missile warning or missile tracking architecture. SSC launch material explicitly links this mission family to missile warning and missile tracking payloads."
            )
            add_source(source_keys, "us_missile_tracking")
        else:
            add_source(source_keys, "us_space_capabilities")
            add_source(source_keys, "us_vulcan_nssl")

        if "electron" in text or "rocket lab" in text:
            vehicle_context = "Rocket Lab's Electron has an official NRO mission pedigree for dedicated small-satellite launches."
            add_source(source_keys, "us_nrol_151")
        elif "falcon 9" in text or "spacex" in text:
            vehicle_context = "Falcon 9 has a clear national security launch pedigree in official U.S. mission material."
            add_source(source_keys, "us_nrol_87")
        elif "atlas v" in text:
            vehicle_context =
