import streamlit as st

st.title("📘 Instructions")
st.write("Welcome to the Wishing Well strategy guide.")

st.markdown("""
## TQQQ/SQQQ 3‑Block Strategy  
**Reactive, Percentile‑Based, Multi‑Day Leveraged ETF System**

---

## 1. Overview
This document describes a reactive, percentile‑based, multi‑day accumulation strategy for trading leveraged ETFs (TQQQ and SQQQ).

### The system uses:
- Nasdaq daily direction  
- Percentile‑based entry levels  
- A 3‑block capital architecture  
- Gain‑target or percentile exits  

### The strategy is designed to:
- Buy deeper during multi‑day streaks  
- Reduce average cost through structured block entries  
- Exit on statistically reliable rebounds  
- Avoid stop‑losses that disrupt cycle completion  
- Maintain discipline and risk control through block sizing  

---

## 2. Capital Architecture
Total capital is divided into **3 equal blocks**.

Example:
- Total: **$1,200**  
- Block 1: **$400**  
- Block 2: **$400**  
- Block 3: **$400**  

---

## 3. Market Signal (Nasdaq Direction)
- Nasdaq **UP** → Buy **SQQQ**  
- Nasdaq **DOWN** → Buy **TQQQ**  

This keeps the strategy aligned with short‑term market movement.

---

## 4. BUY Logic (Percentile‑Based)
Each day, the system calculates the **15th percentile entry price** for the appropriate ETF.

### Entry Ladder:
- Day 1 → BUY Price 1  
- Day 2 → BUY Price 2  
- Day 3 → BUY Price 3  

**Rule:** Each new BUY price must be lower than the previous one.

### 📌 Important: BUY Timing (End‑of‑Day Only)

All BUY decisions are made **after the market close**, never intraday.

This is essential because:

- Intraday direction is unstable and often reverses  
- The true daily direction is only known at the close  
- Percentile entry prices require the final daily candle  
- Buying intraday can break the 3‑block ladder  
- Early dips are often false signals  

**Therefore:  
All block entries (Block 1, Block 2, Block 3) are executed at the closing price only.**            

---

## 5. Block BUY Ladder

You buy **one block per day**, and **only after the market close**, when:

- The Nasdaq closing direction matches the ETF (DOWN → TQQQ, UP → SQQQ)  
- The new BUY price is lower than the previous day’s BUY
- You still have unused blocks  

This creates a disciplined 3‑step ladder:

- **Block 1** → shallow dip  
- **Block 2** → deeper dip  
- **Block 3** → deepest dip  

**No intraday buys are ever executed.  
All entries occur at the close to avoid false signals and maintain ladder integrity.**
        
 ---

## 6. SELL Logic
The system exits using whichever condition triggers first:

### A) Gain‑Target Exit
- Typically **+1.5% to +2.0%**  
- Fast and reliable  

### B) Percentile Exit
- Typically **60th–75th percentile**  
- Larger gains  

### 📌 Important: SELL all shares equal to exiting BUY to unclock al gains from the BUY            

---

## 7. No More BUYs After 3 Blocks
If the streak continues:
- Day 4 → **no more BUYs**  
- You hold and wait for the rebound exit  

---

## 8. Order Execution
### BUY Orders:
- Limit buy at the daily BUY price  
- **Executed only after the market close**  
- Never triggered intraday            
           
### SELL Orders:
- Limit sell at the daily SELL price  
- **Do NOT use trailing stops**  

---

## 9. Drawdown Handling
The system does **not** use stop‑losses because:
- Leveraged ETFs rebound strongly  
- Block averaging reduces cost  
- Stop‑losses often trigger before the rebound  

---

## 10. Real‑World Testing
- Day 1: Nasdaq DOWN → Block 1  
- Day 2: Nasdaq DOWN → Block 2  
- Day 3: Observe (DOWN → Block 3, UP → prepare for exit)  

---

## 11. Summary
This strategy is:
- Reactive, not predictive  
- Statistical, not emotional  
- Structured, not discretionary  
- Risk‑controlled through block sizing  
- Profitable through disciplined exits  
""")   