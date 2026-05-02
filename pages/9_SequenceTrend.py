import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("📉 Mean + Slope Scanner (Oscillation Stats + Trend)")

# ---------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------
tickers_input = st.text_area("Tickers (comma separated)", "FMC,BAX,BBWI,BEN,CPB,CZR,GEN,HRL,HST,INVH,IVZ,KEY,KIM,MOS,NWSA,RF,RHI,VICI,WY,XRAY,AES")
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# ---------------------------------------------------------
# GET COMPANY NAME
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_company_name(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("shortName") or info.get("longName") or "N/A"
    except:
        return "N/A"

# ---------------------------------------------------------
# FETCH LAST 10 CLOSES (SAFE VERSION)
# ---------------------------------------------------------
def fetch_last_10(ticker):
    df = yf.download(
        ticker,
        period="2mo",
        interval="1d",
        progress=False
    )

    if df is None or df.empty:
        return None

    # Fix MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Ensure Close column exists
    if "Close" not in df.columns:
        if "Adj Close" in df.columns:
            df["Close"] = df["Adj Close"]
        else:
            return None

    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna(subset=["Close"])

    if df.empty:
        return None

    return df.tail(10)

# ---------------------------------------------------------
# OSCILLATION STATS (YES/NO + MIN/MAX/MEAN)
# ---------------------------------------------------------
def oscillation_stats(closes, threshold=5.0):
    pct_changes = closes.pct_change().dropna() * 100

    osc_yes_no = "YES" if any(abs(pct_changes) > threshold) else "NO"

    return {
        "Oscillation": osc_yes_no,
        "Osc_Min": round(pct_changes.min(), 2),
        "Osc_Max": round(pct_changes.max(), 2),
        "Osc_Mean": round(pct_changes.mean(), 2)
    }

# ---------------------------------------------------------
# TREND BASED ON SLOPE OF LAST 5 CLOSES
# ---------------------------------------------------------
def classify_trend_slope(df):
    closes = df["Close"].astype(float).tail(5).values

    if len(closes) < 3:
        return "NO_DATA"

    x = np.arange(len(closes), dtype=float)
    slope, intercept = np.polyfit(x, closes, 1)

    if slope > 0:
        return "UP"
    elif slope < 0:
        return "DOWN"
    else:
        return "FLAT"

# ---------------------------------------------------------
# RUN SCAN
# ---------------------------------------------------------
if st.button("Run Scan"):
    results = []

    for t in tickers:
        df = fetch_last_10(t)
        if df is None or len(df) < 5:
            results.append({
                "Ticker": t,
                "Name": get_company_name(t),
                "Last Price": None,
                "Mean (10)": None,
                "Oscillation": "NO_DATA",
                "Osc_Min": None,
                "Osc_Max": None,
                "Osc_Mean": None,
                "Trend": "NO_DATA"
            })
            continue

        closes = df["Close"].astype(float)

        # Oscillation stats
        osc = oscillation_stats(closes)

        # Trend classification (last 5 closes slope)
        trend = classify_trend_slope(df)

        results.append({
            "Ticker": t,
            "Name": get_company_name(t),
            "Last Price": round(closes.iloc[-1], 2),
            "Mean (10)": round(closes.mean(), 2),
            "Oscillation_5%": osc["Oscillation"],
            "Osc_Min": osc["Osc_Min"],
            "Osc_Max": osc["Osc_Max"],
            "Osc_Mean": osc["Osc_Mean"],
            "Trend": trend
        })

    df_results = pd.DataFrame(results)
    st.subheader("📊 Results")
    st.dataframe(df_results, hide_index=True, width="stretch")




