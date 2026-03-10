import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MIMEText

# ---------------------------------------------------------
# Email helper (HOTMAIL / OUTLOOK VERSION)
# ---------------------------------------------------------
def send_alert_email(subject: str, body: str, from_email: str, app_password: str, to_email: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(from_email, app_password)
        server.sendmail(from_email, [to_email], msg.as_string())

# ---------------------------------------------------------
# Percentile-based entry/exit model (same as Page 3)
# ---------------------------------------------------------
@st.cache_data
def load_data(ticker):
    df = yf.download(
        ticker,
        period="3mo",
        interval="1d",
        progress=False
    )
    df = df.dropna()
    return df

def compute_entry_exit(ticker, window, entry_pct, exit_pct):
    df = load_data(ticker)
    if df.empty:
        return None, None, None

    recent = df["Close"].tail(window)

    entry_price = float(np.percentile(recent, entry_pct))
    exit_price = float(np.percentile(recent, exit_pct))
    price_now = float(df["Close"].iloc[-1])

    return entry_price, exit_price, price_now

# ---------------------------------------------------------
# Momentum helper
# ---------------------------------------------------------
def get_momentum(ticker):
    df = load_data(ticker)
    close = df["Close"].dropna()

    if len(close) < 2:
        return "FLAT"

    today = float(close.iloc[-1])
    yesterday = float(close.iloc[-2])

    if today > yesterday:
        return "UP"
    elif today < yesterday:
        return "DOWN"
    else:
        return "FLAT"

# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------
st.title("📨 Percentile-Based Alerts (Email) — Hotmail Ready")

st.write(
    "This page uses the **same percentile entry/exit model as Page 3**, "
    "checks live prices and momentum, and optionally sends email alerts."
)

st.sidebar.header("Alert Settings")

window = st.sidebar.slider("Days Window", 5, 20, 7)
entry_pct = st.sidebar.slider("Entry Percentile", 5, 40, 25)
exit_pct = st.sidebar.slider("Exit Percentile", 60, 95, 75)

enable_email = st.sidebar.checkbox("Enable Email Alerts", value=True)

from_email = st.sidebar.text_input("From Email (Hotmail/Outlook)", "atorquez@hotmail.com")
app_password = st.sidebar.text_input("Email App Password", type="password")
to_email = st.sidebar.text_input("Alert Recipient Email", "atorquez@hotmail.com")

st.sidebar.markdown(
    "**Important:** Use a Microsoft *App Password* (not your real password). "
)

st.divider()

# ---------------------------------------------------------
# Send Test Email Button
# ---------------------------------------------------------
st.subheader("Email System Test")

if st.button("Send Test Email"):
    if not from_email or not app_password or not to_email:
        st.error("Missing email, app password, or recipient.")
    else:
        try:
            send_alert_email(
                subject="Test Email from TQQQ/SQQQ Alert System",
                body="This is a test email confirming your Hotmail SMTP settings are working.",
                from_email=from_email,
                app_password=app_password,
                to_email=to_email
            )
            st.success("Test email sent successfully!")
        except Exception as e:
            st.error(f"Failed to send test email: {e}")

st.divider()

# ---------------------------------------------------------
# Compute entry/exit for both tickers
# ---------------------------------------------------------
st.subheader("Entry/Exit Levels (Percentile Model)")

entry_t, exit_t, price_t_now = compute_entry_exit("TQQQ", window, entry_pct, exit_pct)
entry_s, exit_s, price_s_now = compute_entry_exit("SQQQ", window, entry_pct, exit_pct)

col1, col2 = st.columns(2)
with col1:
    st.metric("TQQQ Entry", f"{entry_t:.2f}")
    st.metric("TQQQ Exit", f"{exit_t:.2f}")
with col2:
    st.metric("SQQQ Entry", f"{entry_s:.2f}")
    st.metric("SQQQ Exit", f"{exit_s:.2f}")

st.divider()

# ---------------------------------------------------------
# Check signals + optionally send alerts
# ---------------------------------------------------------
st.subheader("Signal Check & Alerts")

if st.button("Check Signals & Send Alerts"):
    alerts = []

    # ---------- TQQQ ----------
    mom_t = get_momentum("TQQQ")
    signal_t = "HOLD"

    if price_t_now <= entry_t and mom_t == "UP":
        signal_t = "BUY"
    elif price_t_now >= exit_t and mom_t == "DOWN":
        signal_t = "SELL"

    alerts.append({
        "Ticker": "TQQQ",
        "Price": price_t_now,
        "Entry": entry_t,
        "Exit": exit_t,
        "Momentum": mom_t,
        "Signal": signal_t,
    })

    # ---------- SQQQ ----------
    mom_s = get_momentum("SQQQ")
    signal_s = "HOLD"

    if price_s_now <= entry_s and mom_s == "UP":
        signal_s = "BUY"
    elif price_s_now >= exit_s and mom_s == "DOWN":
        signal_s = "SELL"

    alerts.append({
        "Ticker": "SQQQ",
        "Price": price_s_now,
        "Entry": entry_s,
        "Exit": exit_s,
        "Momentum": mom_s,
        "Signal": signal_s,
    })

    df_alerts = pd.DataFrame(alerts)
    st.write("### Current Signals")
    st.dataframe(df_alerts)

    actionable = [a for a in alerts if a["Signal"] in ("BUY", "SELL")]

    if actionable and enable_email:
        if not from_email or not app_password or not to_email:
            st.error("Email alerts enabled, but email/app password/recipient are missing.")
        else:
            for a in actionable:
                subject = f"{a['Ticker']} {a['Signal']} Signal Triggered"
                body = f"""
Ticker: {a['Ticker']}

Current Price: {a['Price']:.2f}
Entry Level:   {a['Entry']:.2f}
Exit Level:    {a['Exit']:.2f}
Momentum:      {a['Momentum']}

Suggested Action: {a['Signal']}
"""
                try:
                    send_alert_email(subject, body, from_email, app_password, to_email)
                    st.success(f"Email alert sent for {a['Ticker']} ({a['Signal']}).")
                except Exception as e:
                    st.error(f"Failed to send email for {a['Ticker']}: {e}")

    elif actionable and not enable_email:
        st.info("Actionable signals detected, but email alerts are disabled.")
    else:
        st.info("No BUY/SELL signals at this time.")

else:
    st.info("Press **'Check Signals & Send Alerts'** to evaluate signals and optionally send email alerts.")