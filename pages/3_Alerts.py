import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.title("📧 Email Alerts Configuration")

st.write("""
This page manages the Wishing Well email alert system.

**Important Rules:**
- Alerts are sent **only after market close**
- **BUY alerts require action**
- **SELL alerts are informational only**
- No intraday alerts are ever sent
""")

# -----------------------------
# 1. USER INPUTS FOR EMAIL SETUP
# -----------------------------
st.subheader("Email Settings (Gmail)")

sender_email = st.text_input("Your Gmail Address")
app_password = st.text_input("Gmail App Password", type="password")
recipient_email = st.text_input("Recipient Email Address")

# -----------------------------
# 2. EMAIL SENDING FUNCTIONS
# -----------------------------
def send_email(subject, body, sender, password, recipient):
    """Generic Gmail SMTP sender."""
    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())

        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# -----------------------------
# 3. BUY EMAIL TEMPLATE
# -----------------------------
def send_buy_email(ticker, block, entry_price, sell_gain_price, sell_percentile_price):
    subject = "Wishing Well Alert — BUY Signal Triggered"

    body = f"""
Your Wishing Well model has detected a valid BUY opportunity at today's market close.

ETF: {ticker}
Block: {block}
Entry Price: {entry_price}

Sell Target (Gain): {sell_gain_price}
Sell Target (Percentile): {sell_percentile_price}

Action Required:
Place a BUY order for Block {block} at or near {entry_price}.
Immediately set your SELL limit order(s) at the target price(s) above.

This signal is based on final closing data. No intraday action is needed.
"""

    return send_email(subject, body, sender_email, app_password, recipient_email)


# -----------------------------
# 4. SELL EMAIL TEMPLATE
# -----------------------------
def send_sell_email(ticker, block, exit_price, gain_percent):
    subject = "Wishing Well Alert — SELL Executed"

    body = f"""
Your SELL order has been executed.

ETF: {ticker}
Exit Price: {exit_price}
Gain Achieved: {gain_percent}%
Block Closed: {block}

No action is required. Your position closed automatically based on your preset SELL limit order.

Your capital is now available for the next Wishing Well cycle.
"""

    return send_email(subject, body, sender_email, app_password, recipient_email)


# -----------------------------
# 5. TEST BUTTONS
# -----------------------------
st.subheader("Test Email Alerts")

col1, col2 = st.columns(2)

with col1:
    if st.button("Send Test BUY Email"):
        ok = send_buy_email(
            ticker="SQQQ",
            block=1,
            entry_price=70.63,
            sell_gain_price=71.69,
            sell_percentile_price=74.28
        )
        if ok:
            st.success("BUY email sent successfully!")

with col2:
    if st.button("Send Test SELL Email"):
        ok = send_sell_email(
            ticker="TQQQ",
            block=2,
            exit_price=47.82,
            gain_percent=2.0
        )
        if ok:
            st.success("SELL email sent successfully!")