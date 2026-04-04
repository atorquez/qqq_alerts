import streamlit as st

st.title("📘 Instructions")
st.write("Welcome to the Wishing Well strategy guide.")

st.markdown("""
Wishing Well Strategy — TQQQ/SQQQ Model  
Volatility‑Aware, Asymmetric, Multi‑Engine Leveraged ETF System
With Real‑World Execution Rules (MOC / Manual Close Execution)
---
1. Core Philosophy
• 	TQQQ = Recovery asset (3× long NDX)
• 	SQQQ = Tactical hedge (–3× short NDX)
• 	Index anchor: Nasdaq‑100 (NDX), not Nasdaq Composite
• 	Volatility drives opportunity
• 	All BUY decisions are based on the closing price
• 	Execution must occur at the close, not after
• 	If you cannot execute at the close, you skip the BUY
• 	System is reactive, not predictive
---
2. Capital Architecture
• 	Total capital is divided into 3 equal TQQQ blocks.
• 	SQQQ uses at most 1 block (never laddered).
• 	No averaging down SQQQ.
• 	TQQQ can use all 3 blocks in a down‑continuation sequence.
---
3. Market Signal (NDX Direction)
• 	NDX DOWN → TQQQ engines active
• 	NDX UP → SQQQ engine active
• 	Volatility magnitude determines which engines activate (A/B/C).
---
4. BUY Engines (Price‑Based)

Engine A — TQQQ Rebound BUY
Purpose: Capture reversal after TQQQ was the loser.
BUY level:
TQQQ Close × 1.005
Block: Usually Block 1.          

Engine B — SQQQ Winner Discount BUY
Purpose: Capture deep pullback in SQQQ after it was the winner.
BUY zone:
SQQQ Close × 0.95 to 0.92
Block: 1 only (never laddered).

Engine C — TQQQ Deep‑Discount Continuation BUY
Purpose: Capture oversold continuation during multi‑day NDX declines.
BUY zone:
TQQQ Close × 0.94 to 0.92
Blocks: 2 and 3.  
---
5. Block Rules and Asymmetry
TQQQ (Recovery Asset)
• 	Max 3 blocks.
• 	Blocks 1–3 form the ladder.
• 	Average cost determines break‑even.
• 	Hold through downturns.
• 	Exit only when price > average.
• 	Never reset at a loss.
SQQQ (Tactical Hedge)
• 	Max 1 block.
• 	Never averaged down.
• 	Never held through a rebound.
• 	Sold quickly on +0.5% target or trailing stop.        
---
6. SELL Logic (Unified)
• 	Target: +0.5%
• 	Trailing stop: 0.3%
• 	Applies to all engines.
• 	When SELL triggers → all shares of that ETF are sold.
• 	After exit → that ETF’s cycle resets.
---
7. Reset Rules
• 	TQQQ: Reset only after profitable exit.
• 	SQQQ: Reset after each exit.
• 	Never reset mid‑drawdown.
• 	Never reset TQQQ before rebound.
---
8. Drawdown Handling
• 	No stop‑losses on TQQQ.
• 	No averaging down SQQQ.
• 	No more than 3 TQQQ blocks.
• 	No more than 1 SQQQ block.
• 	No intraday discretionary overrides.
---
9. Execution Rules (Updated for Real‑World Constraint)
The model requires closing‑price‑based BUY levels, but:
• 	You cannot buy the closing price after hours.
• 	You must execute at the close.
• 	If you cannot execute at the close, you skip the BUY.

9.1 BUY Execution Options
Option A — MOC (Market‑On‑Close) Order
• 	Must be placed before ~3:50 PM.
• 	Guarantees the official closing price.
• 	Best for Engines A and C.
• 	Works for SQQQ Engine B only if price is already in the BUY zone.

Option B — Manual Execution (3:58–4:00 PM)
• 	Watch the tape.
• 	Execute a market or limit order near the close.
• 	Achieves a price extremely close to the official close.
• 	Works for all engines.
---
9.2 If You Cannot Monitor the Close
• 	You skip the BUY for that day.
• 	You do not attempt after‑hours buying.
• 	You do not chase the price the next morning.
• 	You do not break the block ladder.
Skipping is always safer than forcing.
            
9.3 Why Skipping Is Safe
• 	The model is reactive, not predictive.
• 	Missing a BUY does not break the system.
• 	You never violate risk limits.
• 	You never distort the block structure.
• 	You avoid emotional or forced trades.
• 	You maintain mathematical integrity.

9.4 Future Automation
The app will eventually:
• 	Detect NDX direction at 3:59 PM.
• 	Trigger the correct engine.
• 	Place MOC orders automatically.
• 	Log fills.
• 	Update blocks.
• 	Maintain full automation of the ladder.
---
10. Daily Workflow (Updated)
After the close (night before):
• 	Calculate BUY levels for Engines A/B/C.
• 	Determine active engines.
• 	Prepare next‑day plan.
During the next day:
• 	If you can monitor the close → execute via MOC or manual.
• 	If not → skip BUY.
After the close:
• 	Record fills.
• 	Update average cost (TQQQ).
• 	Recalculate BUY levels.
• 	Continue cycle.
---
11. Key Model Truths
• 	TQQQ rebounds; SQQQ decays.
• 	TQQQ = 3‑block recovery engine.
• 	SQQQ = 1‑block tactical hedge.
• 	NDX is the correct index.
• 	You never exceed block limits.
• 	You only need +3–6% rebound to recover a 3‑block TQQQ sequence.
• 	Execution must occur at the close, not after.            
---
Appendix — BUY & SELL Price Formulas

BUY Price (Percentile Method)
The BUY price is based on the selected BUYPercentile applied to the last N daily closing prices.

Formula
BUY Price = Percentile(Recently Daily Closes, BUYPercentile)  

Interpretation
A lower percentile (e.g., 15%) identifies a pullback level, where price is relatively low compared to recent history.
  
SELL Price (Closing Method)           

A. SELL #1 — Safety Exit (+1.5%)
Formula SELL Price = BUY Price * (1 + 1.015)

B. SELL #2 — Optimal Exit (+2.0%)

Formula
SELL Price = BUY Price * (1 + 1.020)
            
C. SELL #3 — Percentile SELL (Exit Percentile)
This uses the SELLPercentile applied to the same recent daily closes.

Formula
SELL Price = Percentile(Recently Daily Closes, SELLPercentile)

""")