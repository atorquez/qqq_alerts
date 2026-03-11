import streamlit as st
import sys
import os

if "engine_started" not in st.session_state:
    st.session_state.engine_started = False

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "TQQQ"

#st.write("Python version:", sys.version)

# ---------------------------------------------------------
# Ensure Python can find the project root
# ---------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------
import pandas as pd
import numpy as np
import yfinance as yf
from engine_pkg.engine import get_5d_return, decide_ratio

# ---------------------------------------------------------
# Fetch stable 5‑day data (intraday → daily)
# ---------------------------------------------------------
def get_last_5d(ticker):
    df = yf.download(ticker, period="7d", interval="30m")

    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.Series(dtype=float)

    try:
        df_daily = df.resample("1D").last()
    except:
        return pd.Series(dtype=float)

    close = df_daily.get("Close")
    if close is None:
        return pd.Series(dtype=float)

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = pd.to_numeric(close, errors="coerce").dropna()
    if close.empty:
        return pd.Series(dtype=float)

    # Keep simple integer index 0..N-1
    close.index = pd.RangeIndex(start=0, stop=len(close))
    return close

# ---------------------------------------------------------
# SMA10
# ---------------------------------------------------------
def get_sma10(ticker):
    data = yf.download(ticker, period="20d", interval="1d")["Close"].dropna()
    if len(data) < 10:
        return None, None
    sma10 = data.rolling(10).mean().iloc[-1]
    last_close = data.iloc[-1]
    return float(last_close), float(sma10)

# ---------------------------------------------------------
# Page Title
# ---------------------------------------------------------
st.title("📈 Engine Overview (Page 1)")
st.write("This page shows the 5‑day charts, returns, volatility, and the computed TQQQ/SQQQ ratio.")

# ---------------------------------------------------------
# 1. Ticker selection (always visible)
# ---------------------------------------------------------
st.subheader("📈 5‑Day Price + MA5 Chart")
ticker = st.selectbox("Select Ticker", ["TQQQ", "SQQQ"])

# ---------------------------------------------------------
# Run Engine
# ---------------------------------------------------------
if st.button("Run Engine"):
    st.session_state.engine_started = True

    # Now use the selected ticker
    series = get_last_5d(ticker)

    if series.empty:
        st.warning(f"⚠️ Could not load last 5 days of data for {ticker}.")
    else:
        df = pd.DataFrame({"Close": series})
        df["MA5"] = df["Close"].rolling(5).mean()
        df["Day"] = df.index + 1

        import altair as alt

        chart = (
            alt.Chart(df.melt("Day"))
            .mark_line(strokeWidth=2)
            .encode(
                x=alt.X("Day:Q", title="Day", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y(
                    "value:Q",
                    title="Price",
                    scale=alt.Scale(
                        nice=False,       # no rounding to 10s
                        padding=10,       # small breathing room
                        zero=False        # do NOT force y-axis to start at 0
                    )
                ),
                color="variable:N",
                tooltip=["Day", "variable", "value"]
            )
            .properties(height=300)
        )

        st.altair_chart(chart, use_container_width=True)

    # ... rest of engine logic ...

    # ---------------------------------------------------------
    # 2. 5‑Day Returns
    # ---------------------------------------------------------
    st.subheader("📈 5‑Day Returns")

    ret_t, price_t = get_5d_return("TQQQ")
    ret_s, price_s = get_5d_return("SQQQ")

    st.write(f"**TQQQ 5‑day return:** {ret_t:.2f}%")
    st.write(f"**SQQQ 5‑day return:** {ret_s:.2f}%")

    # ---------------------------------------------------------
    # 3. 5‑Day Volatility
    # ---------------------------------------------------------
    st.subheader("📉 5‑Day Volatility")

    def get_vol(ticker):
        data = yf.download(ticker, period="10d", interval="1d")["Close"].dropna()
        return float(np.std(data.pct_change().dropna()))

    vol_t = get_vol("TQQQ")
    vol_s = get_vol("SQQQ")

    st.write(f"**TQQQ volatility:** {vol_t:.2f}%")
    st.write(f"**SQQQ volatility:** {vol_s:.2f}%")

    # ---------------------------------------------------------
    # 4. Ratio Recommendation Panel
    # ---------------------------------------------------------
    st.subheader("📊 Ratio Recommendation")

    w_t, w_s = decide_ratio(ret_t, ret_s, vol_t, vol_s)

    # ---------------------------------------------------------
    # Apply allocation constraints
    # ---------------------------------------------------------
    MAX_WEIGHT = 0.70
    MIN_WEIGHT = 0.30

    if w_t > w_s:
        w_t = MAX_WEIGHT
        w_s = MIN_WEIGHT
    else:
        w_s = MAX_WEIGHT
        w_t = MIN_WEIGHT

    tqqq_pct = round(w_t * 100, 2)
    sqqq_pct = round(w_s * 100, 2)

    # Directional bias
    if w_t > w_s:
        bias = "TQQQ Bias (Bullish)"
    elif w_s > w_t:
        bias = "SQQQ Bias (Bearish)"
    else:
        bias = "Neutral"

    # Signal strength
    strength = abs(w_t - w_s)

    if strength < 0.10:
        signal = "Very Weak"
    elif strength < 0.20:
        signal = "Weak"
    elif strength < 0.35:
        signal = "Moderate"
    else:
        signal = "Strong"

    st.info(f"""
    ### Recommended Split  
    **{tqqq_pct}% TQQQ / {sqqq_pct}% SQQQ**

    ### Directional Bias  
    **{bias}**

    ### Signal Strength  
    **{signal}** (|TQQQ − SQQQ| = {strength:.2f})
    """)

    # ---------------------------------------------------------
    # 5. Trade Decision Panel
    # ---------------------------------------------------------
    st.subheader("📌 Today's Trade Decision")

    no_trade_zone = (0.45 <= w_t <= 0.55)

    t_close, t_sma10 = get_sma10("TQQQ")
    s_close, s_sma10 = get_sma10("SQQQ")

    t_trend_ok = (t_close is not None and t_close > t_sma10)
    s_trend_ok = (s_close is not None and s_close > s_sma10)

    reasons = []

    if no_trade_zone:
        reasons.append("Ratio inside no‑trade zone (weak signal)")

    if not t_trend_ok:
        reasons.append("TQQQ below SMA10 (downtrend)")

    if not s_trend_ok:
        reasons.append("SQQQ below SMA10 (downtrend)")

    trade_allowed = (not no_trade_zone) and (t_trend_ok or s_trend_ok)

    if trade_allowed:
        st.success("✅ **TRADE ALLOWED TODAY**")
    else:
        st.error("❌ **NO TRADE TODAY**")

    st.write("### Why?")
    if reasons:
        for r in reasons:
            st.write(f"- {r}")
    else:
        st.write("- All conditions satisfied.")

# ---------------------------------------------------------
# Key Definitions
# ---------------------------------------------------------
st.markdown("## 📘 Key Definitions")

st.markdown("""
**5‑Day Return**  
Percentage change in price over the last 5 trading days.

**Volatility (5‑Day)**  
Standard deviation of daily returns over the last 5 days.

**MA5 (5‑Day Moving Average)**  
Short‑term smoothing to detect micro‑trend direction.

**Weight (Ratio)**  
Recommended allocation between TQQQ and SQQQ.

**No‑Trade Zone**  
Avoids trades when the signal is too weak.

**SMA10**  
Short‑term trend filter.

**Trade Allowed Today**  
Final decision combining ratio strength + trend filter.
""")