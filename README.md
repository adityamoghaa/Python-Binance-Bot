# Python-Binance-Bot
A simplified trading bot for the Binance Futures Testnet, built in Python using the `python-binance` library.

## Features

- **Market & Limit Orders:** Place buy/sell orders on USDT-M Futures.
- **Stop-Limit Orders (Bonus):** Example advanced order type included.
- **Command-Line Interface:** User-friendly prompts for order input and validation.
- **Logging:** All API requests, responses, and errors are logged to `trading_bot.log`.
- **Reusable Structure:** Core logic in a class for easy extension and reuse.
- **Error Handling:** Graceful failure and clear feedback.

## Requirements

- Python 3.7+
- `python-binance` library

## Getting Started

1. **Register a Binance Futures Testnet account:**
   - Go to [Binance Futures Testnet](https://testnet.binancefuture.com).
   - Create an account and generate API credentials (API Key & Secret).

2. **Install dependencies:**
   ```bash
   pip install python-binance
   ```

3. **Run the bot:**
   ```bash
   python basic_trading_bot.py
   ```

4. **Follow the CLI prompts:**
   - Enter your API Key and Secret.
   - Choose order types, symbol, side, quantity, and price as needed.

## File Structure

```
Python-Binance-Bot/
├── README.md
├── basic_trading_bot.py
└── trading_bot.log
```

## Example Usage

```bash
$ python basic_trading_bot.py
Welcome to the Simplified Binance Futures Testnet Trading Bot!
Enter your API Key: <your-api-key>
Enter your API Secret: <your-api-secret>

Supported symbols: BTCUSDT, ETHUSDT, etc. (USDT-M Futures)
Order Types: market, limit, stop-limit (bonus)
Symbol: BTCUSDT
Order type (market/limit/stop-limit): market
Side (buy/sell): buy
Quantity: 0.001
Order placed successfully!
{ ...order details... }
```

## Extending the Bot

- Add more order types by extending the `BasicBot` class.
- For a more advanced CLI, consider integrating `argparse` or a simple web frontend.

## Disclaimer

- This bot is for educational and testing purposes **ONLY**.
- It uses the **Binance Futures Testnet** and does **not** trade real funds.
- Always keep your API keys private.

---

Thank You!
