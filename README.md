# Multi Asset Trading Back-tester

## Overview

This project implements a systematic trend-following strategy across multiple indices.

## Features

- ATR-based risk management
- Dynamic position sizing
- Portfolio aggregation
- Monte Carlo simulation
- Trade journal generation
- Equity curve analysis
- Drawdown analysis

## Strategy Logic

### Entry Conditions

- Close above Fast SMA
- Open below Fast SMA
- ATR above threshold
- Fast SMA below Slow SMA
- Negative Slow SMA slope

### Exit Conditions

- 2R Take Profit
- 1R Stop Loss
