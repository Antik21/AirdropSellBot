# AirdropSellBot

A Python-based script for **automated token selling** on cryptocurrency exchanges. Supports **Binance**, **OKX**, **Bybit**, and **Gate** with a unified interface for checking balances, placing limit orders, and executing fast sales. Designed to monitor an asset balance and instantly sell tokens via limit orders as soon as they arrive on the account, optimizing price calculation for successful execution. For OKX, it automatically transfers funds from the Funding to the Trading account to enable immediate trading.

---

## ✨ Features

- **Balance Check**: Monitor the balance of a specific asset in real-time.
- **Order Retrieval**: Fetch open buy/sell orders for a trading pair.
- **Price Optimization**: Calculate the optimal selling price based on order book data for successful limit order execution.
- **Instant Selling**: Automatically sell tokens via limit orders as soon as they arrive on the account (non-zero balance detected).
- **Order Management**: Retry or cancel limit orders if they don’t execute within 3 seconds.
- **OKX Auto-Transfer**: Automatically transfer funds from Funding to Trading account on OKX for seamless trading.

---

## 🏦 Supported Exchanges

- **Binance** (via `python-binance`)
- **OKX** (via `python-okx`)
- **Bybit** (via `pybit`)
- **Gate.IO** (via `gate-api`)

---

## 📋 Requirements

- **Python**: 3.7 or higher
- **Dependencies**: 
  - `python-binance`
  - `python-okx`
  - `pybit` ...

Install them with:
```bash
pip install python-binance python-okx pybit
```

### Create a `.env` File

To securely store your API keys, create a `.env` file in the root directory of the project. This file will hold your credentials for Binance, OKX, and Bybit. Here's how to set it up:

- **Step 1**: Create a file named `.env` in the root directory.
- **Step 2**: Add your API keys in the following format:

```
# Binance API keys
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# OKX API keys
OKX_API_KEY=your_okx_api_key_here
OKX_API_SECRET=your_okx_api_secret_here
OKX_PASSPHRASE=your_okx_passphrase_here

# Bybit API keys
BYBIT_API_KEY=your_bybit_api_key_here
BYBIT_API_SECRET=your_bybit_api_secret_here

# Gate API keys
GATE_API_KEY=your_gate_api_key_here
GATE_API_SECRET=your_gate_api_secret_here
```

## Donations
If you find this project helpful and would like to support its development, consider making a donation:
[![Buy Me a Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/antiglobalist)

Arbitrum USDT 0x3E92ac8A955c0CcaA3abE350A7097b4e8aAFB5c5

Your support is greatly appreciated!

**Developed by** [Antiglobalist](https://t.me/deni_rodionov)
