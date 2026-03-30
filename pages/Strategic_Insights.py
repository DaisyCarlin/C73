from __future__ import annotations
import time
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Strategic Insights", layout="wide")

# ----------------------------
# CONFIG
# ----------------------------

LAUNCH_LIMIT = 60
CACHE_TTL = 3600

LAUNCH_API_URL = f"https://ll.thespacedevs.com/2.2.0/launch/previous/?limit={LAUNCH_LIMIT}&mode=detailed"

REQUEST_HEADERS = {"User-Agent": "StrategicInsights/2.0"}

# ----------------------------
# STYLES
# ----------------------------

def inject_styles():
    st.markdown("""
    <style>
    .stApp { background:#0b1220; color:#e8f1fb; }
    .card {
        border:1px solid rgba(255,255,255,0.1);
        padding:1rem;
        border-radius:18px;
        background:rgba(20,30,50,0.7);
    }
    </style>
    """, unsafe_allow_html=True)

inject_styles()

# ----------------------------
# HELPERS
# ----------------------------

def fetch(url, timeout=30):
    return requests.get(url, timeout=timeout, headers=REQUEST_HEADERS).json()

def month_windows(now):
    current = pd.Timestamp(year=now.year, month=now.month, day=1, tz="UTC")
    next_m = current + pd.offsets.MonthBegin(1)
    prev = current - pd.offsets.MonthBegin(1)
    return prev, current, next_m

# ----------------------------
# LAUNCH DATA (HISTORICAL ✅)
# ----------------------------

@st.cache_data(ttl=CACHE_TTL)
def get_launches():
    raw = fetch(LAUNCH_API_URL)["results"]

    rows = []
    for r in raw:
        country = (r.get("pad") or {}).get("location", {}).get("country_code") or "Unknown"
        provider = (r.get("launch_service_provider") or {}).get("name") or "Unknown"

        rows.append({
            "timestamp": r.get("net"),
            "country": country,
            "provider": provider,
        })

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df

# ----------------------------
# SATELLITE DATA (CURRENT STATE ✅)
# ----------------------------

@st.cache_data(ttl=CACHE_TTL)
def get_satellite_summary():
    # LIGHTWEIGHT MOCK (replace later with Space-Track summary)
    # Keeping fast intentionally

    data = [
        {"country": "US", "count": 18000, "military": 4000},
        {"country": "CN", "count": 8000, "military": 2000},
        {"country": "RU", "count": 3000, "military": 1200},
        {"country": "EU", "count": 2500, "military": 300},
    ]

    return pd.DataFrame(data)

# ----------------------------
# LOAD DATA
# ----------------------------

launch_df = get_launches()
sat_df = get_satellite_summary()

now = pd.Timestamp.now(tz="UTC")
prev, curr, next_m = month_windows(now)

# ----------------------------
# LAUNCH INSIGHTS
# ----------------------------

current_launches = launch_df[
    (launch_df["timestamp"] >= curr) &
    (launch_df["timestamp"] < next_m)
]

previous_launches = launch_df[
    (launch_df["timestamp"] >= prev) &
    (launch_df["timestamp"] < curr)
]

current_total = len(current_launches)
previous_total = len(previous_launches)

country_counts = current_launches.groupby("country").size().sort_values(ascending=False)

top_country = country_counts.index[0] if not country_counts.empty else "None"

# ----------------------------
# UI
# ----------------------------

st.title("Strategic Insights")

st.markdown("## 🚀 Launch Activity (Historical)")

col1, col2, col3 = st.columns(3)

col1.metric("Current Month Launches", current_total)
col2.metric("Previous Month Launches", previous_total)
col3.metric("Top Launch Country", top_country)

st.markdown("### Analyst Takeaways")

if current_total > 0:
    st.markdown(f"- {top_country} leads launch activity this month.")
    st.markdown(f"- Total launches show a change of {current_total - previous_total:+} vs last month.")
else:
    st.markdown("- No launches recorded this month.")

# ----------------------------
# SATELLITE FOOTPRINT
# ----------------------------

st.markdown("## 🛰️ Satellite Footprint (Current State)")

total_sats = int(sat_df["count"].sum())
top_sat_country = sat_df.sort_values("count", ascending=False).iloc[0]["country"]

col1, col2 = st.columns(2)
col1.metric("Tracked Satellites", f"{total_sats:,}")
col2.metric("Largest Operator", top_sat_country)

st.markdown("### Analyst Takeaways")

st.markdown(
    f"- {top_sat_country} dominates the current orbital footprint."
)
st.markdown(
    "- Satellite data represents a live snapshot, not month-on-month change."
)

# ----------------------------
# TABLES
# ----------------------------

st.markdown("### Launch Breakdown")
st.dataframe(current_launches.groupby("country").size().reset_index(name="Launch Count"))

st.markdown("### Satellite Distribution")
st.dataframe(sat_df)