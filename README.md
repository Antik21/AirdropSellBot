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

### Extra
**Metamask transfer script**: Await selected asset on your wallet and immediately transfer it to prefield wallet address
  

---

## 🏦 Supported Exchanges

- **Binance** (via `python-binance`)
- **OKX** (via `python-okx`)
- **Bybit** (via `pybit`)
- **Gate.IO** (via `gate-api`)
- **MEXC** (In progress)

---

## ⚙️ Selling Logic

TokenSniper automates the selling process with the following steps:

1. **User Input**:
   - The user selects an exchange (e.g., 1 for OKX, 2 for Bybit, 3 for Binance, 4 for Gate.io).
   - The user specifies the asset symbol to sell (e.g., `BTC`) and the percentage of the balance to sell (e.g., `0.5` for 50%).
   - The script then initiates the selling logic.

2. **Balance Monitoring**:
   - Every second, the bot checks the wallet balance for the specified asset.
   - As soon as the balance becomes non-zero (e.g., when tokens arrive on the account), the selling process starts.

3. **Limit Order Execution**:
   - The bot retrieves the list of bids from the order book for the trading pair (e.g., `BTC_USDT`).
   - It calculates one or more limit orders based on the bid prices, optimizing for successful execution. The price is derived from the order book to ensure the order matches existing demand.

4. **Order Management**:
   - If an order fails to execute within 3 seconds or the market price changes significantly, the bot cancels the order.
   - It then recalculates a new order with updated prices from the latest order book data.
   - This process repeats until the entire specified percentage of the asset is sold.

5. **Completion**:
   - The bot continues placing and managing orders until all tokens are successfully sold, ensuring the full amount is executed efficiently.

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

# Transfer
METAMASK_PRIVATE_KEY=metamask_pk
EXCHANGE_WALLET_ADDRESS=exchange_wallet
TOKEN_CONTRACT_ADDRESS=token_contract
```

## Donations
If you find this project helpful and would like to support its development, consider making a donation:
[![Buy Me a Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/antiglobalist)

Arbitrum USDT 0x3E92ac8A955c0CcaA3abE350A7097b4e8aAFB5c5

Your support is greatly appreciated!

**Developed by** [Antiglobalist](https://t.me/deni_rodionov)
