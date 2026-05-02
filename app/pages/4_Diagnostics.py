import sys
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
from engine_pkg.backtest import BacktestConfig, run_backtest


# ---------------------------------------------------------
# Sidebar Settings Panel
# ---------------------------------------------------------
st.sidebar.header("⚙️ Backtest Settings")

start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2025-12-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2026-03-06"))

budget = st.sidebar.number_input("Budget", value=500.0)
stop_loss = st.sidebar.number_input("Stop Loss (%)", value=-0.03)
take_profit = st.sidebar.number_input("Take Profit (%)", value=0.03)

run_button = st.sidebar.button("Run Backtest")


# ---------------------------------------------------------
# Page Title
# ---------------------------------------------------------
st.title("📊 Backtest Diagnostics (Page 2)")
st.write("This page shows the raw backtest output and the diagnostic skip log.")


# ---------------------------------------------------------
# Run Backtest
# ---------------------------------------------------------
if run_button:

    cfg = BacktestConfig(
        start_date=str(start_date),
        end_date=str(end_date),
        budget=budget,
        stop_loss_pct=stop_loss,
        take_profit_pct=take_profit,
        intraday_interval="5m",
        tickers=("TQQQ", "SQQQ"),
    )

    trades, skipped = run_backtest(cfg)

    # -----------------------------------------------------
    # Trades Table
    # -----------------------------------------------------
    st.subheader("Trades Executed")
    if trades.empty:
        st.info("No trades executed in this period.")
    else:
        st.dataframe(trades)

    # -----------------------------------------------------
    # Skipped Days Table
    # -----------------------------------------------------
    st.subheader("Skipped Days (Diagnostic Dashboard)")
    if skipped.empty:
        st.info("No skipped days logged.")
    else:
        st.dataframe(skipped.sort_values("Date"))

# ---------------------------------------------------------
# Key Definitions
# ---------------------------------------------------------
st.markdown("## 📘 Key Definitions")

st.markdown("""
**Executed Trades**  
Days where the system allowed a trade and the entry/exit logic was triggered.

**Skipped Days**  
Days where the system blocked trading due to weak signals or risk filters.

**No‑Trade Zone (Weak Ratio)**  
Occurs when TQQQ and SQQQ weights are too close to 50/50.  
Indicates low conviction and high noise.

**Trend Filter (SMA10)**  
A safety rule requiring the ETF to be above its 10‑day moving average before entering a trade.

**Exit Reason**  
Why the trade closed:  
- **close** → end‑of‑day exit  
- **stop_loss** → max loss threshold hit  
- **take_profit** → max gain threshold hit

**PnL / Return**  
Profit or loss from the trade, expressed in dollars or percentage.

**Equity Curve**  
Running account value after each trade.
""")    