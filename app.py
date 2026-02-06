import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Trading Replay",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------
# CUSTOM CSS (BASED ON YOUR LIKED VERSION)
# -------------------------------------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: #e6e6e6;
}

.card {
    background-color: #161b22;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    border: 1px solid #262730;
}

.header {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 8px;
}

.subtle {
    color: #9aa0a6;
    font-size: 13px;
}

.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
}

.initiative { background-color: #1f6feb; }
.rotational { background-color: #6e7681; }

.long { background-color: #2ea043; }
.short { background-color: #f85149; }

.rr-good {
    color: #2ea043;
    font-weight: 600;
}

.rr-bad {
    color: #f85149;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# SESSION STATE INIT
# -------------------------------------------------
defaults = {
    "df": None,
    "index": 0,
    "position": None,
    "manual_trades": [],
    "auto_trades": [],
    "confirm_delete": None,
    "symbol": "AAPL",
    "timeframe": "5m"
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------------------------------
# SIDEBAR (YOU LIKED THIS STRUCTURE)
# -------------------------------------------------
with st.sidebar:
    st.markdown("## 📊 Symbol")

    st.session_state.symbol = st.text_input(
        "Search symbol",
        st.session_state.symbol
    )

    st.markdown("""
    <div class="subtle">
    Stocks: AAPL, SPY, NVDA<br>
    FX: EURUSD, GBPUSD<br>
    Crypto: BTCUSD, ETHUSD<br>
    Futures: ES, NQ, CL
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    now = datetime.now()
    st.markdown("## ⏱ Current Time")
    st.write(now.strftime("%A, %b %d"))
    st.write(now.strftime("%H:%M:%S"))

    st.divider()

    day_type = st.selectbox(
        "Day Type",
        ["Initiative", "Rotational"],
        index=0
    )

    badge_class = "initiative" if day_type == "Initiative" else "rotational"
    st.markdown(
        f'<span class="badge {badge_class}">{day_type}</span>',
        unsafe_allow_html=True
    )

# -------------------------------------------------
# DEMO DATA (SAFE, NO API DEPENDENCY)
# -------------------------------------------------
def load_demo_data():
    start = datetime.now().replace(hour=4, minute=0)
    periods = 300
    dates = [start + timedelta(minutes=i) for i in range(periods)]

    base = 100
    prices = base + np.cumsum(np.random.normal(0, 0.15, periods))

    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": prices + np.random.uniform(0.1, 0.4, periods),
        "Low": prices - np.random.uniform(0.1, 0.4, periods),
        "Close": prices + np.random.uniform(-0.1, 0.1, periods),
        "Volume": np.random.randint(500, 2000, periods)
    })
    return df

if st.session_state.df is None:
    st.session_state.df = load_demo_data()

df = st.session_state.df

# -------------------------------------------------
# KEY LEVELS
# -------------------------------------------------
premarket = df[df["Date"].dt.time < time(9, 30)]
rth = df[df["Date"].dt.time >= time(9, 30)]

PMH = premarket["High"].max() if not premarket.empty else None
PML = premarket["Low"].min() if not premarket.empty else None
PDH = df["High"].iloc[:100].max()
PDL = df["Low"].iloc[:100].min()

# -------------------------------------------------
# MAIN LAYOUT
# -------------------------------------------------
st.markdown(f"## {st.session_state.symbol}")

col_left, col_right = st.columns([2, 1])

# -------------------------------------------------
# LEFT: MANUAL REPLAY (UNCHANGED BEHAVIOR)
# -------------------------------------------------
with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="header">🎮 Manual Replay</div>', unsafe_allow_html=True)

    idx = st.session_state.index
    row = df.iloc[idx]

    st.write({
        "Date": row.Date,
        "Open": round(row.Open, 2),
        "High": round(row.High, 2),
        "Low": round(row.Low, 2),
        "Close": round(row.Close, 2)
    })

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("⬅ Previous") and idx > 0:
            st.session_state.index -= 1

    with c2:
        if st.button("Next ➡") and idx < len(df) - 1:
            st.session_state.index += 1

    with c3:
        if st.button("🟢 Buy") and st.session_state.position is None:
            st.session_state.position = {
                "entry_time": row.Date,
                "entry_price": row.Close,
                "note": ""
            }

    with c4:
        if st.button("🔴 Sell") and st.session_state.position:
            trade = st.session_state.position
            trade["exit_time"] = row.Date
            trade["exit_price"] = row.Close
            trade["pnl"] = round(row.Close - trade["entry_price"], 2)
            st.session_state.manual_trades.append(trade)
            st.session_state.position = None

    if st.session_state.position:
        st.session_state.position["note"] = st.text_input(
            "Trade note",
            st.session_state.position["note"]
        )

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------
# RIGHT: KEY LEVELS + AUTOMATED IDEAS
# -------------------------------------------------
with col_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="header">📐 Key Levels</div>', unsafe_allow_html=True)

    st.write({
        "PMH": PMH,
        "PML": PML,
        "PDH": PDH,
        "PDL": PDL
    })

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="header">🤖 Automated Ideas</div>', unsafe_allow_html=True)

    risk = 0.5
    reward = 1.2
    rr = reward / risk

    if rr >= 1:
        rr_class = "rr-good" if rr >= 2 else ""
        st.markdown(
            f"""
            <span class="badge long">LONG</span>
            RR: <span class="{rr_class}">{rr:.2f}</span>
            """,
            unsafe_allow_html=True
        )
    else:
        st.write("No valid setups (RR < 1:1)")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------
# JOURNALS
# -------------------------------------------------
st.divider()
st.markdown("## 📒 Trade Journals")

tab1, tab2 = st.tabs(["Manual", "Automated"])

with tab1:
    if st.session_state.manual_trades:
        df_trades = pd.DataFrame(st.session_state.manual_trades)
        st.dataframe(df_trades, use_container_width=True)
    else:
        st.info("No manual trades yet.")

with tab2:
    if st.session_state.auto_trades:
        df_auto = pd.DataFrame(st.session_state.auto_trades)
        st.dataframe(df_auto, use_container_width=True)
    else:
        st.info("No automated trades yet.")
