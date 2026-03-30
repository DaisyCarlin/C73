from __future__ import annotations

import time
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

st.set_page_config(page_title="Strategic Insights", layout="wide")

# ----------------------------
# CONFIG
# ----------------------------

LAUNCH_RECENT_LIMIT = 150
LAUNCH_REQUEST_TIMEOUT = 45
SPACE_TRACK_REQUEST_TIMEOUT = 15
REQUEST_RETRIES = 3
CACHE_TTL_SECONDS = 3600

LAUNCH_API_URL = f"https://ll.thespacedevs.com/2.2.0/launch/previous/?limit={LAUNCH_RECENT_LIMIT}&mode=detailed"
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


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg-0: #07111f;
                --bg-1: #0d1b2a;
                --stroke: rgba(130, 161, 191, 0.22);
                --text-main: #e8f1fb;
                --text-soft: #91a9c3;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 28%),
                    radial-gradient(circle at top right, rgba(88, 166, 255, 0.12), transparent 26%),
                    linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 100%);
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

            .hero-card,
            .panel-card {
                border: 1px solid var(--stroke);
                background: linear-gradient(180deg, rgba(10, 23, 37, 0.9), rgba(14, 31, 49, 0.82));
                border-radius: 22px;
                box-shadow: 0 16px 34px rgba(4, 9, 18, 0.22);
            }

            .hero-card {
                padding: 1.35rem 1.5rem;
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
                font-size: 2.2rem;
                line-height: 1.05;
                font-weight: 700;
                margin: 0;
                color: var(--text-main);
            }

            .hero-copy,
            .panel-copy {
                color: var(--text-soft);
                font-size: 0.95rem;
                margin: 0.55rem 0 0 0;
                line-height: 1.5;
            }

            .panel-card {
                padding: 1rem 1rem 0.85rem 1rem;
            }

            .panel-title {
                font-size: 1rem;
                font-weight: 700;
                color: var(--text-main);
                margin-bottom: 0.25rem;
            }

            div[data-testid="stMetric"] {
                border: 1px solid var(--stroke);
                border-radius: 18px;
                padding: 0.9rem 1rem;
                background: linear-gradient(180deg, rgba(12, 24, 39, 0.9), rgba(14, 32, 50, 0.76));
                box-shadow: 0 12px 28px rgba(4, 9, 18, 0.2);
            }

            .stDataFrame, div[data-testid="stTable"] {
                border-radius: 18px;
                overflow: hidden;
                border: 1px solid var(--stroke);
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


def fetch_json_with_retry(url: str, timeout: int, retries: int = REQUEST_RETRIES, headers: dict | None = None):
    last_error = None
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            last_error = error
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise last_error


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
    session.headers.update({"User-Agent": "StrategicInsights/1.0"})
    return session


def month_windows(now_utc: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    current_month_start = pd.Timestamp(year=now_utc.year, month=now_utc.month, day=1, tz="UTC")
    next_month_start = current_month_start + pd.offsets.MonthBegin(1)
    previous_month_start = current_month_start - pd.offsets.MonthBegin(1)
    return previous_month_start, current_month_start, next_month_start


def top_value_by_country(events_df: pd.DataFrame, value_col: str) -> pd.Series:
    if events_df.empty or value_col not in events_df.columns:
        return pd.Series(dtype="object")

    grouped = (
        events_df.groupby(["country", value_col], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["country", "count", value_col], ascending=[True, False, True])
    )
    return grouped.drop_duplicates(subset=["country"]).set_index("country")[value_col]


def looks_sensitive_launch(name: str, subcategory: str, source: str) -> bool:
    text = " ".join([safe_text(name).lower(), safe_text(subcategory).lower(), safe_text(source).lower()])

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


# ----------------------------
# LIVE LAUNCH EVENTS
# ----------------------------


def build_launch_events(raw_results) -> pd.DataFrame:
    rows = []

    for item in raw_results:
        mission = item.get("mission") or {}
        rocket = item.get("rocket") or {}
        configuration = rocket.get("configuration") or {}
        provider = item.get("launch_service_provider") or {}
        pad = item.get("pad") or {}
        location = pad.get("location") or {}

        name = safe_text(item.get("name")) or "Unknown launch"
        subcategory = safe_text(mission.get("type")) or "orbital_launch"
        source = safe_text(provider.get("name")) or "Unknown"
        timestamp = item.get("net")
        country = safe_text(location.get("country_code")) or "Unknown"

        rows.append(
            {
                "event_id": f"launch_{safe_text(item.get('id') or name)}_{safe_text(timestamp)}",
                "timestamp": timestamp,
                "country": country,
                "event_type": "launch",
                "subcategory": subcategory,
                "source": source,
                "sensitive": looks_sensitive_launch(name, subcategory, source),
                "name": name,
                "detail": safe_text(configuration.get("name")) or "Unknown rocket",
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_recent_launch_events() -> pd.DataFrame:
    raw = fetch_json_with_retry(LAUNCH_API_URL, timeout=LAUNCH_REQUEST_TIMEOUT)["results"]
    df = build_launch_events(raw)
    if not df.empty:
        df = df.sort_values("timestamp", ascending=False)
    return df


# ----------------------------
# LIVE SATELLITE FOOTPRINT
# ----------------------------


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_live_satellite_events(identity: str, password: str) -> pd.DataFrame:
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
    loaded_at = datetime.now(timezone.utc).isoformat()

    for record in payload:
        name = safe_text(record.get("OBJECT_NAME")) or f"NORAD {safe_text(record.get('NORAD_CAT_ID'))}"
        category = classify_satellite(name)
        country = safe_text(record.get("COUNTRY_CODE")) or "Unknown"

        rows.append(
            {
                "event_id": f"satellite_{safe_text(record.get('NORAD_CAT_ID'))}",
                "timestamp": pd.to_datetime(loaded_at, utc=True, errors="coerce"),
                "country": country,
                "event_type": "satellite",
                "subcategory": category,
                "source": "space-track",
                "sensitive": satellite_is_sensitive(name, category, country),
                "name": name,
                "detail": safe_text(record.get("OBJECT_TYPE")) or "Unknown object type",
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df


# ----------------------------
# FILTERS
# ----------------------------


def filter_events(df: pd.DataFrame, sensitive_only: bool) -> pd.DataFrame:
    filtered = df.copy()
    if sensitive_only and not filtered.empty and "sensitive" in filtered.columns:
        filtered = filtered[filtered["sensitive"]]
    return filtered.reset_index(drop=True)


# ----------------------------
# LAUNCH ANALYTICS
# ----------------------------


def calculate_launch_country_summary(events_df: pd.DataFrame, now_utc: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    previous_month_start, current_month_start, next_month_start = month_windows(now_utc)

    valid_df = events_df.dropna(subset=["timestamp"]).copy()

    current_df = valid_df[
        (valid_df["timestamp"] >= current_month_start) & (valid_df["timestamp"] < next_month_start)
    ].copy()
    previous_df = valid_df[
        (valid_df["timestamp"] >= previous_month_start) & (valid_df["timestamp"] < current_month_start)
    ].copy()

    current_counts = current_df.groupby("country").size().rename("current_count")
    previous_counts = previous_df.groupby("country").size().rename("previous_count")
    all_countries = current_counts.index.union(previous_counts.index)

    summary_df = pd.DataFrame(index=all_countries).reset_index().rename(columns={"index": "country"})
    summary_df["current_count"] = summary_df["country"].map(current_counts).fillna(0).astype(int)
    summary_df["previous_count"] = summary_df["country"].map(previous_counts).fillna(0).astype(int)
    summary_df["absolute_change"] = summary_df["current_count"] - summary_df["previous_count"]

    summary_df["pct_change"] = 0.0
    has_previous = summary_df["previous_count"] > 0
    summary_df.loc[has_previous, "pct_change"] = (
        (summary_df.loc[has_previous, "current_count"] - summary_df.loc[has_previous, "previous_count"])
        / summary_df.loc[has_previous, "previous_count"]
    ) * 100.0
    summary_df.loc[(~has_previous) & (summary_df["current_count"] > 0), "pct_change"] = 100.0

    sensitive_counts = (
        current_df[current_df["sensitive"] == True]
        .groupby("country")
        .size()
        .rename("sensitive_count")
    )
    summary_df["sensitive_count"] = summary_df["country"].map(sensitive_counts).fillna(0).astype(int)

    summary_df["sensitive_share"] = 0.0
    has_current = summary_df["current_count"] > 0
    summary_df.loc[has_current, "sensitive_share"] = (
        summary_df.loc[has_current, "sensitive_count"] / summary_df.loc[has_current, "current_count"]
    ) * 100.0

    current_top_subcategories = top_value_by_country(current_df, "subcategory")
    previous_top_subcategories = top_value_by_country(previous_df, "subcategory")
    summary_df["top_subcategory"] = summary_df["country"].map(current_top_subcategories)
    summary_df["top_subcategory"] = summary_df["top_subcategory"].fillna(summary_df["country"].map(previous_top_subcategories))
    summary_df["top_subcategory"] = summary_df["top_subcategory"].fillna("No events")

    current_top_sources = top_value_by_country(current_df, "source")
    previous_top_sources = top_value_by_country(previous_df, "source")
    summary_df["top_source"] = summary_df["country"].map(current_top_sources)
    summary_df["top_source"] = summary_df["top_source"].fillna(summary_df["country"].map(previous_top_sources))
    summary_df["top_source"] = summary_df["top_source"].fillna("Unknown")

    summary_df["significance"] = "Low"
    summary_df.loc[
        (summary_df["current_count"] >= 10) & (summary_df["pct_change"].abs() >= 10),
        "significance"
    ] = "Medium"
    summary_df.loc[
        (summary_df["current_count"] >= 20) & (summary_df["pct_change"].abs() >= 25),
        "significance"
    ] = "High"

    summary_df = summary_df.sort_values(
        ["current_count", "absolute_change", "country"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    return summary_df, current_df, previous_df


def build_launch_insights(summary_df: pd.DataFrame, current_df: pd.DataFrame) -> list[str]:
    if summary_df.empty or int(summary_df["current_count"].sum()) == 0:
        return ["No current-month launch activity matches the selected filters yet, so no country-level movement stands out."]

    insights: list[str] = []
    current_positive = summary_df[summary_df["current_count"] > 0].copy()

    most_active = current_positive.sort_values(["current_count", "country"], ascending=[False, True]).iloc[0]
    insights.append(
        f"{most_active['country']} recorded the highest launch activity this month with "
        f"{int(most_active['current_count'])} launches, driven mainly by {most_active['top_subcategory']} missions."
    )

    biggest_increase_df = summary_df[summary_df["absolute_change"] > 0].sort_values(
        ["absolute_change", "pct_change", "current_count", "country"],
        ascending=[False, False, False, True],
    )
    if not biggest_increase_df.empty:
        biggest_increase = biggest_increase_df.iloc[0]
        insights.append(
            f"{biggest_increase['country']} shows the strongest month-on-month increase in launch activity, up "
            f"{int(biggest_increase['absolute_change'])} launches "
            f"({float(biggest_increase['pct_change']):+.1f}%), led by {biggest_increase['top_subcategory']} missions."
        )

    high_sensitive_df = current_positive[current_positive["sensitive_share"] >= 50].sort_values(
        ["sensitive_share", "sensitive_count", "country"],
        ascending=[False, False, True],
    )
    if not high_sensitive_df.empty:
        sensitive_leader = high_sensitive_df.iloc[0]
        insights.append(
            f"{sensitive_leader['country']} has the highest sensitive-launch concentration in the current view, with "
            f"{sensitive_leader['sensitive_share']:.0f}% of its logged launch activity marked sensitive."
        )

    high_significance_df = summary_df[summary_df["significance"] == "High"]
    if not high_significance_df.empty:
        highlighted = ", ".join(high_significance_df["country"].head(3).tolist())
        insights.append(
            f"{len(high_significance_df)} countries currently rate as high significance in the launch view, with {highlighted} standing out most clearly."
        )

    return insights[:4]


def format_launch_summary_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    if summary_df.empty:
        return summary_df

    display_df = summary_df.copy()
    display_df["pct_change"] = display_df["pct_change"].map(lambda value: f"{value:+.1f}%")
    display_df["sensitive_share"] = display_df["sensitive_share"].map(lambda value: f"{value:.1f}%")
    display_df = display_df.rename(
        columns={
            "country": "Country",
            "current_count": "Current Month",
            "previous_count": "Previous Month",
            "absolute_change": "Absolute Change",
            "pct_change": "Percent Change",
            "sensitive_count": "Sensitive Count",
            "sensitive_share": "Sensitive Share",
            "top_subcategory": "Top Mission Type",
            "top_source": "Top Provider",
            "significance": "Significance",
        }
    )
    return display_df


def format_launch_movers_table(summary_df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    if summary_df.empty:
        return summary_df

    movers_df = summary_df.copy()
    movers_df["movement_size"] = movers_df["absolute_change"].abs()
    movers_df = movers_df.sort_values(
        ["movement_size", "absolute_change", "current_count", "country"],
        ascending=[False, False, False, True],
    ).head(limit)
    movers_df = movers_df.drop(columns=["movement_size"])
    return format_launch_summary_table(movers_df)


# ----------------------------
# SATELLITE ANALYTICS
# ----------------------------


def calculate_satellite_country_summary(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty:
        return pd.DataFrame()

    summary_df = (
        events_df.groupby("country", dropna=False)
        .agg(
            current_count=("event_id", "size"),
            sensitive_count=("sensitive", "sum"),
        )
        .reset_index()
        .rename(columns={"country": "country"})
    )

    summary_df["current_count"] = summary_df["current_count"].fillna(0).astype(int)
    summary_df["sensitive_count"] = summary_df["sensitive_count"].fillna(0).astype(int)
    summary_df["sensitive_share"] = 0.0

    has_current = summary_df["current_count"] > 0
    summary_df.loc[has_current, "sensitive_share"] = (
        summary_df.loc[has_current, "sensitive_count"] / summary_df.loc[has_current, "current_count"]
    ) * 100.0

    top_subcategories = top_value_by_country(events_df, "subcategory")
    top_sources = top_value_by_country(events_df, "source")

    summary_df["top_subcategory"] = summary_df["country"].map(top_subcategories).fillna("No objects")
    summary_df["top_source"] = summary_df["country"].map(top_sources).fillna("Unknown")

    summary_df = summary_df.sort_values(
        ["current_count", "sensitive_count", "country"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    return summary_df


def build_satellite_insights(summary_df: pd.DataFrame) -> list[str]:
    if summary_df.empty or int(summary_df["current_count"].sum()) == 0:
        return ["No satellite records match the selected filters in the current footprint view."]

    insights: list[str] = []

    most_active = summary_df.sort_values(["current_count", "country"], ascending=[False, True]).iloc[0]
    insights.append(
        f"{most_active['country']} currently has the largest tracked orbital footprint in this view, with "
        f"{int(most_active['current_count'])} satellites, led mainly by {most_active['top_subcategory']} systems."
    )

    high_sensitive_df = summary_df[summary_df["sensitive_share"] >= 50].sort_values(
        ["sensitive_share", "sensitive_count", "country"],
        ascending=[False, False, True],
    )
    if not high_sensitive_df.empty:
        sensitive_leader = high_sensitive_df.iloc[0]
        insights.append(
            f"{sensitive_leader['country']} has the highest sensitive-satellite concentration in the current footprint, with "
            f"{sensitive_leader['sensitive_share']:.0f}% of tracked objects marked sensitive."
        )

    if len(summary_df) > 1:
        second = summary_df.iloc[1]
        insights.append(
            f"Behind {most_active['country']}, the next largest currently tracked orbital footprint belongs to "
            f"{second['country']} with {int(second['current_count'])} satellites."
        )

    top_category_counts = (
        summary_df.groupby("top_subcategory")
        .size()
        .reset_index(name="country_count")
        .sort_values(["country_count", "top_subcategory"], ascending=[False, True])
    )
    if not top_category_counts.empty:
        category_leader = top_category_counts.iloc[0]
        insights.append(
            f"{category_leader['top_subcategory']} is the most common leading satellite category across the currently tracked countries in this view."
        )

    return insights[:4]


def format_satellite_summary_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    if summary_df.empty:
        return summary_df

    display_df = summary_df.copy()
    display_df["sensitive_share"] = display_df["sensitive_share"].map(lambda value: f"{value:.1f}%")
    display_df = display_df.rename(
        columns={
            "country": "Country",
            "current_count": "Tracked Satellites",
            "sensitive_count": "Sensitive Count",
            "sensitive_share": "Sensitive Share",
            "top_subcategory": "Top Satellite Category",
            "top_source": "Source",
        }
    )
    return display_df


# ----------------------------
# PAGE
# ----------------------------

inject_styles()

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-kicker">COUNTRY-LEVEL ANALYST VIEW</div>
        <h1 class="hero-title">Strategic Insights</h1>
        <p class="hero-copy">
            Compare launches month-by-month, and view satellites as a current-state orbital footprint.
            Switch between rocket-only, satellite-only, or both whenever you want.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

identity = st.secrets.get("SPACE_TRACK_IDENTITY")
password = st.secrets.get("SPACE_TRACK_PASSWORD")

if not identity or not password:
    st.error("Missing Space-Track credentials in Streamlit secrets.")
    st.code(
        'Create ".streamlit/secrets.toml" with:\n\nSPACE_TRACK_IDENTITY = "your_email"\nSPACE_TRACK_PASSWORD = "your_password"'
    )
    st.stop()

try:
    launch_df = get_recent_launch_events()
    satellite_df = get_live_satellite_events(identity, password)
    data_error = None
except Exception as error:
    launch_df = pd.DataFrame()
    satellite_df = pd.DataFrame()
    data_error = str(error)

if data_error:
    st.error(f"Could not load live strategic data: {data_error}")
    st.stop()

event_type_options = ["launch", "satellite"]

with st.sidebar:
    st.markdown("### Insight Filters")
    selected_event_types = st.multiselect(
        "Event types",
        options=event_type_options,
        default=event_type_options,
        help="Choose rocket only, satellite only, or keep both selected.",
    )
    sensitive_only = st.toggle(
        "Sensitive only",
        value=False,
        help="Only include activity marked as sensitive.",
    )

show_launches = "launch" in selected_event_types
show_satellites = "satellite" in selected_event_types

filtered_launch_df = filter_events(launch_df, sensitive_only) if show_launches else pd.DataFrame()
filtered_satellite_df = filter_events(satellite_df, sensitive_only) if show_satellites else pd.DataFrame()

now_utc = pd.Timestamp.now(tz="UTC")
previous_month_start, current_month_start, next_month_start = month_windows(now_utc)

launch_summary_df, current_launch_df, previous_launch_df = (
    calculate_launch_country_summary(filtered_launch_df, now_utc) if not filtered_launch_df.empty else (pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
)
satellite_summary_df = calculate_satellite_country_summary(filtered_satellite_df) if not filtered_satellite_df.empty else pd.DataFrame()

loaded_sources = []
if show_launches:
    loaded_sources.append("Launches")
if show_satellites:
    loaded_sources.append("Satellites")

scope_text = (
    "launch activity only" if show_launches and not show_satellites
    else "satellite footprint only" if show_satellites and not show_launches
    else "launch activity and satellite footprint" if show_launches and show_satellites
    else "no active scope"
)

st.caption(
    f"Loaded sources: {', '.join(loaded_sources) if loaded_sources else 'None'} | "
    f"View scope: {scope_text} | "
    f"Launch month window: {current_month_start.strftime('%d %b %Y')} to {next_month_start.strftime('%d %b %Y')} UTC | "
    f"Previous launch month window: {previous_month_start.strftime('%d %b %Y')} to {current_month_start.strftime('%d %b %Y')} UTC"
)

if not show_launches and not show_satellites:
    st.info("Select at least one event type in the sidebar.")
    st.stop()

# ----------------------------
# TOP-LEVEL SUMMARY
# ----------------------------

top_metrics = st.columns(4)

launch_current_total = int(current_launch_df.shape[0]) if not current_launch_df.empty else 0
launch_previous_total = int(previous_launch_df.shape[0]) if not previous_launch_df.empty else 0
satellite_total = int(filtered_satellite_df.shape[0]) if not filtered_satellite_df.empty else 0
satellite_countries = int(satellite_summary_df.shape[0]) if not satellite_summary_df.empty else 0

with top_metrics[0]:
    st.metric(
        "Current Month Launches",
        f"{launch_current_total:,}" if show_launches else "—",
        delta=f"{launch_current_total - launch_previous_total:+,} vs prev month" if show_launches else None,
    )

with top_metrics[1]:
    st.metric(
        "Tracked Satellites Now",
        f"{satellite_total:,}" if show_satellites else "—",
        delta=f"{satellite_countries:,} active countries" if show_satellites else None,
    )

with top_metrics[2]:
    sensitive_launches = int(current_launch_df["sensitive"].sum()) if show_launches and not current_launch_df.empty else 0
    sensitive_satellites = int(filtered_satellite_df["sensitive"].sum()) if show_satellites and not filtered_satellite_df.empty else 0
    st.metric(
        "Sensitive Launches",
        f"{sensitive_launches:,}" if show_launches else "—",
        delta=f"{sensitive_satellites:,} sensitive satellites" if show_satellites else None,
    )

with top_metrics[3]:
    if show_launches and not launch_summary_df.empty:
        largest_launch_country = str(launch_summary_df.iloc[0]["country"])
    else:
        largest_launch_country = "—"

    if show_satellites and not satellite_summary_df.empty:
        largest_sat_country = str(satellite_summary_df.iloc[0]["country"])
    else:
        largest_sat_country = "—"

    summary_label = largest_launch_country if show_launches and not show_satellites else largest_sat_country if show_satellites and not show_launches else "Mixed view"
    summary_delta = None
    if show_launches and show_satellites:
        summary_delta = f"Launch leader: {largest_launch_country} | Satellite leader: {largest_sat_country}"

    st.metric("Strategic Lead", summary_label, delta=summary_delta)

# ----------------------------
# INTERPRETATION NOTES
# ----------------------------

notes = []
if show_launches:
    notes.append("Launch figures are true month-on-month comparisons drawn from recent historical launch events.")
if show_satellites:
    notes.append("Satellite figures are a current-state orbital footprint, not a month-on-month event comparison.")
if show_launches and show_satellites:
    notes.append("The combined view is best read as one strategic page with two different lenses: launch movement and current orbital infrastructure.")
if show_satellites:
    notes.append("Satellite categories are inferred from public naming patterns and public catalogue metadata, so they are indicative rather than definitive mission attribution.")

if notes:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Interpretation Notes</div>
            <div class="panel-copy">
                Read the launch and satellite sections differently: launches are event-driven trends, satellites are current-state footprint.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for note in notes:
        st.markdown(f"- {note}")

# ----------------------------
# LAUNCH SECTION
# ----------------------------

if show_launches:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Launch Strategic Insights</div>
            <div class="panel-copy">
                Month-on-month country comparison based on recent historical launch events.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    launch_insights = build_launch_insights(launch_summary_df, current_launch_df)
    for insight in launch_insights:
        st.markdown(f"- {insight}")

    launch_left, launch_right = st.columns([1.65, 1], gap="large")

    with launch_left:
        st.markdown(
            """
            <div class="panel-card">
                <div class="panel-title">Launch Country Summary</div>
                <div class="panel-copy">
                    Country-level launch totals, month-on-month movement, sensitivity, dominant mission type, dominant provider, and significance.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if launch_summary_df.empty:
            st.info("No launch country summary is available for the current filters and month windows.")
        else:
            st.dataframe(format_launch_summary_table(launch_summary_df), use_container_width=True, hide_index=True)

    with launch_right:
        st.markdown(
            """
            <div class="panel-card">
                <div class="panel-title">Top Launch Countries This Month</div>
                <div class="panel-copy">
                    Current-month launch volume by country.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if launch_summary_df.empty or int(launch_summary_df["current_count"].sum()) == 0:
            st.info("No current-month launch activity is available to chart.")
        else:
            chart_df = launch_summary_df[launch_summary_df["current_count"] > 0][["country", "current_count"]].head(10).copy()
            chart_df = chart_df.rename(columns={"country": "Country", "current_count": "Current Month"})
            st.bar_chart(chart_df.set_index("Country"))

    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Sensitive vs Non-Sensitive Launches</div>
            <div class="panel-copy">
                Compare how much of each country's current-month launch activity is marked sensitive versus routine.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if launch_summary_df.empty or int(launch_summary_df["current_count"].sum()) == 0:
        st.info("No current-month launch sensitivity split is available.")
    else:
        sensitivity_chart_df = launch_summary_df[launch_summary_df["current_count"] > 0][["country", "sensitive_count", "current_count"]].copy()
        sensitivity_chart_df["non_sensitive_count"] = sensitivity_chart_df["current_count"] - sensitivity_chart_df["sensitive_count"]
        sensitivity_chart_df = sensitivity_chart_df[["country", "sensitive_count", "non_sensitive_count"]].set_index("country")
        st.bar_chart(sensitivity_chart_df)

    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Top Launch Providers This Month</div>
            <div class="panel-copy">
                Which launch providers are contributing the most current-month launch activity.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if current_launch_df.empty:
        st.info("No current-month launch provider mix is available.")
    else:
        provider_chart_df = (
            current_launch_df.groupby("source")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(10)
            .set_index("source")
        )
        st.bar_chart(provider_chart_df)

    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Launch Mission-Type Mix This Month</div>
            <div class="panel-copy">
                See how the current-month launch picture breaks down across mission types.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if current_launch_df.empty:
        st.info("No current-month launch mission-type mix is available.")
    else:
        mission_chart_df = (
            current_launch_df.groupby("subcategory")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(10)
            .set_index("subcategory")
        )
        st.bar_chart(mission_chart_df)

    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Launch Movers</div>
            <div class="panel-copy">
                Countries with the largest absolute month-on-month launch movement under the current filters.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if launch_summary_df.empty:
        st.info("No launch movers are available because there are no country comparisons yet.")
    else:
        st.dataframe(format_launch_movers_table(launch_summary_df), use_container_width=True, hide_index=True)

# ----------------------------
# SATELLITE SECTION
# ----------------------------

if show_satellites:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Satellite Strategic Footprint</div>
            <div class="panel-copy">
                Current-state orbital footprint by country and category, based on the live public catalogue snapshot.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    satellite_insights = build_satellite_insights(satellite_summary_df)
    for insight in satellite_insights:
        st.markdown(f"- {insight}")

    sat_left, sat_right = st.columns([1.65, 1], gap="large")

    with sat_left:
        st.markdown(
            """
            <div class="panel-card">
                <div class="panel-title">Satellite Country Summary</div>
                <div class="panel-copy">
                    Current tracked orbital footprint by country, including sensitive-share and dominant satellite category.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if satellite_summary_df.empty:
            st.info("No satellite footprint summary is available for the current filters.")
        else:
            st.dataframe(format_satellite_summary_table(satellite_summary_df), use_container_width=True, hide_index=True)

    with sat_right:
        st.markdown(
            """
            <div class="panel-card">
                <div class="panel-title">Largest Current Orbital Footprints</div>
                <div class="panel-copy">
                    Countries with the largest currently tracked satellite presence in the selected view.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if satellite_summary_df.empty:
            st.info("No satellite footprint chart is available.")
        else:
            sat_chart_df = satellite_summary_df[["country", "current_count"]].head(10).copy()
            sat_chart_df = sat_chart_df.rename(columns={"country": "Country", "current_count": "Tracked Satellites"})
            st.bar_chart(sat_chart_df.set_index("Country"))

    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Sensitive vs Non-Sensitive Satellites</div>
            <div class="panel-copy">
                Compare how much of each country's currently tracked satellite footprint is marked sensitive versus routine.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if satellite_summary_df.empty:
        st.info("No satellite sensitivity split is available.")
    else:
        sat_sensitivity_df = satellite_summary_df[["country", "sensitive_count", "current_count"]].copy()
        sat_sensitivity_df["non_sensitive_count"] = sat_sensitivity_df["current_count"] - sat_sensitivity_df["sensitive_count"]
        sat_sensitivity_df = sat_sensitivity_df[["country", "sensitive_count", "non_sensitive_count"]].set_index("country")
        st.bar_chart(sat_sensitivity_df)

    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Top Satellite Categories</div>
            <div class="panel-copy">
                Which satellite categories dominate the current tracked footprint.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if filtered_satellite_df.empty:
        st.info("No satellite category mix is available.")
    else:
        sat_category_df = (
            filtered_satellite_df.groupby("subcategory")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(10)
            .set_index("subcategory")
        )
        st.bar_chart(sat_category_df)

    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Top Sources</div>
            <div class="panel-copy">
                Source mix for the current satellite footprint view.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if filtered_satellite_df.empty:
        st.info("No satellite source mix is available.")
    else:
        sat_source_df = (
            filtered_satellite_df.groupby("source")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(10)
            .set_index("source")
        )
        st.bar_chart(sat_source_df)