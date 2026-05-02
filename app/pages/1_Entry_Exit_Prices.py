import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.title("Intraday Entry / Exit Diagnostics")
st.write("Analyze intraday price touches for realistic entry/exit hit frequency.")

# ---------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------
ticker = st.sidebar.text_input("Ticker", "TQQQ")
interval = st.sidebar.selectbox("Interval", ["5m", "1m"], index=1)
days_back = st.sidebar.slider("Days Back", 5, 10, 7)

# Percentile window and thresholds (model defaults)
window = st.sidebar.slider("Percentile Window (days)", 3, 7, 5)
entry_percentile = st.sidebar.slider("Entry Percentile", 5, 40, 25)
exit_percentile = st.sidebar.slider("Exit Percentile", 60, 95, 75)

# Gain target exit (practical trading goal)
gain_target = st.sidebar.slider("Gain Target (%)", 0.5, 2.0, 1.5)

# ---------------------------------------------------------
# Fetch intraday data ONCE
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

df = df.dropna()

# ---------------------------------------------------------
# Fix timezone properly (Yahoo returns UTC)
# ---------------------------------------------------------
idx = pd.to_datetime(df.index)

if idx.tz is None:
    df.index = idx.tz_localize("UTC").tz_convert("US/Eastern")
else:
    df.index = idx.tz_convert("US/Eastern")

# ---------------------------------------------------------
# Slice last 7 days (or days_back if < 7)
# ---------------------------------------------------------
slice_days = min(days_back, 7)

end_time = df.index.max()
start_time = end_time - pd.Timedelta(days=slice_days)
df_last7 = df.loc[start_time:end_time]

# ---------------------------------------------------------
# Compute daily closes for percentile window
# ---------------------------------------------------------
daily = df_last7["Close"].resample("1D").last().dropna()

if len(daily) < window:
    st.error("Not enough daily data to compute percentiles. Reduce window.")
    st.stop()

recent = daily.tail(window)
entry_price = float(np.percentile(recent, entry_percentile))
exit_price = float(np.percentile(recent, exit_percentile))

# Gain-target exit based on entry
exit_gain_price = entry_price * (1 + gain_target / 100.0)

# Precompute gains for display
gain_pct_model = (exit_price / entry_price - 1.0) * 100.0
gain_pct_target = (exit_gain_price / entry_price - 1.0) * 100.0

# ---------------------------------------------------------
# Intraday signal detection (Option A: separate cycles)
# ---------------------------------------------------------
def intraday_signals_dual(df, entry_price, exit_price, exit_gain_price):
    buy_hits = 0

    sell_hits_model = 0
    sell_hits_gain = 0

    cycles_model = 0
    cycles_gain = 0

    in_pos_model = False
    in_pos_gain = False

    for i in range(1, len(df)):
        low = float(df["Low"].iloc[i])
        high = float(df["High"].iloc[i])
        close_now = float(df["Close"].iloc[i])
        close_prev = float(df["Close"].iloc[i - 1])

        # intraday momentum
        if close_now > close_prev:
            momentum = "UP"
        elif close_now < close_prev:
            momentum = "DOWN"
        else:
            momentum = "FLAT"

        # BUY: intraday low touches entry level + momentum UP
        if (not in_pos_model or not in_pos_gain) and low <= entry_price and momentum == "UP":
            # Count a single BUY hit, but we can be "in position" for both paths
            if not in_pos_model or not in_pos_gain:
                buy_hits += 1
            in_pos_model = True
            in_pos_gain = True

        # SELL A: percentile exit
        if in_pos_model and high >= exit_price and momentum == "DOWN":
            sell_hits_model += 1
            cycles_model += 1
            in_pos_model = False

        # SELL B: gain-target exit
        if in_pos_gain and high >= exit_gain_price and momentum == "DOWN":
            sell_hits_gain += 1
            cycles_gain += 1
            in_pos_gain = False

    return buy_hits, sell_hits_model, sell_hits_gain, cycles_model, cycles_gain

# Run the function
buy_hits, sell_hits_model, sell_hits_gain, cycles_model, cycles_gain = intraday_signals_dual(
    df_last7, entry_price, exit_price, exit_gain_price
)

# ---------------------------------------------------------
# 1) Show Intraday Signal Diagnostics FIRST
# ---------------------------------------------------------
st.subheader("Intraday Signal Diagnostics")

st.write(f"**Entry Price (Percentile):** {entry_price:.2f}")
st.write(f"**Exit Price (Percentile Model):** {exit_price:.2f}  "
         f"(_Gain vs Entry: {gain_pct_model:.2f}%_)")
st.write(f"**Exit Price (Gain Target {gain_target:.2f}%):** {exit_gain_price:.2f}  "
         f"(_Gain vs Entry: {gain_pct_target:.2f}%_)")

st.write("---")
st.write(f"**Intraday BUY hits (shared):** {buy_hits}")
st.write(f"**Intraday SELL hits (Percentile Exit):** {sell_hits_model}")
st.write(f"**Intraday SELL hits (Gain-Target Exit):** {sell_hits_gain}")
st.write(f"**Completed cycles (Percentile Exit):** {cycles_model}")
st.write(f"**Completed cycles (Gain-Target Exit):** {cycles_gain}")

if cycles_model > 0:
    avg_minutes_model = len(df_last7) / cycles_model
    st.write(f"**Average minutes per cycle (Percentile Exit):** {avg_minutes_model:.1f}")
else:
    st.write("**Average minutes per cycle (Percentile Exit):** No completed cycles")

if cycles_gain > 0:
    avg_minutes_gain = len(df_last7) / cycles_gain
    st.write(f"**Average minutes per cycle (Gain-Target Exit):** {avg_minutes_gain:.1f}")
else:
    st.write("**Average minutes per cycle (Gain-Target Exit):** No completed cycles")

# ---------------------------------------------------------
# 2) Show the 7-day intraday table SECOND
# ---------------------------------------------------------
st.subheader(f"Intraday Data (Last {slice_days} Days, {interval} Resolution)")
st.write("Intraday data shape:", df_last7.shape)

# Sort newest → oldest
df_last7 = df_last7.sort_index(ascending=False)

# Format numeric columns to 2 decimals
df_last7_fmt = df_last7.copy()
for col in ["Open", "High", "Low", "Close"]:
    df_last7_fmt[col] = df_last7_fmt[col].map(lambda x: f"{x:.2f}")

st.dataframe(df_last7_fmt, height=600, use_container_width=True)