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
            .panel-card,
            .signal-card {
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
                text-transform: uppercase;
            }

            .hero-title {
                font-size: 2.2rem;
                line-height: 1.05;
                font-weight: 700;
                margin: 0;
                color: var(--text-main);
            }

            .hero-copy,
            .panel-copy,
            .signal-copy {
                color: var(--text-soft);
                font-size: 0.95rem;
                margin: 0.55rem 0 0 0;
                line-height: 1.5;
            }

            .panel-card {
                padding: 1rem 1rem 0.85rem 1rem;
                margin-bottom: 0.85rem;
            }

            .panel-title {
                font-size: 1rem;
                font-weight: 700;
                color: var(--text-main);
                margin-bottom: 0.25rem;
            }

            .signal-card {
                padding: 1rem 1rem 0.95rem 1rem;
                min-height: 150px;
            }

            .signal-title {
                color: var(--text-main);
                font-size: 1rem;
                font-weight: 700;
                margin-bottom: 0.4rem;
            }

            .signal-main {
                color: var(--text-main);
                font-size: 1.05rem;
                font-weight: 700;
                line-height: 1.45;
                margin-bottom: 0.45rem;
            }

            .signal-why {
                color: #b9d7ee;
                font-size: 0.92rem;
                line-height: 1.55;
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

            .small-note {
                color: var(--text-soft);
                font-size: 0.88rem;
                line-height: 1.5;
                margin-top: 0.2rem;
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


def country_label(code: str) -> str:
    code = safe_text(code).upper()
    mapping = {
        "US": "U.S.",
        "USA": "U.S.",
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
        "UK": "U.K.",
        "GB": "U.K.",
        "FR": "France",
    }
    return mapping.get(code, code if code else "Unknown")


def maybe_prefix_suggestion(text: str) -> str:
    return text if text.endswith(".") else f"{text}."


def render_signal_card(title: str, main_text: str, why_text: str) -> None:
    st.markdown(
        f"""
        <div class="signal-card">
            <div class="signal-title">{title}</div>
            <div class="signal-main">{main_text}</div>
            <div class="signal-why">{why_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    summary_df = summary_df.sort_values(
        ["current_count", "absolute_change", "country"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    return summary_df, current_df, previous_df


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
    )

    summary_df["current_count"] = summary_df["current_count"].fillna(0).astype(int)
    summary_df["sensitive_count"] = summary_df["sensitive_count"].fillna(0).astype(int)
    summary_df["sensitive_share"] = 0.0

    has_current = summary_df["current_count"] > 0
    summary_df.loc[has_current, "sensitive_share"] = (
        summary_df.loc[has_current, "sensitive_count"] / summary_df.loc[has_current, "current_count"]
    ) * 100.0

    top_subcategories = top_value_by_country(events_df, "subcategory")
    summary_df["top_subcategory"] = summary_df["country"].map(top_subcategories).fillna("No objects")

    summary_df = summary_df.sort_values(
        ["current_count", "sensitive_count", "country"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    return summary_df


def build_main_headline(
    show_launches: bool,
    show_satellites: bool,
    launch_summary_df: pd.DataFrame,
    satellite_summary_df: pd.DataFrame,
) -> str:
    if show_launches and not launch_summary_df.empty:
        biggest_increase_df = launch_summary_df[launch_summary_df["absolute_change"] > 0].sort_values(
            ["absolute_change", "pct_change", "current_count", "country"],
            ascending=[False, False, False, True],
        )
        if not biggest_increase_df.empty:
            row = biggest_increase_df.iloc[0]
            if int(row["sensitive_count"]) > 0:
                return (
                    f"{country_label(row['country'])} saw the sharpest rise in launches this month, "
                    f"suggesting a stronger state-linked mission tempo."
                )

    if show_satellites and not satellite_summary_df.empty:
        row = satellite_summary_df.iloc[0]
        return (
            f"{country_label(row['country'])} still has the largest visible satellite footprint, "
            f"indicating the broadest orbital presence in the current view."
        )

    return "No strong signal stands out yet in the current filters."


def build_signal_cards(
    show_launches: bool,
    show_satellites: bool,
    launch_summary_df: pd.DataFrame,
    current_launch_df: pd.DataFrame,
    satellite_summary_df: pd.DataFrame,
) -> list[dict]:
    cards: list[dict] = []

    if show_launches and not launch_summary_df.empty and int(launch_summary_df["current_count"].sum()) > 0:
        current_positive = launch_summary_df[launch_summary_df["current_count"] > 0].copy()

        most_active = current_positive.sort_values(["current_count", "country"], ascending=[False, True]).iloc[0]
        cards.append(
            {
                "title": "Launch leader",
                "main": f"{country_label(most_active['country'])} had the most launches this month.",
                "why": f"This can be linked to stronger short-term launch tempo, driven mainly by {most_active['top_subcategory'].lower()} missions.",
            }
        )

        biggest_increase_df = launch_summary_df[launch_summary_df["absolute_change"] > 0].sort_values(
            ["absolute_change", "pct_change", "current_count", "country"],
            ascending=[False, False, False, True],
        )
        if not biggest_increase_df.empty:
            biggest_increase = biggest_increase_df.iloc[0]
            cards.append(
                {
                    "title": "Fastest launch rise",
                    "main": (
                        f"{country_label(biggest_increase['country'])} added "
                        f"{int(biggest_increase['absolute_change'])} more launches month-on-month."
                    ),
                    "why": (
                        f"This may suggest a higher launch tempo, and can be linked to "
                        f"{biggest_increase['top_subcategory'].lower()} activity."
                    ),
                }
            )

        sensitive_df = current_positive[current_positive["sensitive_count"] > 0].sort_values(
            ["sensitive_share", "sensitive_count", "country"],
            ascending=[False, False, True],
        )
        if not sensitive_df.empty:
            sensitive_leader = sensitive_df.iloc[0]
            cards.append(
                {
                    "title": "Sensitive launch signal",
                    "main": (
                        f"{country_label(sensitive_leader['country'])} has the strongest sensitive-launch picture "
                        f"in the current launch view."
                    ),
                    "why": (
                        f"{sensitive_leader['sensitive_share']:.0f}% of its launches were flagged sensitive, "
                        f"suggesting more state-linked or military-adjacent activity."
                    ),
                }
            )

    if show_satellites and not satellite_summary_df.empty and int(satellite_summary_df["current_count"].sum()) > 0:
        sat_leader = satellite_summary_df.iloc[0]
        cards.append(
            {
                "title": "Largest orbital footprint",
                "main": f"{country_label(sat_leader['country'])} has the biggest tracked satellite footprint.",
                "why": (
                    f"This can be linked to broad orbital presence, led mainly by "
                    f"{safe_text(sat_leader['top_subcategory']).lower()} systems."
                ),
            }
        )

        if len(satellite_summary_df) > 1:
            second = satellite_summary_df.iloc[1]
            cards.append(
                {
                    "title": "Second-largest footprint",
                    "main": f"{country_label(second['country'])} is the next-largest footprint in the current view.",
                    "why": "This suggests the wider orbital picture is concentrated among a small number of major state or state-linked actors.",
                }
            )

        sensitive_sat_df = satellite_summary_df[satellite_summary_df["sensitive_count"] > 0].sort_values(
            ["sensitive_share", "sensitive_count", "country"],
            ascending=[False, False, True],
        )
        if not sensitive_sat_df.empty:
            sat_sensitive = sensitive_sat_df.iloc[0]
            cards.append(
                {
                    "title": "Sensitive satellite concentration",
                    "main": f"{country_label(sat_sensitive['country'])} has the highest sensitive-share in the current footprint.",
                    "why": (
                        f"{sat_sensitive['sensitive_share']:.0f}% of its tracked satellites were marked sensitive, "
                        f"suggesting a more strategic or military-linked orbital layer."
                    ),
                }
            )

    return cards[:5]


def build_changes_bullets(
    show_launches: bool,
    show_satellites: bool,
    launch_summary_df: pd.DataFrame,
    current_launch_df: pd.DataFrame,
    previous_launch_df: pd.DataFrame,
    satellite_summary_df: pd.DataFrame,
) -> list[str]:
    bullets: list[str] = []

    if show_launches:
        launch_current_total = int(current_launch_df.shape[0]) if not current_launch_df.empty else 0
        launch_previous_total = int(previous_launch_df.shape[0]) if not previous_launch_df.empty else 0
        bullets.append(f"Launches this month: {launch_current_total:,} ({launch_current_total - launch_previous_total:+,} vs previous month).")

        if not launch_summary_df.empty and int(launch_summary_df["current_count"].sum()) > 0:
            top_country = launch_summary_df.iloc[0]
            bullets.append(f"Current launch leader: {country_label(top_country['country'])}.")
            biggest_increase_df = launch_summary_df[launch_summary_df["absolute_change"] > 0].sort_values(
                ["absolute_change", "pct_change", "current_count", "country"],
                ascending=[False, False, False, True],
            )
            if not biggest_increase_df.empty:
                mover = biggest_increase_df.iloc[0]
                bullets.append(
                    f"Biggest rise: {country_label(mover['country'])} (+{int(mover['absolute_change'])} launches)."
                )

        sensitive_launches = int(current_launch_df["sensitive"].sum()) if not current_launch_df.empty else 0
        bullets.append(f"Sensitive launches this month: {sensitive_launches:,}.")

    if show_satellites:
        satellite_total = int(satellite_summary_df["current_count"].sum()) if not satellite_summary_df.empty else 0
        bullets.append(f"Tracked satellites in current view: {satellite_total:,}.")

        if not satellite_summary_df.empty:
            sat_leader = satellite_summary_df.iloc[0]
            bullets.append(f"Satellite footprint leader: {country_label(sat_leader['country'])}.")
            sensitive_satellites = int(satellite_summary_df["sensitive_count"].sum())
            bullets.append(f"Sensitive satellites in current view: {sensitive_satellites:,}.")

    return bullets[:5]


def format_top_launch_chart_df(launch_summary_df: pd.DataFrame) -> pd.DataFrame:
    if launch_summary_df.empty or int(launch_summary_df["current_count"].sum()) == 0:
        return pd.DataFrame()

    chart_df = launch_summary_df[launch_summary_df["current_count"] > 0][["country", "current_count"]].head(6).copy()
    chart_df["Country"] = chart_df["country"].map(country_label)
    chart_df["Launches"] = chart_df["current_count"]
    return chart_df[["Country", "Launches"]].set_index("Country")


def format_top_satellite_chart_df(satellite_summary_df: pd.DataFrame) -> pd.DataFrame:
    if satellite_summary_df.empty:
        return pd.DataFrame()

    chart_df = satellite_summary_df[["country", "current_count"]].head(6).copy()
    chart_df["Country"] = chart_df["country"].map(country_label)
    chart_df["Tracked Footprint"] = chart_df["current_count"]
    return chart_df[["Country", "Tracked Footprint"]].set_index("Country")


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
            A simpler read of launch activity and satellite footprint, focused on what changed, who matters, and what that may suggest.
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
    calculate_launch_country_summary(filtered_launch_df, now_utc)
    if not filtered_launch_df.empty
    else (pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
)
satellite_summary_df = (
    calculate_satellite_country_summary(filtered_satellite_df)
    if not filtered_satellite_df.empty
    else pd.DataFrame()
)

if not show_launches and not show_satellites:
    st.info("Select at least one event type in the sidebar.")
    st.stop()

headline = build_main_headline(
    show_launches=show_launches,
    show_satellites=show_satellites,
    launch_summary_df=launch_summary_df,
    satellite_summary_df=satellite_summary_df,
)

st.markdown(
    f"""
    <div class="panel-card">
        <div class="panel-title">Main readout</div>
        <div class="signal-main" style="margin-top:.35rem;">
            {headline}
        </div>
        <div class="small-note">
            Best-effort signals based on recent launch events and live public satellite catalogue data.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

top_metrics = st.columns(4)

launch_current_total = int(current_launch_df.shape[0]) if not current_launch_df.empty else 0
launch_previous_total = int(previous_launch_df.shape[0]) if not previous_launch_df.empty else 0
satellite_total = int(filtered_satellite_df.shape[0]) if not filtered_satellite_df.empty else 0
sensitive_launches = int(current_launch_df["sensitive"].sum()) if show_launches and not current_launch_df.empty else 0
sensitive_satellites = int(filtered_satellite_df["sensitive"].sum()) if show_satellites and not filtered_satellite_df.empty else 0

with top_metrics[0]:
    st.metric(
        "Launches this month",
        f"{launch_current_total:,}" if show_launches else "—",
        delta=f"{launch_current_total - launch_previous_total:+,} vs prev month" if show_launches else None,
    )

with top_metrics[1]:
    st.metric(
        "Sensitive launches",
        f"{sensitive_launches:,}" if show_launches else "—",
    )

with top_metrics[2]:
    st.metric(
        "Tracked satellites",
        f"{satellite_total:,}" if show_satellites else "—",
    )

with top_metrics[3]:
    st.metric(
        "Sensitive satellites",
        f"{sensitive_satellites:,}" if show_satellites else "—",
    )

signal_cards = build_signal_cards(
    show_launches=show_launches,
    show_satellites=show_satellites,
    launch_summary_df=launch_summary_df,
    current_launch_df=current_launch_df,
    satellite_summary_df=satellite_summary_df,
)

if signal_cards:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Key signals</div>
            <div class="panel-copy">
                Short takeaways from the current view.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(len(signal_cards)) if len(signal_cards) <= 3 else st.columns(3)
    for i, card in enumerate(signal_cards):
        with cols[i % len(cols)]:
            render_signal_card(card["title"], card["main"], card["why"])

changes = build_changes_bullets(
    show_launches=show_launches,
    show_satellites=show_satellites,
    launch_summary_df=launch_summary_df,
    current_launch_df=current_launch_df,
    previous_launch_df=previous_launch_df,
    satellite_summary_df=satellite_summary_df,
)

if changes:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">What changed</div>
            <div class="panel-copy">
                The clearest changes in the current view.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for bullet in changes:
        st.markdown(f"- {maybe_prefix_suggestion(bullet)}")

chart_left, chart_right = st.columns(2, gap="large")

with chart_left:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Launch picture</div>
            <div class="panel-copy">
                Current-month launches by country.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    launch_chart_df = format_top_launch_chart_df(launch_summary_df) if show_launches else pd.DataFrame()
    if launch_chart_df.empty:
        st.info("No launch chart available under the current filters.")
    else:
        st.bar_chart(launch_chart_df)

with chart_right:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">Orbital footprint</div>
            <div class="panel-copy">
                Largest currently tracked satellite footprints.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sat_chart_df = format_top_satellite_chart_df(satellite_summary_df) if show_satellites else pd.DataFrame()
    if sat_chart_df.empty:
        st.info("No satellite chart available under the current filters.")
    else:
        st.bar_chart(sat_chart_df)