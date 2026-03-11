import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import altair as alt

st.title("Entry / Exit Price Engine")
st.write("Determine ideal entry and exit prices based on recent price ranges.")

# ---------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------
ticker = st.sidebar.text_input("Ticker", "TQQQ")
window = st.sidebar.slider("Days Window", 5, 20, 7)
entry_percentile = st.sidebar.slider("Entry Percentile", 5, 40, 25)
exit_percentile = st.sidebar.slider("Exit Percentile", 60, 95, 75)

# ---------------------------------------------------------
# Safe fetch with retries (Cloud-friendly)
# ---------------------------------------------------------
def safe_fetch(ticker, period="3mo", interval="1d", retries=3):
    for attempt in range(retries):
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            progress=False
        )
        df = df.dropna()

        if not df.empty:
            return df

        time.sleep(1)  # wait before retry

    return df  # may be empty after retries

@st.cache_data
def load_data(ticker):
    return safe_fetch(ticker)

df = load_data(ticker)

# ---------------------------------------------------------
# Convert index to clean YYYY-MM-DD
# ---------------------------------------------------------
if not df.empty:
    df.index = df.index.date

# ---------------------------------------------------------
# Debug info (helps diagnose Cloud issues)
# ---------------------------------------------------------
st.write("**Data shape returned by yfinance:**", df.shape)
st.dataframe(df.tail())

# ---------------------------------------------------------
# Safety check for empty or insufficient data
# ---------------------------------------------------------
if df.empty or "Close" not in df.columns:
    st.error("No price data returned from yfinance. Try another ticker or refresh the app.")
    st.stop()

recent = df["Close"].tail(window)

if recent.empty or len(recent) < 5:
    st.error("Not enough recent price data to compute entry/exit levels. Data returned from yfinance was incomplete.")
    st.stop()

# ---------------------------------------------------------
# Calculate levels
# ---------------------------------------------------------
entry_price = float(np.percentile(recent, entry_percentile))
exit_price = float(np.percentile(recent, exit_percentile))
price_now = float(df["Close"].iloc[-1])

# ---------------------------------------------------------
# Momentum calculation
# ---------------------------------------------------------
if len(df) > 1:
    today = float(df["Close"].iloc[-1])
    yesterday = float(df["Close"].iloc[-2])

    if today > yesterday:
        momentum = "UP"
    elif today < yesterday:
        momentum = "DOWN"
    else:
        momentum = "FLAT"
else:
    momentum = "FLAT"

# ---------------------------------------------------------
# Signal logic
# ---------------------------------------------------------
signal = "H HOLD"

if price_now <= entry_price and momentum == "UP":
    signal = "BUY"
elif price_now >= exit_price and momentum == "DOWN":
    signal = "SELL"

# ---------------------------------------------------------
# Display metrics
# ---------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Current Price", f"{price_now:.2f}")
col2.metric("Entry Price", f"{entry_price:.2f}")
col3.metric("Exit Price", f"{exit_price:.2f}")
col4.metric("Signal", signal)

st.divider()

st.subheader("Recent Prices")
st.dataframe(df.tail(10))

# ---------------------------------------------------------
# Price Chart (Altair with visible date axis)
# ---------------------------------------------------------
import altair as alt

st.subheader("Price Chart")

df_chart = df.reset_index().rename(columns={"index": "Date"})

chart = (
    alt.Chart(df_chart)
    .mark_line()
    .encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Close:Q", title="Price"),
        tooltip=["Date:T", "Close:Q"]
    )
    .properties(height=300)
)

st.altair_chart(chart, use_container_width=True)

# ---------------------------------------------------------
# Explanation
# ---------------------------------------------------------
with st.expander("Calculation Details"):
    st.write(f"""
Entry price = {entry_percentile}th percentile of last {window} days.

Exit price = {exit_percentile}th percentile of last {window} days.

Momentum compares today's close with yesterday's close.
""")