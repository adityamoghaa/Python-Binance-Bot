# Python Binance Futures Testnet Bot

A lightweight command-line trading bot for Binance USDT-M Futures Testnet, written in Python with the `python-binance` SDK.

## Overview

This project provides a simple interactive workflow for placing futures orders from the terminal while keeping the core trading actions encapsulated in a reusable `BasicBot` class.

## Features

- Place **MARKET** orders
- Place **LIMIT** orders
- Place **STOP_MARKET** orders (labeled as stop-limit in CLI flow)
- Input validation for order side and quantity
- File-based logging to `trading_bot.log`
- Basic exception handling for Binance API failures

## Tech Stack

- Python 3.7+
- [`python-binance`](https://pypi.org/project/python-binance/)

## Getting Started

### 1) Create Binance Testnet API Credentials

1. Visit the [Binance Futures Testnet](https://testnet.binancefuture.com/).
2. Generate your API Key and API Secret.

### 2) Install Dependencies

```bash
pip install python-binance
```

### 3) Run the Bot

```bash
python trading_bot.py
```

### 4) Follow the Interactive Prompts

You will be prompted for:
- API key and secret
- Symbol (for example, `BTCUSDT`)
- Order type (`market`, `limit`, `stop-limit`)
- Side (`buy` / `sell`)
- Quantity (and price fields where applicable)

## Project Structure

```text
Python-Binance-Bot/
├── trading_bot.py
├── README.md
└── LICENSE
```

## Logging

The bot writes runtime logs to:

```text
trading_bot.log
```

This includes initialization details, order attempts, API responses, and errors.

## Security Notes

- Never share or commit your API credentials.
- Use testnet keys only unless you intentionally switch to live trading endpoints.
- Consider using environment variables or a secrets manager for production-grade key handling.

## Disclaimer

This project is intended for educational and testing purposes. Use at your own risk.
