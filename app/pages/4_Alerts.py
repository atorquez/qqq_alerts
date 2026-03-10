import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MIMEText
import time

st.title("Entry/Exit Levels (Percentile Model)")
st.write("Automated BUY/SELL alerts based on percentile thresholds and momentum.")

# ---------------------------------------------------------
# Sidebar: Email Settings
# ---------------------------------------------------------
st.sidebar.header("Email Settings")

from_email = st.sidebar.text_input("Gmail Address")
app_password = st.sidebar.text_input("Gmail App Password", type="password")
to_email = st.sidebar.text_input("Recipient Email")

# ---------------------------------------------------------
# Sidebar: Model Settings
# ---------------------------------------------------------
st.sidebar.header("Model Settings")

window = st.sidebar.slider("Days Window", 5, 20, 7)
entry_percentile = st.sidebar.slider("Entry Percentile", 5, 40, 25)
exit_percentile = st.sidebar.slider("Exit Percentile", 60, 95, 75)

# ---------------------------------------------------------
# Safe fetch with retries
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

        time.sleep(1)

    return df  # may be empty

@st.cache_data
def load_data(ticker):
    return safe_fetch(ticker)

# ---------------------------------------------------------
# Compute entry/exit safely
# ---------------------------------------------------------
def compute_levels(df, window, entry_p, exit_p):
    if df.empty or "Close" not in df.columns:
        return None, None, None, "NO_DATA"

    recent = df["Close"].tail(window)

    if recent.empty or len(recent) < 5:
        return None, None, None, "INSUFFICIENT_DATA"

    entry = float(np.percentile(recent, entry_p))
    exit = float(np.percentile(recent, exit_p))
    now = float(df["Close"].iloc[-1])

    return entry, exit, now, "OK"

# ---------------------------------------------------------
# Compute momentum safely
# ---------------------------------------------------------
def compute_momentum(df):
    if len(df) < 2:
        return "FLAT"

    today = float(df["Close"].iloc[-1])
    yesterday = float(df["Close"].iloc[-2])

    if today > yesterday:
        return "UP"
    elif today < yesterday:
        return "DOWN"
    else:
        return "FLAT"

# ---------------------------------------------------------
# Email sender
# ---------------------------------------------------------
def send_alert_email(subject, body, from_email, app_password, to_email):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(from_email, app_password)
        server.sendmail(from_email, [to_email], msg.as_string())

# ---------------------------------------------------------
# Load data for TQQQ and SQQQ
# ---------------------------------------------------------
tqqq = load_data("TQQQ")
sqqq = load_data("SQQQ")

st.write("**TQQQ Data Shape:**", tqqq.shape)
st.write("**SQQQ Data Shape:**", sqqq.shape)

# ---------------------------------------------------------
# Compute levels
# ---------------------------------------------------------
entry_t, exit_t, now_t, status_t = compute_levels(tqqq, window, entry_percentile, exit_percentile)
entry_s, exit_s, now_s, status_s = compute_levels(sqqq, window, entry_percentile, exit_percentile)

momentum_t = compute_momentum(tqqq)
momentum_s = compute_momentum(sqqq)

# ---------------------------------------------------------
# Handle missing data gracefully
# ---------------------------------------------------------
if status_t != "OK" or status_s != "OK":
    st.error("Not enough data to compute entry/exit levels. Try again later.")
    st.stop()

# ---------------------------------------------------------
# Signal logic
# ---------------------------------------------------------
signal_t = "HOLD"
signal_s = "HOLD"

if now_t <= entry_t and momentum_t == "UP":
    signal_t = "BUY"
elif now_t >= exit_t and momentum_t == "DOWN":
    signal_t = "SELL"

if now_s <= entry_s and momentum_s == "UP":
    signal_s = "BUY"
elif now_s >= exit_s and momentum_s == "DOWN":
    signal_s = "SELL"

# ---------------------------------------------------------
# Display metrics
# ---------------------------------------------------------
st.subheader("TQQQ Levels")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current", f"{now_t:.2f}")
col2.metric("Entry", f"{entry_t:.2f}")
col3.metric("Exit", f"{exit_t:.2f}")
col4.metric("Signal", signal_t)

st.subheader("SQQQ Levels")
col5, col6, col7, col8 = st.columns(4)
col5.metric("Current", f"{now_s:.2f}")
col6.metric("Entry", f"{entry_s:.2f}")
col7.metric("Exit", f"{exit_s:.2f}")
col8.metric("Signal", signal_s)

# ---------------------------------------------------------
# Email alert button
# ---------------------------------------------------------
if st.button("Send Test Email"):
    if not from_email or not app_password or not to_email:
        st.error("Missing email, app password, or recipient.")
    else:
        try:
            send_alert_email(
                subject="Test Alert",
                body="This is a test alert from your Streamlit engine.",
                from_email=from_email,
                app_password=app_password,
                to_email=to_email
            )
            st.success("Test email sent successfully!")
        except Exception as e:
            st.error(f"Failed to send test email: {e}")