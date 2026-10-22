# Five minute demonstration

## Business question
Which operating drivers explain the profit shortfall, and how much cash remains if demand weakens while inventory turns slow?

1. Start on Summary. Identify that the case contains synthetic data and point to the modeled results, not realized business benefits.
2. Show the actual-vs-budget bridge. Explain why volume is valued at budget weighted margin and mix is a separate effect. Verify the residual is zero within rounding.
3. Change Assumptions D5 from 1 to 2. Explain that lower demand, weaker pricing, cost inflation, slower inventory turns and shorter supplier terms collectively reduce cash.
4. Trace merchandise COGS into inventory and AP. Fulfillment is expensed and should not inflate inventory balances. Explain why depreciation reduces earnings but is added back in cash flow.
5. Open the native PivotTable and filter Region. Conclude with the memo's proposed actions and assumptions that require validation.

## Questions to prepare for

- Why is a seasonal benchmark better here? The synthetic generator contains holiday seasonality. Never generalize this test to real demand forecasting.
- How did you avoid leakage? Backtest predictions use only 2025 data. The forward June 2026 forecast can use actuals available by its as-of date.
- Why no ML model? Eighteen months is a small dataset. A transparent benchmark and reconciled financial drivers are more defensible than unsupported complexity.
- What changes with a real deployment? Replace generated CSVs, validate source grain and mapping, use merchandise-ledger balances, calibrate mix/price elasticity, add financing and reserves where needed, obtain finance-owner sign-off.
- What does the project prove? You can build a reproducible case model and explain its tradeoffs. It does not prove actual company savings or stakeholder influence.
