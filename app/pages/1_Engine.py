import sys
st.write("Python version:", sys.version)
import os

# ---------------------------------------------------------
# Ensure Python can find the project root
# ---------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from engine_pkg.engine import get_5d_return, decide_ratio


# ---------------------------------------------------------
# Helper: SMA10
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
st.write("This page shows the 5‑day returns, volatility, and the computed TQQQ/SQQQ ratio.")


# ---------------------------------------------------------
# Compute Engine Data
# ---------------------------------------------------------
if st.button("Run Engine"):

    # --- Compute 5‑day returns ---
    ret_t, price_t = get_5d_return("TQQQ")
    ret_s, price_s = get_5d_return("SQQQ")

    # --- Compute 5‑day volatility ---
    def get_vol(ticker):
        data = yf.download(ticker, period="10d", interval="1d")["Close"].dropna()
        return float(np.std(data.pct_change().dropna()))

    vol_t = get_vol("TQQQ")
    vol_s = get_vol("SQQQ")

    # --- Compute ratio ---
    w_t, w_s = decide_ratio(ret_t, ret_s, vol_t, vol_s)

    # --- Build output table ---
    df = pd.DataFrame({
        "Ticker": ["TQQQ", "SQQQ"],
        "5d Return": [ret_t, ret_s],
        "Volatility": [vol_t, vol_s],
        "Weight": [w_t, w_s],
        "Last Close": [price_t, price_s]
    })

    st.subheader("Engine Output")
    st.dataframe(df)

    # ---------------------------------------------------------
    # Recommended Split
    # ---------------------------------------------------------
    st.subheader("Recommended Allocation")

    tqqq_pct = round(w_t * 100, 2)
    sqqq_pct = round(w_s * 100, 2)

    st.success(f"📌 **Proposed Split:** {tqqq_pct}% TQQQ / {sqqq_pct}% SQQQ")

    # ---------------------------------------------------------
    # Today's Trade Decision Panel
    # ---------------------------------------------------------
    st.subheader("📌 Today's Trade Decision")

    # --- No-trade zone check ---
    no_trade_zone = (0.45 <= w_t <= 0.55)

    # --- SMA10 trend filter ---
    t_close, t_sma10 = get_sma10("TQQQ")
    s_close, s_sma10 = get_sma10("SQQQ")

    t_trend_ok = (t_close is not None and t_close > t_sma10)
    s_trend_ok = (s_close is not None and s_close > s_sma10)

    # --- Decision Logic ---
    reasons = []

    if no_trade_zone:
        reasons.append("Ratio inside no‑trade zone (weak signal)")

    if not t_trend_ok:
        reasons.append("TQQQ below SMA10 (downtrend)")

    if not s_trend_ok:
        reasons.append("SQQQ below SMA10 (downtrend)")

    trade_allowed = (not no_trade_zone) and (t_trend_ok or s_trend_ok)

    # --- Display Decision ---
    if trade_allowed:
        st.success("✅ **TRADE ALLOWED TODAY**")
    else:
        st.error("❌ **NO TRADE TODAY**")

    # --- Explanation ---
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
Standard deviation of daily returns over the last 5 days. Higher volatility = more uncertainty.

**Risk‑Adjusted Score**  
Return divided by volatility. Used to compare TQQQ vs SQQQ on equal footing.

**Weight (Ratio)**  
The recommended allocation between TQQQ and SQQQ based on risk‑adjusted momentum.

**No‑Trade Zone**  
If the ratio is too close to 50/50 (weak signal), the system avoids trading to prevent noise‑driven losses.

**SMA10 (10‑Day Simple Moving Average)**  
Short‑term trend indicator.  
- Price > SMA10 → uptrend  
- Price < SMA10 → downtrend

**Trade Allowed Today**  
A final decision combining ratio strength + trend filter.  
This prevents entering trades during weak or choppy markets.
""")   