# trading_alert_bot.py

import pandas as pd
import numpy as np
import streamlit as st
import smtplib
from email.mime.text import MIMEText

# --- USER SETTINGS ---
TICKERS = ["TQQQ", "SQQQ"]
EMAIL_TO = "atorquez@hotmail.com"  # Replace with your email
EMAIL_FROM = "streamlitbot@example.com"
EMAIL_PASSWORD = "your-app-password"  # SMTP or App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- 1. Load historical data (previous day) ---
def load_historical_data(ticker):
    # Replace with your data source
    # Example: CSV with 'Open', 'High', 'Low', 'Close' columns
    df = pd.read_csv(f"{ticker}_1day.csv")
    return df

# --- 2. Calculate statistical entry & exit ---
def calculate_entry_exit(df):
    # Example using percentile of the day's low/high
    entry = np.percentile(df['Low'], 10)   # Ideal low
    exit_price = np.percentile(df['High'], 90)  # Target exit
    atr = df['High'].max() - df['Low'].min()   # Simple volatility
    stop = entry - 0.5 * atr
    return round(entry,2), round(exit_price,2), round(stop,2)

# --- 3. Send email alert ---
def send_email_alert(ticker, entry, stop, target):
    subject = f"{ticker} Trade Alert"
    body = f"""
    {ticker} Trade Alert
    -------------------
    Action: BUY
    Entry Price: {entry}
    Stop Loss: {stop}
    Target Exit: {target}
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        server.quit()
        st.success(f"Alert sent for {ticker}!")
    except Exception as e:
        st.error(f"Error sending email: {e}")

# --- 4. Main Streamlit App ---
st.title("TQQQ/SQQQ Trading Alert Bot")

for ticker in TICKERS:
    st.header(ticker)
    df = load_historical_data(ticker)
    entry, target, stop = calculate_entry_exit(df)
    st.write(f"Ideal Entry: {entry}, Target Exit: {target}, Stop Loss: {stop}")
   
    # Streamlit button to simulate price trigger
    if st.button(f"Send {ticker} Alert"):
        send_email_alert(ticker, entry, stop, target)

st.info("User executes trade manually based on email alerts.")

# tqqq_sqqq_alert_bot.py
import yfinance as yf
import numpy as np
import streamlit as st
import smtplib
from email.mime.text import MIMEText

# --- USER SETTINGS ---
TICKERS = ["TQQQ", "SQQQ"]
EMAIL_TO = "atorquez@hotmail.com"        # Replace with your email
EMAIL_FROM = "streamlitbot@example.com"  # Replace with your bot email
EMAIL_PASSWORD = "yqnb yrvv ttgx geib"     # SMTP/App password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- 1. Fetch previous day's data ---
def get_prev_day_data(ticker):
    data = yf.download(ticker, period="2d", interval="1d")
    if len(data) < 2:
        st.error(f"Not enough data for {ticker}")
        return None
    prev_day = data.iloc[-2]  # previous trading day
    return prev_day

# --- 2. Calculate statistical entry & exit ---
def calculate_entry_exit(prev_day):
    low = prev_day['Low']
    high = prev_day['High']
    close = prev_day['Close']
   
    # Ideal entry = low + 10% of day range (avoids spike lows)
    entry = low + 0.10 * (high - low)
   
    # Ideal exit = high - 10% of day range (avoids spike highs)
    exit_price = high - 0.10 * (high - low)
   
    # Stop = below entry by 50% of day range
    stop = entry - 0.5 * (high - low)
   
    return round(entry, 2), round(exit_price, 2), round(stop, 2)

# --- 3. Send email alert ---
def send_email_alert(ticker, entry, stop, target):
    subject = f"{ticker} Trade Alert"
    body = f"""
{ticker} Trade Alert
-------------------
Action: BUY
Entry Price: {entry}
Stop Loss: {stop}
Target Exit: {target}

Note: Execute manually based on this alert.
"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        server.quit()
        st.success(f"Alert sent for {ticker}!")
    except Exception as e:
        st.error(f"Error sending email: {e}")

# --- 4. Main Streamlit App ---
st.title("TQQQ/SQQQ Statistical Alert Bot")

for ticker in TICKERS:
    st.header(ticker)
    prev_day = get_prev_day_data(ticker)
    if prev_day is not None:
        entry, target, stop = calculate_entry_exit(prev_day)
        st.write(f"Ideal Entry: {entry}, Target Exit: {target}, Stop Loss: {stop}")
       
        # Optional: simulate price check or button
        if st.button(f"Send {ticker} Alert"):
            send_email_alert(ticker, entry, stop, target)

st.info("User executes trade manually based on email alerts.")