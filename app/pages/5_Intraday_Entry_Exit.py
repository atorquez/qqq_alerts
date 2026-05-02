import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt

st.title("Intraday Entry / Exit Diagnostics")
st.write("Analyze intraday price touches for realistic entry/exit hit frequency.")

# ---------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------
ticker = st.sidebar.text_input("Ticker", "TQQQ")
interval = st.sidebar.selectbox("Interval", ["5m", "1m"], index=0)
days_back = st.sidebar.slider("Days Back", 5, 10, 7)
window = st.sidebar.slider("Percentile Window (days)", 5, 20, 7)
entry_percentile = st.sidebar.slider("Entry Percentile", 5, 40, 25)
exit_percentile = st.sidebar.slider("Exit Percentile", 60, 95, 75)

# ---------------------------------------------------------
# Fetch intraday data
# ---------------------------------------------------------
period_str = f"{days_back}d"

df = yf.download(
    ticker,
    period=period_str,
    interval=interval,
    progress=False
)

if df.empty:
    st.error("No intraday data returned. Try a different ticker or interval.")
    st.stop()

# Clean index
df = df.dropna()
df.index = pd.to_datetime(df.index).tz_localize(None)

st.write("Intraday data shape:", df.shape)
st.dataframe(df.tail())

# ---------------------------------------------------------
# Compute daily closes for percentile window
# ---------------------------------------------------------
daily = df["Close"].resample("1D").last().dropna()

st.write("Daily resample shape:", daily.shape)

if len(daily) < window:
    st.error("Not enough daily data to compute percentiles. Try increasing Days Back.")
    st.stop()

recent = daily.tail(window)
entry_price = float(np.percentile(recent, entry_percentile))
exit_price = float(np.percentile(recent, exit_percentile))

# ---------------------------------------------------------
# Intraday signal detection
# ---------------------------------------------------------
def intraday_signals(df, entry_price, exit_price):
    buy_hits = 0
    sell_hits = 0
    cycles = 0
    in_position = False

    for i in range(1, len(df)):
        low = float(df["Low"].iloc[i])
        high = float(df["High"].iloc[i])
        close_now = float(df["Close"].iloc[i])
        close_prev = float(df["Close"].iloc[i-1])

        # intraday momentum
        if close_now > close_prev:
            momentum = "UP"
        elif close_now < close_prev:
            momentum = "DOWN"
        else:
            momentum = "FLAT"

        # BUY: intraday low touches entry level + momentum UP
        if not in_position and low <= entry_price and momentum == "UP":
            buy_hits += 1
            in_position = True

        # SELL: intraday high touches exit level + momentum DOWN
        elif in_position and high >= exit_price and momentum == "DOWN":
            sell_hits += 1
            cycles += 1
            in_position = False

    return buy_hits, sell_hits, cycles

# Run the function (this was missing before)
buy_hits, sell_hits, cycles = intraday_signals(df, entry_price, exit_price)

# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------
st.subheader("Intraday Signal Diagnostics")

st.write(f"**Entry Price:** {entry_price:.2f}")
st.write(f"**Exit Price:** {exit_price:.2f}")
st.write("---")
st.write(f"**Intraday BUY hits:** {buy_hits}")
st.write(f"**Intraday SELL hits:** {sell_hits}")
st.write(f"**Completed cycles:** {cycles}")

if cycles > 0:
    avg_minutes = len(df) / cycles
    st.write(f"**Average minutes per cycle:** {avg_minutes:.1f}")
else:
    st.write("**Average minutes per cycle:** No completed cycles")

# ---------------------------------------------------------
# Chart
# ---------------------------------------------------------
st.subheader("Intraday Price Chart")

df_chart = df.reset_index().rename(columns={"index": "Datetime"})

# Compute tight y-axis bounds with padding
y_min = df["Close"].min()
y_max = df["Close"].max()
padding = (y_max - y_min) * 0.05  # 5% padding

chart = (
    alt.Chart(df_chart)
    .mark_line()
    .encode(
        x=alt.X("Datetime:T", title="Datetime"),
        y=alt.Y(
            "Close:Q",
            title="Price",
            scale=alt.Scale(
                domain=[float(y_min - padding), float(y_max + padding)]
            ),
            axis=alt.Axis(
                format=".2f",      # show decimals
                tickCount=12,      # more granular ticks
                labelOverlap=False
            )
        ),
        tooltip=[
            alt.Tooltip("Datetime:T", title="Time"),
            alt.Tooltip("Close:Q", title="Price", format=".2f")
        ]
    )
    .properties(height=300)
)

st.altair_chart(chart, use_container_width=True)