import streamlit as st
st.set_page_config(layout="wide")

import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt

# REVISION: 03.14.26

#st.title("🔮 Wishing Well - Smart Way to Trade")
st.title("🌠 BUY and SELL Strategies")
st.write("Define the best BUY and SELL prices based on your WIN cycle strategies: for example, small percentages 0.5% to 1.5% the WIN cycles are faster and high percentages over 1.5% the WIN cycles are longer.")
st.write("---")

# ---------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------
ticker = st.sidebar.text_input("Ticker", "TQQQ")
interval = st.sidebar.selectbox("Interval", ["5m", "1m"], index=1)
days_back = st.sidebar.slider("Days Back", 5, 10, 7)

# Percentile window and thresholds (model defaults)
window = st.sidebar.slider("Percentile Window (days)", 3, 7, 5)
entry_percentile = st.sidebar.slider("BUYPercentile", 5, 40, 25)
exit_percentile = st.sidebar.slider("SELL Percentile", 60, 95, 75)

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

st.write(f"**BUY Price (Percentile):** {entry_price:.2f}")
st.write(f"**SELL Price (Percentile Model):** {exit_price:.2f}  "
         f"(_Gain vs BUY: {gain_pct_model:.2f}%_)")
st.write(f"**SELL Price (Gain Target {gain_target:.2f}%):** {exit_gain_price:.2f}  "
         f"(_Gain vs BUY: {gain_pct_target:.2f}%_)")


# ---------------------------------------------------------
# Trend Panel (MA10 + MA20) using SAME ticker
# ---------------------------------------------------------
st.subheader("Short-Term Trend (MA10 & MA20)")
def plot_ma_panel(ticker, container):
    df_daily = yf.download(ticker, period="40d", interval="1d", progress=False)

    if df_daily.empty:
        container.warning(f"No data for {ticker}.")
        return

    df_daily = df_daily.dropna()

    # Flatten MultiIndex if needed
    if isinstance(df_daily.columns, pd.MultiIndex):
        df_daily.columns = [col[0] for col in df_daily.columns]

    # Compute moving averages
    df_daily["MA10"] = df_daily["Close"].rolling(10).mean()
    df_daily["MA20"] = df_daily["Close"].rolling(20).mean()

    # Last 20 days
    df_plot = df_daily.tail(20).copy()

    # Reset index for Altair
    df_plot = df_plot.reset_index().rename(columns={"index": "Date"})

    # Detect crossovers
    df_plot["prev_MA10"] = df_plot["MA10"].shift(1)
    df_plot["prev_MA20"] = df_plot["MA20"].shift(1)

    df_plot["bullish"] = (
        (df_plot["prev_MA10"] < df_plot["prev_MA20"]) &
        (df_plot["MA10"] > df_plot["MA20"])
    )

    df_plot["bearish"] = (
        (df_plot["prev_MA10"] > df_plot["prev_MA20"]) &
        (df_plot["MA10"] < df_plot["MA20"])
    )

    # Melt for Altair
    df_long = df_plot.melt(
        id_vars=["Date"],
        value_vars=["Close", "MA10", "MA20"],
        var_name="variable",
        value_name="value"
    )

    df_long["value"] = df_long["value"].astype(float)

    # DYNAMIC Y-AXIS SCALING
    vmin = df_long["value"].min()
    vmax = df_long["value"].max()

    pad = (vmax - vmin) * 0.10
    domain_min = vmin - pad
    domain_max = vmax + pad

    price_range = vmax - vmin

    if price_range < 1:
        step = 0.05
    elif price_range < 3:
        step = 0.10
    elif price_range < 8:
        step = 0.25
    else:
        step = 0.50

    y_values = list(np.arange(domain_min, domain_max + step, step))

    # ---------------------------------------------------------
    # PRICE + MA LINES
    # ---------------------------------------------------------
    price_lines = (
        alt.Chart(df_long)
        .mark_line()
        .encode(
            x=alt.X("Date:T",
                axis=alt.Axis(title="Date", format="%b %d", labelAngle=-30)
            ),
            y=alt.Y("value:Q",
                axis=alt.Axis(title="Price", format=".2f", values=y_values),
                scale=alt.Scale(domain=[domain_min, domain_max])
            ),
            color=alt.Color("variable:N", title="Series"),
            tooltip=["Date:T", "variable:N", "value:Q"]
        )
    )

    # ---------------------------------------------------------
    # CROSSOVER MARKERS
    # ---------------------------------------------------------
    bullish_points = (
        alt.Chart(df_plot[df_plot["bullish"]])
        .mark_point(color="green", size=100)
        .encode(x="Date:T", y="MA10:Q")
    )

    bearish_points = (
        alt.Chart(df_plot[df_plot["bearish"]])
        .mark_point(color="red", size=100)
        .encode(x="Date:T", y="MA10:Q")
    )

    # ---------------------------------------------------------
    # VOLUME BARS (Option A: Green/Red)
    # ---------------------------------------------------------
    df_plot["prev_close"] = df_plot["Close"].shift(1)
    df_plot["vol_color"] = df_plot.apply(
        lambda row: "green" if row["Close"] > row["prev_close"] else "red",
        axis=1
    )

    volume_bars = (
        alt.Chart(df_plot)
        .mark_bar()
        .encode(
            x="Date:T",
            y=alt.Y("Volume:Q", axis=alt.Axis(title="Volume")),
            color=alt.Color("vol_color:N", scale=None)
        )
        .properties(height=80)
    )

    # ---------------------------------------------------------
    # COMBINE CHARTS (vertical stack)
    # ---------------------------------------------------------
    final_chart = alt.vconcat(
        price_lines + bullish_points + bearish_points,
        volume_bars
    ).resolve_scale(x="shared")

    container.altair_chart(final_chart, width="stretch")

plot_ma_panel(ticker, st)

st.write("""
### 📘 How to Read This Chart

**BUY TQQQ (Nasdaq DOWN):**
1. MA10 crosses **below** MA20  
2. Price is **below** MA10  
3. Red volume bars increasing (selling pressure)  
4. Nasdaq closing direction = **DOWN**

**BUY SQQQ (Nasdaq UP):**
1. MA10 crosses **above** MA20  
2. Price is **above** MA10  
3. Green volume bars increasing (buying pressure)  
4. Nasdaq closing direction = **UP**

These signals help identify short-term overextensions and pullbacks that align with the Wishing Well 3‑Block Strategy.
""")

st.write("---")

# ---------------------------------------------------------
# Nasdaq Up/Down Sequence (Last 30 Days + Streak Detection)
# ---------------------------------------------------------
st.subheader("Nasdaq (NDX) – Last 30 Days Trend & Streaks")

ndx = yf.download("^NDX", period="40d", interval="1d", progress=False)

if ndx.empty:
    st.warning("Could not retrieve Nasdaq data.")
else:
    if isinstance(ndx.columns, pd.MultiIndex):
        ndx.columns = ['_'.join(col).strip() for col in ndx.columns.values]

    close_cols = [c for c in ndx.columns if "Close" in c]
    if not close_cols:
        st.warning("No Close column found in Nasdaq data.")
    else:
        close_col = close_cols[0]

        closes = ndx[close_col].dropna()

        ndx_df = pd.DataFrame({"Close": closes})
        ndx_df["Change"] = ndx_df["Close"].diff()
        ndx_df["Pct_Change"] = ndx_df["Change"] / ndx_df["Close"].shift(1) * 100

        ndx_df["Direction"] = ndx_df["Pct_Change"].apply(
            lambda x: "UP" if x > 0 else ("DOWN" if x < 0 else "FLAT")
        )

        streaks = []
        current_streak = 0
        last_dir = None

        for d in ndx_df["Direction"]:
            if d == last_dir:
                current_streak += 1
            else:
                current_streak = 1
                last_dir = d
            streaks.append(current_streak)

        ndx_df["Streak"] = streaks

        ndx_last60 = ndx_df.tail(60)
        ndx_last60 = ndx_last60.sort_index(ascending=False)

        ndx_last60_fmt = ndx_last60.copy()
        ndx_last60_fmt["Close"] = ndx_last60_fmt["Close"].map(lambda x: f"{x:.2f}")
        ndx_last60_fmt["Change"] = ndx_last60_fmt["Change"].map(lambda x: f"{x:.2f}")
        ndx_last60_fmt["Pct_Change"] = ndx_last60_fmt["Pct_Change"].map(lambda x: f"{x:.2f}%")

        st.dataframe(ndx_last60_fmt, height=400, use_container_width=True)

        long_streaks = ndx_last60[ndx_last60["Streak"] >= 3]

        if not long_streaks.empty:
            st.success("Detected UP/DOWN streaks of 3+ days:")
            st.dataframe(long_streaks[["Close", "Pct_Change", "Direction", "Streak"]], height=300, use_container_width=True)
        else:
            st.info("No UP or DOWN streaks of 3+ days in the last 60 days.")

#--------------------------------------------------------
# Extra Data 
#--------------------------------------------------------
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
st.write("---")

# ---------------------------------------------------------
# 2) Show the 7-day intraday table SECOND
# ---------------------------------------------------------
st.subheader(f"Intraday Data (Last {slice_days} Days, {interval} Resolution)")
st.write("Intraday data shape:", df_last7.shape)

df_last7 = df_last7.sort_index(ascending=False)

df_last7_fmt = df_last7.copy()
for col in ["Open", "High", "Low", "Close"]:
    df_last7_fmt[col] = df_last7_fmt[col].map(lambda x: f"{x:.2f}")

st.dataframe(df_last7_fmt, height=600, use_container_width=True)