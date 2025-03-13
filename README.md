# AirdropSellBot

A Python-based script for **automated token selling** on cryptocurrency exchanges. Supports **Binance**, **OKX**, and **Bybit** with a unified interface for checking balances, placing limit orders, and executing fast sales. Designed to monitor an asset balance and sell it instantly when available, optimizing price calculation for quick execution.

---

## ✨ Features

- **Balance Check**: Monitor the balance of a specific asset in real-time.
- **Order Retrieval**: Fetch open buy/sell orders for a trading pair.
- **Price Optimization**: Calculate the best selling price based on order book data.
- **Instant Selling**: Automatically sell tokens as soon as the balance becomes non-zero.
- **Order Management**: Retry or cancel orders if they don’t execute within 3 seconds.

---

## 🏦 Supported Exchanges

- **Binance** (via `python-binance`)
- **OKX** (via `python-okx`)
- **Bybit** (via `pybit`)

---

## 📋 Requirements

- **Python**: 3.7 or higher
- **Dependencies**: 
  - `python-binance`
  - `python-okx`
  - `pybit`

Install them with:
```bash
pip install python-binance python-okx pybit
