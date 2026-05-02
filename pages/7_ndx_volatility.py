import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("📈 Nasdaq‑100 (NDX) – Volatility Explorer")
st.write("Analyze last‑day volatility for all Nasdaq‑100 tickers.")
st.write("---")

# ---------------------------------------------------------
# Static NDX ticker list (stable + fast)
# ---------------------------------------------------------
NDX_TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","GOOG","META","TSLA","AVGO","PEP",
    "COST","NFLX","AMD","INTC","QCOM","CSCO","ADBE","AMGN","TXN","HON",
    "SBUX","BKNG","MDLZ","ADI","LRCX","AMAT","REGN","VRTX","GILD","PYPL",
    "MAR","KDP","PANW","FTNT","CRWD","ABNB","TEAM","SNPS","ADSK","KLAC",
    "MELI","MRVL","NXPI","CDNS","AEP","CEG","CHTR","EA","EXC","FISV",
    "IDXX","ILMN","KHC","MNST","MSCI","ORLY","PAYX","PCAR","ROST","SIRI",
    "SWKS","TTWO","VRSK","WDAY","XEL","ZS","BIDU","JD","PDD","BMRN",
    "CTAS","DLTR","EBAY","FAST","FOX","FOXA","GEN","LULU","MCHP","ODFL",
    "SGEN","SPLK","VRSN","WBA","WBD","ZM","APP","ARM","PLTR","TSCO",
    "WMT","TMO","ASML","ISRG","CSX","CPRT","ANSS","ALGN"
]

# ---------------------------------------------------------
# Volatility calculation
# ---------------------------------------------------------
def get_last_day_volatility(tickers):
    results = []

    for t in tickers:
        try:
            df = yf.download(t, period="3d", interval="1d", progress=False)

            if df is None or df.empty:
                continue

            # Fix MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]

            if "Close" not in df.columns:
                continue

            df = df.dropna(subset=["Close"])

            if len(df) < 2:
                continue

            prev_close = float(df["Close"].iloc[-2])
            last_close = float(df["Close"].iloc[-1])

            day_low = float(df["Low"].iloc[-1])
            day_high = float(df["High"].iloc[-1])

            pct_change = (last_close - prev_close) / prev_close * 100
            vol = abs(pct_change)

            results.append({
                "Ticker": t,
                "Prev_Close": round(prev_close, 2),
                "Last_Close": round(last_close, 2),
                "Day_Low": round(day_low, 2),
                "Day_High": round(day_high, 2),
                "Pct_Change": round(pct_change, 2),
                "Volatility": round(vol, 2)
            })

        except Exception:
            continue

    df = pd.DataFrame(results)

    if df.empty:
        return df

    df["Volatility"] = pd.to_numeric(df["Volatility"], errors="coerce")
    df = df.dropna(subset=["Volatility"])

    return df.sort_values("Volatility", ascending=False)

# ---------------------------------------------------------
# Run volatility scan
# ---------------------------------------------------------
st.subheader("NDX – Last Day Volatility Movers")

vol_df = get_last_day_volatility(NDX_TICKERS)

if vol_df.empty:
    st.warning("No volatility data returned. Try again later.")
else:
    st.write("### 🔥 Top 20 Most Volatile Tickers (Last Day)")
    st.dataframe(vol_df.head(20), use_container_width=True)

    st.write("---")
    st.write("### 📉 Biggest Losers (Negative % Change)")
    losers = vol_df[vol_df["Pct_Change"] < 0].sort_values("Pct_Change")
    st.dataframe(losers.head(10), use_container_width=True)

    st.write("---")
    st.write("### 📈 Biggest Gainers (Positive % Change)")
    gainers = vol_df[vol_df["Pct_Change"] > 0].sort_values("Pct_Change", ascending=False)
    st.dataframe(gainers.head(10), use_container_width=True)

    st.write("---")
    st.write("### 📊 Full NDX Volatility Table (All Tickers)")

    st.dataframe(vol_df, use_container_width=True, height=600)