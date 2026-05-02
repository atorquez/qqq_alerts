import streamlit as st
st.set_page_config(layout="wide")

import numpy as np
import pandas as pd
import yfinance as yf

st.title("🌠 NDX Basket Analysis")
st.write("Short-term trend classification using last 5 daily closes.")
st.write("---")

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

CONFIG = {
    "tickers": [
        "NVDA","AAPL","MSFT","AMZN","TSLA","WMT","GOOGL","META","GOOG",
        "AVGO","COST","MU","NFLX","AMD","PLTR","CSCO","AMAT","LRCX",
        "TMUS","LIN","INTC","PEP","KLAC","AMGN","TXT",
        "AES","BAX","BBWI","BEN","CPB","CZR","FMC","GEN","HRL","HST",
        "INVH","IVZ","KEY","KIM","MOS","NWSA","RF","RHI","VICI","WY","XRAY"
    ],
    "lookback_days": 5,
}

# Ticker names
TICKER_NAMES = {
    "NVDA": "NVIDIA", "AAPL": "Apple", "MSFT": "Microsoft", "AMZN": "Amazon",
    "TSLA": "Tesla", "WMT": "Walmart", "GOOGL": "Alphabet Class A",
    "META": "Meta Platforms", "GOOG": "Alphabet Class C", "AVGO": "Broadcom",
    "COST": "Costco", "MU": "Micron", "NFLX": "Netflix", "AMD": "Advanced Micro Devices",
    "PLTR": "Palantir", "CSCO": "Cisco", "AMAT": "Applied Materials",
    "LRCX": "Lam Research", "TMUS": "T-Mobile", "LIN": "Linde", "INTC": "Intel",
    "PEP": "PepsiCo", "KLAC": "KLA Corp", "AMGN": "Amgen", "TXT": "Textron",
    "AES": "AES Corporation", "BAX": "Baxter International", "BBWI": "Bath & Body Works",
    "BEN": "Franklin Resources", "CPB": "Campbell Soup", "CZR": "Caesars Entertainment",
    "FMC": "FMC Corporation", "GEN": "Gen Digital", "HRL": "Hormel Foods",
    "HST": "Host Hotels & Resorts", "INVH": "Invitation Homes", "IVZ": "Invesco",
    "KEY": "KeyCorp", "KIM": "Kimco Realty", "MOS": "The Mosaic Company",
    "NWSA": "News Corp", "RF": "Regions Financial", "RHI": "Robert Half International",
    "VICI": "Vici Properties", "WY": "Weyerhaeuser", "XRAY": "Dentsply Sirona"
}

with st.sidebar:
    st.header("Configuration")
    st.write(f"Tickers: **{len(CONFIG['tickers'])}**")
    st.write(f"Lookback: **{CONFIG['lookback_days']} days**")
    st.write("---")

# ─────────────────────────────────────────────
# FETCH LAST 5 DAILY CLOSES
# ─────────────────────────────────────────────

def fetch_last_closes(ticker: str) -> pd.DataFrame:
    df = yf.download(
        ticker,
        period="3mo",
        interval="1d",
        progress=False
    )
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df.tail(CONFIG["lookback_days"])

# ─────────────────────────────────────────────
# REGRESSION ON LAST 5 CLOSES
# ─────────────────────────────────────────────

def compute_regression_angle(df: pd.DataFrame) -> float:
    closes = df["Close"].values.astype(float)
    if len(closes) < 3:
        return 0.0
    x = np.arange(len(closes), dtype=float)
    slope, intercept = np.polyfit(x, closes, 1)
    angle_deg = np.degrees(np.arctan(slope))
    return round(float(angle_deg), 2)

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
    df = fetch_last_closes(ticker)
    if df.empty:
        return {
            "ticker": ticker,
            "name": TICKER_NAMES.get(ticker, ""),
            "last_price": None,
            "classification": "NO_DATA",
        }
    angle = compute_regression_angle(df)
    classification = classify_angle(angle)
    last_price = float(df["Close"].iloc[-1].item())
    return {
        "ticker": ticker,
        "name": TICKER_NAMES.get(ticker, ""),
        "last_price": round(last_price, 2),
        "classification": classification,
    }

# ─────────────────────────────────────────────
# RUN ANALYSIS
# ─────────────────────────────────────────────

results = [evaluate_trend(t) for t in CONFIG["tickers"]]
df_results = pd.DataFrame(results)

# ─────────────────────────────────────────────
# ADD MA20, MA5, MA5vsMA20, LastPricevsMA5
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
ma5_vs_ma20_list = []
lastprice_vs_ma5_list = []

for ticker in df_results["ticker"]:
    hist = fetch_full_history(ticker)

    if hist.empty or len(hist) < 20:
        ma20_list.append(None)
        ma5_list.append(None)
        ma5_vs_ma20_list.append(None)
        lastprice_vs_ma5_list.append(None)
        continue

    ma20 = hist["Close"].rolling(20).mean().dropna().iloc[-1]
    ma5 = hist["Close"].rolling(5).mean().dropna().iloc[-1]
    last_price = hist["Close"].iloc[-1]

    MA5vsMA20 = (ma5 - ma20) / ma20 * 100
    LastPricevsMA5 = (last_price - ma5) / ma5 * 100

    ma20_list.append(round(ma20, 2))
    ma5_list.append(round(ma5, 2))
    ma5_vs_ma20_list.append(round(MA5vsMA20, 2))
    lastprice_vs_ma5_list.append(round(LastPricevsMA5, 2))

df_results["MA20"] = ma20_list
df_results["MA5"] = ma5_list
df_results["MA5vsMA20"] = ma5_vs_ma20_list
df_results["LastPricevsMA5"] = lastprice_vs_ma5_list

# Reorder columns
df_results = df_results[[
    "ticker",
    "name",
    "last_price",
    "classification",
    "MA20",
    "MA5",
    "MA5vsMA20",
    "LastPricevsMA5"
]]

# ─────────────────────────────────────────────
# DISPLAY RESULTS
# ─────────────────────────────────────────────

st.subheader("📊 Trend Classification (Last 5 Daily Closes)")
st.dataframe(df_results, width="stretch")




