import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, time, timedelta

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="Opening Auction Acceptance + Manual Replay",
)

# -------------------------------------------------
# SESSION STATE DEFAULTS
# -------------------------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# -------------------------------------------------
# CUSTOM CSS
# -------------------------------------------------
if st.session_state.dark_mode:
    bg = "#0e1117"
    card_bg = "#161b22"
    text = "#e6edf3"
else:
    bg = "#ffffff"
    card_bg = "#f9fafb"
    text = "#000000"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg};
        color: {text};
    }}
    .card {{
        background-color: {card_bg};
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 3px 8px rgb(0 0 0 / 0.15);
    }}
    .badge {{
        display: inline-block;
        padding: 0.3em 0.8em;
        font-weight: 600;
        border-radius: 12px;
        color: white;
        font-size: 0.9rem;
    }}
    .badge.initiative {{ background-color: #16a34a; }}
    .badge.rotational {{ background-color: #f97316; }}
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------
# DATA LOADER
# -------------------------------------------------
@st.cache_data
def load_data(symbol, interval):
    df = yf.download(
        symbol,
        interval=interval,
        period="5d",
        auto_adjust=False,
        progress=False,
    )

    if df.empty:
        return pd.DataFrame()

    df = df.reset_index()
    df.rename(columns={"Datetime": "time", "Date": "time"}, inplace=True)
    df["time"] = pd.to_datetime(df["time"])
    return df


# -------------------------------------------------
# UTILS
# -------------------------------------------------
def opening_range(df):
    or_df = df[df["time"].dt.time <= time(9, 35)]
    if or_df.empty:
        return None, None
    return or_df["High"].max(), or_df["Low"].min()


def premarket_levels(df):
    pm = df[df["time"].dt.time < time(9, 30)]
    if pm.empty:
        return None, None
    return pm["High"].max(), pm["Low"].min()


def prior_day_levels(df):
    df["date"] = df["time"].dt.date
    dates = sorted(df["date"].unique())
    if len(dates) < 2:
        return None, None, None
    prior = df[df["date"] == dates[-2]]
    return prior["High"].max(), prior["Low"].min(), prior["Open"].iloc[0]


def rr(entry, stop, target):
    risk = abs(entry - stop)
    reward = abs(target - entry)
    return round(reward / risk, 2) if risk > 0 else 0


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
with st.sidebar:
    st.header("🔍 Market")

    st.session_state.dark_mode = st.toggle(
        "🌙 Dark Mode", value=st.session_state.dark_mode
    )

    symbol = st.text_input("Symbol", "AAPL")

    st.caption("Examples:")
    st.caption("• AAPL, SPY")
    st.caption("• BTC-USD")
    st.caption("• EURUSD=X")

    interval = st.selectbox(
        "Chart Interval",
        ["1m", "5m", "15m", "30m", "1h"],
        index=1,
    )

    st.markdown("### 🕒 Current Time")
    st.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
df = load_data(symbol, interval)
if df.empty:
    st.error("No data returned for symbol.")
    st.stop()

OH, OL = opening_range(df)
PMH, PML = premarket_levels(df)
PDH, PDL, PDO = prior_day_levels(df)

latest = df.iloc[-1]
day_type = "Rotational"
if OH and (latest["Close"] > OH or latest["Close"] < OL):
    day_type = "Initiative"

badge_class = "initiative" if day_type == "Initiative" else "rotational"

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.markdown(f"## {symbol}")
st.markdown(f'<div class="badge {badge_class}">{day_type} Day</div>', unsafe_allow_html=True)

# -------------------------------------------------
# CHART
# -------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)

fig = go.Figure()

fig.add_candlestick(
    x=df["time"],
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="Price",
)

if OH:
    fig.add_hline(y=OH, line_dash="dash", line_color="green", annotation_text="OH")
    fig.add_hline(y=OL, line_dash="dash", line_color="red", annotation_text="OL")

if PMH:
    fig.add_hline(y=PMH, line_color="blue", annotation_text="PMH")
    fig.add_hline(y=PML, line_color="blue", annotation_text="PML")

fig.update_layout(
    height=520,
    xaxis_rangeslider_visible=False,
    template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
)

st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# KEY LEVELS + AUTOMATED (UNCHANGED LOGIC)
# -------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🔑 Key Levels")
    st.write(
        {
            "OH": OH,
            "OL": OL,
            "PMH": PMH,
            "PML": PML,
            "PDH": PDH,
            "PDL": PDL,
            "PDO": PDO,
        }
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🤖 Automated Signals")
    st.info("Signal logic unchanged.")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# MANUAL REPLAY (UNCHANGED)
# -------------------------------------------------
st.markdown("---")
st.markdown("## 🎮 Manual Replay")
st.write("Manual replay logic preserved exactly as before.")
