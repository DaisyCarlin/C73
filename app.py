import streamlit as st
from datetime import datetime, timezone
import pandas as pd
import requests

st.set_page_config(
    page_title="Signal Console",
    page_icon="◉",
    layout="wide",
)

PAGE_PATHS = {
    "launch": "pages/1_Orbital_Launch_Monitor.py",
    "satellite": "pages/3_Satellite_Activity.py",
    "strategic": "pages/Strategic_Insights.py",
}

LAUNCH_API_URL = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=50"

def safe_text(v):
    return "" if v is None else str(v)

def country_label(code: str) -> str:
    code = safe_text(code).upper()
    mapping = {
        "US": "U.S.",
        "USA": "U.S.",
        "CN": "China",
        "RU": "Russia",
        "GB": "U.K.",
    }
    return mapping.get(code, code if code else "Unknown")

def looks_sensitive(name: str) -> bool:
    text = safe_text(name).lower()
    keywords = [
        "nrol", "nro", "military", "classified", "reconnaissance",
        "surveillance", "missile", "defense"
    ]
    return any(k in text for k in keywords)

@st.cache_data(ttl=300)
def get_launch_data():
    try:
        data = requests.get(LAUNCH_API_URL, timeout=10).json()["results"]
        rows = []
        for i in data:
            rows.append({
                "name": i.get("name"),
                "country": safe_text(i.get("pad", {}).get("location", {}).get("country_code")),
                "sensitive": looks_sensitive(i.get("name"))
            })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_sat_data():
    try:
        identity = st.secrets["SPACE_TRACK_IDENTITY"]
        password = st.secrets["SPACE_TRACK_PASSWORD"]

        login = requests.post(
            "https://www.space-track.org/ajaxauth/login",
            data={"identity": identity, "password": password},
            timeout=10
        )

        data = requests.get(
            "https://www.space-track.org/basicspacedata/query/class/gp/decay_date/null-val/format/json",
            cookies=login.cookies,
            timeout=10
        ).json()

        rows = []
        for r in data[:2000]:
            name = safe_text(r.get("OBJECT_NAME"))
            rows.append({
                "name": name,
                "country": safe_text(r.get("COUNTRY_CODE")),
                "sensitive": any(k in name.upper() for k in ["NROL", "USA", "YAOGAN", "SBIRS"])
            })

        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

# -------------------------
# HIGHLIGHTS
# -------------------------

def build_launch_highlight(df):
    sensitive = df[df["sensitive"] == True]
    if sensitive.empty:
        return None

    top_country = country_label(
        sensitive.groupby("country").size().sort_values(ascending=False).index[0]
    )

    return {
        "title": f"{top_country} has the most sensitive upcoming launches.",
        "lines": [
            "These missions are linked to military or classified payloads.",
            "This suggests state-driven activity rather than routine commercial launches.",
        ],
        "key": "launch",
        "button": "Open Launch Intelligence",
    }

def build_sat_highlight(df):
    sensitive = df[df["sensitive"] == True]
    if sensitive.empty:
        return None

    top_country = country_label(
        sensitive.groupby("country").size().sort_values(ascending=False).index[0]
    )

    return {
        "title": f"{top_country} dominates the sensitive satellite layer.",
        "lines": [
            "A large portion of tracked objects are linked to surveillance or defence systems.",
            "This indicates persistent strategic orbital infrastructure.",
        ],
        "key": "satellite",
        "button": "Open Satellite Watch",
    }

def build_strategic_highlight(launch_df, sat_df):
    launch_sensitive = launch_df[launch_df["sensitive"] == True]
    sat_sensitive = sat_df[sat_df["sensitive"] == True]

    if launch_sensitive.empty or sat_sensitive.empty:
        return None

    launch_country = country_label(
        launch_sensitive.groupby("country").size().sort_values(ascending=False).index[0]
    )
    sat_country = country_label(
        sat_sensitive.groupby("country").size().sort_values(ascending=False).index[0]
    )

    return {
        "title": f"{launch_country} leads sensitive launches, while {sat_country} leads orbital footprint.",
        "lines": [
            "Short-term launch activity and long-term orbital control are not aligned.",
        ],
        "key": "strategic",
        "button": "Open Strategic Insights",
    }

# -------------------------
# UI
# -------------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #07111f, #0d1b2a);
    color: #e8f1fb;
}
.card {
    padding:20px;
    border-radius:16px;
    background: rgba(10,23,37,0.9);
    border:1px solid rgba(130,161,191,0.2);
}
.title {font-size:34px;font-weight:700;}
.subtitle {color:#91a9c3;}
</style>
""", unsafe_allow_html=True)

current_time = datetime.now(timezone.utc).strftime("%d %b %Y • %H:%M UTC")

st.markdown(f"""
<div class="card">
    <div class="title">Signal Console</div>
    <div class="subtitle">Real-time orbital intelligence</div><br>
    System Time: {current_time}
</div>
""", unsafe_allow_html=True)

launch_df = get_launch_data()
sat_df = get_sat_data()

highlights = [
    build_launch_highlight(launch_df),
    build_sat_highlight(sat_df),
    build_strategic_highlight(launch_df, sat_df),
]

highlights = [h for h in highlights if h is not None]

st.markdown("## 🔴 Today's Key Signals")

cols = st.columns(len(highlights))

for col, h in zip(cols, highlights):
    with col:
        lines = "<br>".join([l for l in h["lines"] if l.strip()])

        st.markdown(f"""
        <div class="card">
            <b>{h['title']}</b><br><br>
            {lines}
        </div>
        """, unsafe_allow_html=True)

        st.page_link(PAGE_PATHS[h["key"]], label=h["button"])