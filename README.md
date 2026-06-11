Multi Asset Trading Back-tester


Overview

This project implements a systematic trend-following strategy across multiple indices.

Features:

ATR-based risk management
Dynamic position sizing
Portfolio aggregation
Monte Carlo simulation
Trade journal generation
Equity curve analysis
Drawdown analysis


Strategy Logic


Entry Conditions
Close above Fast SMA
Open below Fast SMA
ATR above threshold
Fast SMA below Slow SMA
Negative Slow SMA slope

Exit Conditions
2R Take Profit
1R Stop Loss


Risk Management
Risk per Trade: 2%
Dynamic Position Sizing


Portfolio-level analytics
Performance
Metric	         Value
Trades	         209
Win Rate	       43.06%
Profit Factor	   1.34
Sharpe Ratio	   2.19
Return	         95.99%
Max Drawdown	   36.94%

Monte Carlo Results

Worst Case Scenario (5% Quantile)

Return: 11744
Max Drawdown: -5117
