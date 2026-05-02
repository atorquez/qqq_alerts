import streamlit as st
st.set_page_config(layout="wide")

import numpy as np
import pandas as pd
import yfinance as yf

st.title("🌠 NDX Basket Analysis")
st.write("Classify short-term trend using last 10 daily closes.")
st.write("---")

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

CONFIG = {
    "tickers": [
        "NVDA","AAPL","MSFT","AMZN","TSLA","WMT","GOOGL","META","GOOG",
        "AVGO","COST","MU","NFLX","AMD","PLTR","CSCO","AMAT","LRCX",
        "TMUS","LIN","INTC","PEP","KLAC","AMGN","TXT"
    ],
    "lookback_days": 10,
}

with st.sidebar:
    st.header("Configuration")
    st.write(f"Tickers: **{len(CONFIG['tickers'])}**")
    st.write(f"Lookback: **{CONFIG['lookback_days']} days**")
    st.write("---")

# ─────────────────────────────────────────────
# FETCH LAST 10 DAILY CLOSES
# ─────────────────────────────────────────────

def fetch_last_10_closes(ticker: str) -> pd.DataFrame:
   df = yf.download(
        ticker,
       period="3mo",
        interval="1d",
        progress=False
    )

    if df.empty:
        return df

#    if isinstance(df.columns, pd.MultiIndex):
#        df.columns = df.columns.get_level_values(0)
#
#    df.dropna(inplace=True)
#   return df.tail(CONFIG["lookback_days"])

# ─────────────────────────────────────────────
# REGRESSION ON LAST 10 CLOSES
# ─────────────────────────────────────────────

#def compute_regression_angle(df: pd.DataFrame) -> dict:
#    closes = df["Close"].values.astype(float)
#
#    if len(closes) < 5:
#        return {
#            "slope": 0.0,
#            "intercept": float(closes[-1]),
#            "angle_deg": 0.0,
#            "r_squared": 0.0,
#        }
#
#    x = np.arange(len(closes), dtype=float)
#    x_mean = x.mean()
#    y_mean = closes.mean()
#
#    cov_xy = np.mean((x - x_mean) * (closes - y_mean))
#    var_x = np.mean((x - x_mean) ** 2)
#
#   slope = cov_xy / var_x if var_x != 0 else 0.0
#   intercept = y_mean - slope * x_mean
#
#    std_x = x.std()
#    std_y = closes.std()
#    r_squared = (cov_xy / (std_x * std_y))**2 if std_x > 0 and std_y > 0 else 0.0

#  angle_deg = np.degrees(np.arctan(slope))

    return {
        "slope": round(float(slope), 4),
        "intercept": round(float(intercept), 4),
        "angle_deg": round(float(angle_deg), 2),
        "r_squared": round(float(r_squared), 4),
    }

# ─────────────────────────────────────────────
# TREND CLASSIFICATION
# ─────────────────────────────────────────────

def classify_angle(angle: float) -> str:
    if angle < 0:
        return "Down"
    elif angle < 10:
        return "Flat"
    elif angle < 20:
        return "Up – Moderate"
    elif angle < 35:
        return "Up – Strong"
    else:
        return "Up – Extreme"

# ─────────────────────────────────────────────
# PER-TICKER EVALUATION
# ─────────────────────────────────────────────

def evaluate_trend(ticker: str) -> dict:
    df = fetch_last_10_closes(ticker)

    if df.empty:
        return {
            "ticker": ticker,
            "angle_deg": None,
            "r_squared": None,
            "slope": None,
            "last_price": None,
            "classification": "NO_DATA",
        }

    trend = compute_regression_angle(df)
    classification = classify_angle(trend["angle_deg"])
    last_price = float(df["Close"].iloc[-1].item())

    return {
        "ticker": ticker,
        "angle_deg": trend["angle_deg"],
        "r_squared": trend["r_squared"],
        "slope": trend["slope"],
        "last_price": round(last_price, 2),
        "classification": classification,
    }

# ─────────────────────────────────────────────
# RUN ANALYSIS
# ─────────────────────────────────────────────

results = [evaluate_trend(t) for t in CONFIG["tickers"]]
df_results = pd.DataFrame(results)

df_results = df_results.sort_values(by="angle_deg", ascending=False, na_position="last")

# ─────────────────────────────────────────────
# ADD MA20, MA5, MA5_lower (1 std), META, PASS
# ─────────────────────────────────────────────

def fetch_full_history(ticker: str) -> pd.DataFrame:
    df = yf.download(
        ticker,
        period="2mo",
        interval="1d",
        progress=False
    )
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df

ma20_list = []
ma5_list = []
ma20_lower_list = []
ma5_vs_ma20_list = []
ma20L_vs_lastprice_list = []

for ticker in df_results["ticker"]:
    hist = fetch_full_history(ticker)

    if hist.empty or len(hist) < 20:
        ma20_list.append(None)
        ma5_list.append(None)
        ma20_lower_list.append(None)
        ma5_vs_ma20_list.append(None)
        ma20L_vs_lastprice_list.append(None)
        continue

    # MA20
    ma20_series = hist["Close"].rolling(20).mean().dropna()
    ma20 = ma20_series.iloc[-1]

    # MA5
    ma5_series = hist["Close"].rolling(5).mean().dropna()
    ma5 = ma5_series.iloc[-1]

    # Standard deviations
    ma20_std = ma20_series.std()
    ma5_std = ma5_series.std()

    # Lower bands
    ma20_lower = ma20 - ma20_std
    ma5_lower = ma5 - ma5_std

    # MA5 vs MA20 (%)
    MA5vsMA20 = (ma5 - ma20) / ma20 * 100

    # MA20_lower vs Last Price (%)
    last_price = hist["Close"].iloc[-1]
    MA20LvsLastPrice = (ma20_lower - last_price) / last_price * 100

    # Append values
    ma20_list.append(round(ma20, 2))
    ma5_list.append(round(ma5, 2))
    ma20_lower_list.append(round(ma20_lower, 2))

    # Percentages rounded to 2 decimals
    ma5_vs_ma20_list.append(round(MA5vsMA20, 2))
    ma20L_vs_lastprice_list.append(round(MA20LvsLastPrice, 2))


# Assign to df_results
df_results["MA20"] = ma20_list
df_results["MA5"] = ma5_list
df_results["MA20_lower"] = ma20_lower_list
df_results["MA5vsMA20"] = ma5_vs_ma20_list
df_results["MA20LvsLastPrice"] = ma20L_vs_lastprice_list


# ─────────────────────────────────────────────
# DISPLAY RESULTS
# ─────────────────────────────────────────────

st.subheader("📊 Trend Classification (Last 10 Daily Closes)")
st.dataframe(df_results, width="stretch")