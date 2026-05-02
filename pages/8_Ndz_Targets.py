import streamlit as st
st.set_page_config(layout="wide")

import numpy as np
import pandas as pd
import yfinance as yf

st.title("📘 Page 6 – NDX Basket Opportunity Scanner")
st.write("Identify pullback opportunities using MA20, MA5, and volatility-adjusted MA20_Lower.")
st.write("---")

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

CONFIG = {
    "tickers": {
        "NVDA": "NVIDIA",
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "AMZN": "Amazon",
        "TSLA": "Tesla",
        "WMT": "Walmart",
        "GOOGL": "Alphabet Class A",
        "META": "Meta Platforms",
        "GOOG": "Alphabet Class C",
        "AVGO": "Broadcom",
        "COST": "Costco",
        "MU": "Micron",
        "NFLX": "Netflix",
        "AMD": "Advanced Micro Devices",
        "PLTR": "Palantir",
        "CSCO": "Cisco",
        "AMAT": "Applied Materials",
        "LRCX": "Lam Research",
        "TMUS": "T-Mobile",
        "LIN": "Linde",
        "INTC": "Intel",
        "PEP": "PepsiCo",
        "KLAC": "KLA Corp",
        "AMGN": "Amgen",
        "TXT": "Textron"
    }
}

with st.sidebar:
    st.header("NDX Basket Model")
    st.write(f"Tickers: **{len(CONFIG['tickers'])}**")
    st.write("---")

# ─────────────────────────────────────────────
# FETCH FULL HISTORY
# ─────────────────────────────────────────────

def fetch_history(ticker: str) -> pd.DataFrame:
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

# ─────────────────────────────────────────────
# PROCESS TICKERS
# ─────────────────────────────────────────────

rows = []

for symbol, name in CONFIG["tickers"].items():
    hist = fetch_history(symbol)

    if hist.empty or len(hist) < 20:
        rows.append({
            "Ticker": symbol,
            "Name": name,
            "MA20": None,
            "MA5": None,
            "Last Price": None,
            "MA20_Lower": None,
            "MA5vsMA20 (%)": None,
            "LastPricevsMA20_Lower (%)": None
        })
        continue

    # MA20
    ma20_series = hist["Close"].rolling(20).mean().dropna()
    ma20 = ma20_series.iloc[-1]

    # MA5
    ma5_series = hist["Close"].rolling(5).mean().dropna()
    ma5 = ma5_series.iloc[-1]

    # Standard deviation of MA20
    ma20_std = ma20_series.std()

    # Lower band
    ma20_lower = ma20 - ma20_std

    # Last price
    last_price = hist["Close"].iloc[-1]

    # Percentages
    ma5_vs_ma20 = (ma5 - ma20) / ma20 * 100
    last_vs_ma20lower = (last_price - ma20_lower) / ma20_lower * 100

    rows.append({
        "Ticker": symbol,
        "Name": name,
        "MA20": round(ma20, 2),
        "MA5": round(ma5, 2),
        "Last Price": round(last_price, 2),
        "MA20_Lower": round(ma20_lower, 2),
        "MA5vsMA20 (%)": round(ma5_vs_ma20, 2),
        "LastPricevsMA20_Lower (%)": round(last_vs_ma20lower, 2)
    })

# ─────────────────────────────────────────────
# DISPLAY RESULTS
# ─────────────────────────────────────────────

df = pd.DataFrame(rows)

st.subheader("📊 NDX Basket Targets Scanner")
st.dataframe(df, width="stretch")
