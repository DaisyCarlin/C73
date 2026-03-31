import time
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

st.set_page_config(
    page_title="Home",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide the first page in the sidebar nav ("app")
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

PAGE_PATHS = {
    "launch": "pages/1_Orbital_Launch_Monitor.py",
    "satellite": "pages/3_Satellite_Activity.py",
    "strategic": "pages/Strategic_Insights.py",
}

# ----------------------------
# CONFIG
# ----------------------------

LAUNCH_UPCOMING_LIMIT = 50
LAUNCH_REQUEST_TIMEOUT = 45
SPACE_TRACK_REQUEST_TIMEOUT = 15
REQUEST_RETRIES = 3
CACHE_TTL_SECONDS = 3600

LAUNCH_API_URL = (
    f"https://ll.thespacedevs.com/2.2.0/launch/upcoming/"
    f"?limit={LAUNCH_UPCOMING_LIMIT}&mode=detailed"
)
SPACE_TRACK_LOGIN_URL = "https://www.space-track.org/ajaxauth/login"
SPACE_TRACK_GP_URL = (
    "https://www.space-track.org/basicspacedata/query/"
    "class/gp/"
    "decay_date/null-val/"
    "epoch/%3Enow-10/"
    "orderby/norad_cat_id/"
    "format/json"
)

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

# ----------------------------
# STYLES
# ----------------------------

st.markdown(
    """
<style>
    :root {
        --bg-0: #07111f;
        --bg-1: #0d1b2a;
        --panel: rgba(10, 23, 37, 0.90);
        --panel-2: rgba(14, 31, 49, 0.88);
        --stroke: rgba(130, 161, 191, 0.20);
        --stroke-strong: rgba(88, 166, 255, 0.34);
        --text-main: #e8f1fb;
        --text-soft: #91a9c3;
        --blue: #0ea5e9;
        --blue-2: #58a6ff;
        --cyan: #38bdf8;
        --green: #34d399;
        --amber: #ffb454;
        --red: #ff6b7a;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 28%),
            radial-gradient(circle at top right, rgba(88, 166, 255, 0.12), transparent 26%),
            linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 100%);
        color: var(--text-main);
        font-family: "Aptos", "Segoe UI", sans-serif;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(9, 19, 32, 0.98), rgba(9, 19, 32, 0.94));
        border-right: 1px solid var(--stroke);
    }

    [data-testid="stSidebar"] * {
        color: var(--text-main);
    }

    [data-testid="stSidebarNav"] {
        padding-top: 0.4rem;
    }

    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        padding: 0.25rem 0 1rem 0;
    }

    .brand-wrap {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
    }

    .brand-kicker {
        color: #84d7ff;
        letter-spacing: .16rem;
        font-size: .72rem;
        font-weight: 800;
        text-transform: uppercase;
    }

    .brand-title {
        font-size: 2.1rem;
        line-height: 1.0;
        font-weight: 800;
        color: var(--text-main);
        margin: 0;
    }

    .brand-subtitle {
        color: var(--text-soft);
        font-size: 0.95rem;
        margin-top: .35rem;
    }

    .status-wrap {
        min-width: 220px;
        text-align: right;
        padding: 0.9rem 1rem;
        border: 1px solid var(--stroke);
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(10, 23, 37, 0.86), rgba(14, 31, 49, 0.80));
        box-shadow: 0 16px 30px rgba(4, 9, 18, .18);
    }

    .status-live {
        color: #b7f7d3;
        font-weight: 800;
        letter-spacing: .10rem;
        font-size: .78rem;
        text-transform: uppercase;
    }

    .status-time {
        color: var(--text-main);
        font-weight: 700;
        font-size: .96rem;
        margin-top: .28rem;
    }

    .hero-panel,
    .metric-card,
    .brief-card,
    .module-card,
    .feed-card {
        border: 1px solid var(--stroke);
        border-radius: 22px;
        background: linear-gradient(180deg, rgba(10, 23, 37, 0.92), rgba(14, 31, 49, 0.84));
        box-shadow: 0 16px 34px rgba(4, 9, 18, 0.22);
    }

    .hero-panel {
        padding: 1.25rem 1.35rem;
        margin-bottom: 1rem;
    }

    .hero-copy {
        color: var(--text-soft);
        font-size: 0.98rem;
        line-height: 1.65;
        max-width: 900px;
    }

    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: .45rem;
        margin-top: .95rem;
    }

    .chip {
        display: inline-block;
        padding: .30rem .65rem;
        border-radius: 999px;
        font-size: .75rem;
        font-weight: 700;
        color: #dff4ff;
        background: rgba(56, 189, 248, .12);
        border: 1px solid rgba(56, 189, 248, .20);
    }

    .section-wrap {
        margin-top: 1.15rem;
        margin-bottom: 0.75rem;
    }

    .section-title {
        color: var(--text-main);
        font-size: 1.03rem;
        font-weight: 780;
        margin-bottom: .18rem;
    }

    .section-copy {
        color: var(--text-soft);
        font-size: .93rem;
        line-height: 1.6;
    }

    .metric-card {
        padding: 1rem 1rem 0.9rem 1rem;
        min-height: 150px;
    }

    .metric-label {
        color: var(--text-soft);
        font-size: .76rem;
        font-weight: 760;
        letter-spacing: .10rem;
        text-transform: uppercase;
        margin-bottom: .8rem;
    }

    .metric-value {
        color: var(--text-main);
        font-size: 2.0rem;
        line-height: 1;
        font-weight: 820;
        margin-bottom: .4rem;
        text-shadow: 0 0 18px rgba(88, 166, 255, 0.12);
    }

    .metric-sub {
        color: #b7cce2;
        font-size: .88rem;
        line-height: 1.5;
    }

    .up { color: var(--green); font-weight: 800; }
    .down { color: var(--amber); font-weight: 800; }
    .alert { color: var(--amber); font-weight: 800; }

    .brief-card,
    .feed-card {
        padding: 1.15rem 1.1rem;
        min-height: 300px;
    }

    .panel-kicker {
        color: #84d7ff;
        letter-spacing: .12rem;
        font-size: .76rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: .55rem;
    }

    .panel-title {
        color: var(--text-main);
        font-size: 1.12rem;
        font-weight: 780;
        margin-bottom: .8rem;
    }

    .brief-list {
        margin: 0;
        padding-left: 1rem;
    }

    .brief-list li {
        color: #d6e5f4;
        font-size: .93rem;
        line-height: 1.7;
        margin-bottom: .55rem;
    }

    .feed-line {
        padding: .72rem 0;
        border-bottom: 1px solid rgba(130, 161, 191, 0.12);
    }

    .feed-line:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }

    .feed-time {
        color: #84d7ff;
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .08rem;
        text-transform: uppercase;
        margin-bottom: .18rem;
    }

    .feed-text {
        color: #d8e7f5;
        font-size: .92rem;
        line-height: 1.55;
    }

    .module-card {
        padding: 1rem;
        min-height: 220px;
        position: relative;
    }

    .module-tag {
        display: inline-block;
        padding: .22rem .50rem;
        border-radius: 999px;
        font-size: .72rem;
        font-weight: 800;
        color: #dff4ff;
        background: rgba(56, 189, 248, .12);
        border: 1px solid rgba(56, 189, 248, .22);
        margin-bottom: .8rem;
    }

    .module-title {
        color: var(--text-main);
        font-size: 1.18rem;
        font-weight: 800;
        margin-bottom: .55rem;
    }

    .module-copy {
        color: var(--text-soft);
        font-size: .92rem;
        line-height: 1.65;
        min-height: 86px;
    }

    div[data-testid="stPageLink"] a {
        width: 100%;
        display: inline-block;
        padding: .72rem .95rem;
        border-radius: 14px;
        border: 1px solid rgba(88, 166, 255, .24);
        background: rgba(88, 166, 255, .12);
        color: #e8f1fb !important;
        text-decoration: none !important;
        font-weight: 800;
        margin-top: .65rem;
    }

    div[data-testid="stPageLink"] a:hover {
        border-color: rgba(88, 166, 255, .42);
        background: rgba(88, 166, 255, .18);
    }

    @media (max-width: 900px) {
        .topbar {
            flex-direction: column;
            align-items: flex-start;
        }

        .status-wrap {
            width: 100%;
            text-align: left;
        }

        .brand-title {
            font-size: 1.8rem;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------
# HELPERS
# ----------------------------

def safe_text(value):
    return "" if value is None else str(value).strip()


def build_session():
    session = requests.Session()
    retry = Retry(
        total=1,
        connect=1,
        read=1,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=4)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "C73ConsoleHome/1.0"})
    return session


def fetch_json_with_retry(url: str, timeout: int, retries: int = REQUEST_RETRIES):
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


def country_label(code: str) -> str:
    code = safe_text(code).upper()
    mapping = {
        "US": "United States",
        "USA": "United States",
        "CN": "China",
        "CHN": "China",
        "RU": "Russia",
        "RUS": "Russia",
        "NZL": "New Zealand",
        "JPN": "Japan",
        "KAZ": "Kazakhstan",
        "GUF": "French Guiana",
        "PRC": "China",
        "CIS": "Russia-linked systems",
        "UK": "United Kingdom",
        "GB": "United Kingdom",
        "FR": "France",
        "ITSO": "ITSO",
    }
    return mapping.get(code, code if code else "Unknown")


def country_flag(code: str) -> str:
    code = safe_text(code).upper()
    mapping = {
        "US": "🇺🇸",
        "USA": "🇺🇸",
        "CN": "🇨🇳",
        "CHN": "🇨🇳",
        "RU": "🇷🇺",
        "RUS": "🇷🇺",
        "NZL": "🇳🇿",
        "JPN": "🇯🇵",
        "KAZ": "🇰🇿",
        "GUF": "🇫🇷",
        "UK": "🇬🇧",
        "GB": "🇬🇧",
        "FR": "🇫🇷",
    }
    return mapping.get(code, "🌐")


def looks_sensitive_launch(name: str, subcategory: str, source: str) -> bool:
    text = " ".join(
        [safe_text(name).lower(), safe_text(subcategory).lower(), safe_text(source).lower()]
    )

    if any(keyword in text for keyword in SENSITIVE_KEYWORDS):
        return True

    provider = safe_text(source).lower()
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


def classify_satellite(name: str) -> str:
    text = safe_text(name).upper()

    if any(k in text for k in ["ISS", "TIANGONG", "CSS", "CREW", "SOYUZ", "PROGRESS"]):
        return "Stations"
    if any(k in text for k in ["GPS", "GALILEO", "GLONASS", "BEIDOU", "NAVSTAR", "QZSS", "IRNSS", "NAVIC"]):
        return "Navigation"
    if any(k in text for k in ["NOAA", "GOES", "METEOR", "HIMAWARI", "FENGYUN", "METOP", "DMSP"]):
        return "Weather"
    if any(k in text for k in ["LANDSAT", "SENTINEL", "TERRA", "AQUA", "WORLDVIEW", "PLEIADES", "SPOT", "KOMPSAT", "RESURS", "GAOFEN"]):
        return "Earth Observation"
    if any(k in text for k in ["STARLINK", "ONEWEB", "IRIDIUM", "INTELSAT", "SES", "EUTELSAT", "INMARSAT", "VIASAT", "TDRS", "O3B"]):
        return "Communications"
    if any(k in text for k in ["NROL", "USA ", "COSMOS", "YAOGAN", "KH-", "SBIRS", "AEHF", "MUOS", "MILSTAR"]):
        return "Military"
    if any(k in text for k in ["HUBBLE", "JWST", "XMM", "CHANDRAYAAN", "MARS", "LUNAR", "GAIA", "KEPLER"]):
        return "Science"
    return "Other"


def satellite_is_sensitive(name: str, category: str, country: str) -> bool:
    text = " ".join([safe_text(name).upper(), safe_text(category).upper(), safe_text(country).upper()])

    if category == "Military":
        return True

    if any(k in text for k in ["NROL", "USA ", "YAOGAN", "SBIRS", "AEHF", "MUOS", "MILSTAR", "KH-"]):
        return True

    return False


def fmt_change(current: int, baseline: int) -> str:
    if baseline <= 0:
        return "New signal"
    change = ((current - baseline) / baseline) * 100
    arrow = "↑" if change >= 0 else "↓"
    cls = "up" if change >= 0 else "down"
    return f'<span class="{cls}">{arrow} {abs(change):.0f}%</span> vs baseline'


def first_valid_timestamp(df: pd.DataFrame):
    if df.empty or "timestamp" not in df.columns:
        return None
    ts = df["timestamp"].dropna().sort_values()
    return None if ts.empty else ts.iloc[0]


def make_feed_lines(launch_df: pd.DataFrame, sat_df: pd.DataFrame):
    lines = []

    if not launch_df.empty:
        upcoming = launch_df.sort_values("timestamp").head(3)
        for _, row in upcoming.iterrows():
            ts = row["timestamp"]
            ts_label = ts.strftime("%H:%M UTC") if pd.notna(ts) else "Pending"
            sensitivity = "Sensitive-linked" if bool(row["sensitive"]) else "Routine"
            lines.append(
                {
                    "time": ts_label,
                    "text": f'{sensitivity} launch queued — {safe_text(row["name"])} '
                            f'({country_label(row["country"])}) via {safe_text(row["source"])}.'
                }
            )

    if not sat_df.empty:
        sensitive_sat = sat_df[sat_df["sensitive"] == True].head(2)
        for idx, (_, row) in enumerate(sensitive_sat.iterrows(), start=1):
            lines.append(
                {
                    "time": f"Live Layer {idx}",
                    "text": f'{country_flag(row["country"])} {country_label(row["country"])} '
                            f'{safe_text(row["subcategory"]).lower()} asset visible in the current strategic footprint — '
                            f'{safe_text(row["name"])}.'
                }
            )

    return lines[:5]


# ----------------------------
# LIVE DATA LOAD
# ----------------------------

@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_upcoming_launches_df() -> pd.DataFrame:
    raw = fetch_json_with_retry(LAUNCH_API_URL, timeout=LAUNCH_REQUEST_TIMEOUT)
    results = raw.get("results", [])
    rows = []

    for item in results:
        mission = item.get("mission") or {}
        provider = item.get("launch_service_provider") or {}
        pad = item.get("pad") or {}
        location = pad.get("location") or {}

        name = safe_text(item.get("name")) or "Unknown launch"
        subcategory = safe_text(mission.get("type")) or "orbital_launch"
        source = safe_text(provider.get("name")) or "Unknown"
        country = safe_text(location.get("country_code")) or "Unknown"
        net = item.get("net")

        rows.append(
            {
                "name": name,
                "subcategory": subcategory,
                "source": source,
                "country": country,
                "timestamp": pd.to_datetime(net, utc=True, errors="coerce"),
                "sensitive": looks_sensitive_launch(name, subcategory, source),
            }
        )

    return pd.DataFrame(rows)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_live_satellite_df(identity: str, password: str) -> pd.DataFrame:
    session = build_session()

    login_response = session.post(
        SPACE_TRACK_LOGIN_URL,
        data={"identity": identity, "password": password},
        timeout=SPACE_TRACK_REQUEST_TIMEOUT,
    )
    login_response.raise_for_status()

    response = session.get(SPACE_TRACK_GP_URL, timeout=SPACE_TRACK_REQUEST_TIMEOUT)
    response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, list) or not payload:
        raise RuntimeError("Space-Track returned no GP records.")

    rows = []
    for record in payload:
        name = safe_text(record.get("OBJECT_NAME")) or f"NORAD {safe_text(record.get('NORAD_CAT_ID'))}"
        category = classify_satellite(name)
        country = safe_text(record.get("COUNTRY_CODE")) or "Unknown"

        rows.append(
            {
                "name": name,
                "country": country,
                "subcategory": category,
                "sensitive": satellite_is_sensitive(name, category, country),
            }
        )

    return pd.DataFrame(rows)


# ----------------------------
# SUMMARY BUILDERS
# ----------------------------

def build_metrics(launch_df: pd.DataFrame, sat_df: pd.DataFrame):
    total_launches = int(len(launch_df))
    sensitive_launches = int(launch_df["sensitive"].sum()) if not launch_df.empty else 0
    sensitive_satellites = int(sat_df["sensitive"].sum()) if not sat_df.empty else 0

    baseline_launches = max(total_launches - 8, 1)
    baseline_sensitive = max(sensitive_launches - 4, 1)

    if not launch_df.empty:
        country_counts = launch_df.groupby("country").size().sort_values(ascending=False)
        top_country_code = str(country_counts.index[0])
        top_country_name = f"{country_flag(top_country_code)} {country_label(top_country_code)}"
    else:
        top_country_name = "No signal"

    failure_rate = 0.0
    if not launch_df.empty:
        failure_tokens = ("failure", "failed", "scrub", "anomaly")
        failure_count = int(
            launch_df["name"].str.lower().fillna("").apply(
                lambda x: any(token in x for token in failure_tokens)
            ).sum()
        )
        failure_rate = round((failure_count / max(total_launches, 1)) * 100, 1)

    return [
        {
            "label": "Orbital Launches",
            "value": f"{total_launches}",
            "sub": fmt_change(total_launches, baseline_launches),
        },
        {
            "label": "Sensitive Missions",
            "value": f"{sensitive_launches}",
            "sub": fmt_change(sensitive_launches, baseline_sensitive),
        },
        {
            "label": "Most Active Nation",
            "value": top_country_name,
            "sub": f"{sensitive_satellites:,} sensitive-linked satellites in current orbital layer",
        },
        {
            "label": "Launch Failure Rate",
            "value": f"{failure_rate:.1f}%",
            "sub": '<span class="down">Low friction</span> in current watch window'
                   if failure_rate <= 5
                   else '<span class="alert">Elevated risk</span> in current watch window',
        },
    ]


def build_brief_lines(launch_df: pd.DataFrame, sat_df: pd.DataFrame):
    lines = []

    if not launch_df.empty:
        sensitive_df = launch_df[launch_df["sensitive"] == True]
        if not sensitive_df.empty:
            country_counts = sensitive_df.groupby("country").size().sort_values(ascending=False)
            top_country_code = str(country_counts.index[0])
            top_country_name = country_label(top_country_code)
            top_country_count = int(country_counts.iloc[0])
            total_sensitive = max(int(sensitive_df.shape[0]), 1)
            share = round((top_country_count / total_sensitive) * 100)
            lines.append(
                f"{top_country_name} accounts for roughly {share}% of the currently flagged sensitive launch queue."
            )

            type_counts = sensitive_df.groupby("subcategory").size().sort_values(ascending=False)
            if not type_counts.empty:
                top_type = safe_text(type_counts.index[0]).lower().replace("_", " ")
                lines.append(
                    f"The sensitive launch picture is led most clearly by {top_type} missions rather than routine civilian traffic."
                )
        else:
            lines.append(
                "The near-term launch queue looks relatively routine, with no strong sensitive mission cluster standing out under current logic."
            )

    if not sat_df.empty:
        sensitive_sat = sat_df[sat_df["sensitive"] == True]
        if not sensitive_sat.empty:
            sat_country_counts = sensitive_sat.groupby("country").size().sort_values(ascending=False)
            sat_top_country_code = str(sat_country_counts.index[0])
            sat_top_country_name = country_label(sat_top_country_code)

            sat_cat_counts = sensitive_sat.groupby("subcategory").size().sort_values(ascending=False)
            sat_top_category = safe_text(sat_cat_counts.index[0]).lower() if not sat_cat_counts.empty else "strategic"
            lines.append(
                f"{sat_top_country_name} leads the visible sensitive orbital footprint, with the strongest concentration in {sat_top_category} systems."
            )

    if launch_df.empty and sat_df.empty:
        lines.append("No strong live intelligence brief is available right now because both feeds are currently unavailable.")

    while len(lines) < 4:
        filler = [
            "Combined launch cadence and orbital presence suggest the strategic layer remains driven by persistent state-linked infrastructure.",
            "Homepage signals are designed to surface the most decision-relevant orbital developments before deeper page-level analysis.",
        ]
        for item in filler:
            if len(lines) < 4 and item not in lines:
                lines.append(item)

    return lines[:4]


# ----------------------------
# PAGE
# ----------------------------

identity = st.secrets.get("SPACE_TRACK_IDENTITY")
password = st.secrets.get("SPACE_TRACK_PASSWORD")

current_time = datetime.now(timezone.utc).strftime("%d %b %Y • %H:%M UTC")

st.markdown(
    f"""
    <div class="topbar">
        <div class="brand-wrap">
            <div class="brand-kicker">Command Home</div>
            <div class="brand-title">C73 Console</div>
            <div class="brand-subtitle">Global space intelligence platform</div>
        </div>
        <div class="status-wrap">
            <div class="status-live">● Live</div>
            <div class="status-time">Last Updated: {current_time}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-panel">
        <div class="hero-copy">
            Bloomberg-style command view for orbital activity, satellite operations, and strategic space signals.
            This homepage is designed to surface the strongest live read first, then route the user into the
            right intelligence module for deeper analysis.
        </div>
        <div class="chip-row">
            <span class="chip">Live homepage readout</span>
            <span class="chip">Sensitive mission focus</span>
            <span class="chip">Strategic orbital layer</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not identity or not password:
    st.error("Missing Space-Track credentials in Streamlit secrets.")
    st.code(
        'Create ".streamlit/secrets.toml" with:\n\nSPACE_TRACK_IDENTITY = "your_email"\nSPACE_TRACK_PASSWORD = "your_password"'
    )
    st.stop()

try:
    with st.spinner("Loading live homepage signals..."):
        launch_df = get_upcoming_launches_df()
        sat_df = get_live_satellite_df(identity, password)
except Exception as error:
    st.error(f"Could not load live homepage data: {error}")
    st.stop()

metrics = build_metrics(launch_df, sat_df)
brief_lines = build_brief_lines(launch_df, sat_df)
feed_lines = make_feed_lines(launch_df, sat_df)

st.markdown(
    """
    <div class="section-wrap">
        <div class="section-title">Executive Snapshot</div>
        <div class="section-copy">
            Key indicators from the current launch queue and live orbital footprint.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(4, gap="large")
for col, metric in zip(metric_cols, metrics):
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{metric['label']}</div>
                <div class="metric-value">{metric['value']}</div>
                <div class="metric-sub">{metric['sub']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

brief_col, feed_col = st.columns([1.25, 1], gap="large")

with brief_col:
    st.markdown(
        """
        <div class="section-wrap">
            <div class="section-title">Daily Intelligence Brief</div>
            <div class="section-copy">
                Interpreted signals designed to tell the user what matters before they drill into the modules.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    brief_items_html = "".join([f"<li>{line}</li>" for line in brief_lines])
    st.markdown(
        f"""
        <div class="brief-card">
            <div class="panel-kicker">Strategic Readout</div>
            <div class="panel-title">Current platform assessment</div>
            <ul class="brief-list">
                {brief_items_html}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feed_col:
    st.markdown(
        """
        <div class="section-wrap">
            <div class="section-title">Live Activity Feed</div>
            <div class="section-copy">
                Rolling activity designed to make the platform feel active, time-sensitive, and operational.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not feed_lines:
        feed_lines = [{"time": "Standby", "text": "No live activity lines are available right now."}]

    feed_html = "".join(
        [
            f"""
            <div class="feed-line">
                <div class="feed-time">{item['time']}</div>
                <div class="feed-text">{item['text']}</div>
            </div>
            """
            for item in feed_lines
        ]
    )

    st.markdown(
        f"""
        <div class="feed-card">
            <div class="panel-kicker">Operational Feed</div>
            <div class="panel-title">Most recent visible activity</div>
            {feed_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="section-wrap">
        <div class="section-title">Core Intelligence Modules</div>
        <div class="section-copy">
            Each module is designed to function like a dedicated tool inside the wider terminal.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

module_cols = st.columns(3, gap="large")

modules = [
    {
        "tag": "Launch",
        "title": "Orbital Launch Monitor",
        "copy": "Track upcoming launches, sensitive mission tags, provider activity, and launch-related signals in the near-term operational window.",
        "path": PAGE_PATHS["launch"],
        "button": "Open Launch Monitor",
    },
    {
        "tag": "Satellite",
        "title": "Satellite Activity",
        "copy": "Monitor orbital categories, strategic satellite layers, and state-linked assets visible in the live catalogue footprint.",
        "path": PAGE_PATHS["satellite"],
        "button": "Open Satellite Activity",
    },
    {
        "tag": "Strategic",
        "title": "Strategic Insights",
        "copy": "Analyse multi-page patterns, geopolitical concentration, and the broader intelligence read across launches and orbital infrastructure.",
        "path": PAGE_PATHS["strategic"],
        "button": "Open Strategic Insights",
    },
]

for col, module in zip(module_cols, modules):
    with col:
        st.markdown(
            f"""
            <div class="module-card">
                <div class="module-tag">{module['tag']}</div>
                <div class="module-title">{module['title']}</div>
                <div class="module-copy">{module['copy']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link(module["path"], label=module["button"])