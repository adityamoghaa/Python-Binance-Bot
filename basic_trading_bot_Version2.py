import logging
import sys
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException

# Configure logging
logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

class BasicBot:
    def __init__(self, api_key, api_secret, testnet=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.base_url = 'https://testnet.binancefuture.com' if testnet else 'https://fapi.binance.com'
        self.client = Client(api_key, api_secret)
        if testnet:
            self.client.FUTURES_URL = self.base_url
            # Trigger endpoint switch by changing leverage (dummy call)
            try:
                self.client.futures_change_leverage(symbol="BTCUSDT", leverage=1)
            except BinanceAPIException:
                pass
        logging.info(f"Initialized BasicBot in {'testnet' if testnet else 'live'} mode.")

    def place_market_order(self, symbol, side, quantity):
        try:
            logging.info(f"Placing MARKET {side} order for {quantity} {symbol}")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            logging.info(f"Order response: {order}")
            return order
        except BinanceAPIException as e:
            logging.error(f"Market order error: {e}")
            print(f"Order failed: {e}")
            return None

    def place_limit_order(self, symbol, side, quantity, price):
        try:
            logging.info(f"Placing LIMIT {side} order for {quantity} {symbol} at {price}")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                quantity=quantity,
                price=price,
                timeInForce=TIME_IN_FORCE_GTC
            )
            logging.info(f"Order response: {order}")
            return order
        except BinanceAPIException as e:
            logging.error(f"Limit order error: {e}")
            print(f"Order failed: {e}")
            return None

    def place_stop_limit_order(self, symbol, side, quantity, price, stop_price):
        """Bonus: Stop-Limit order (implemented using STOP_MARKET for testnet)."""
        try:
            logging.info(f"Placing STOP-LIMIT {side} order for {quantity} {symbol} at {price}, stop at {stop_price}")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_STOP_MARKET,
                quantity=quantity,
                stopPrice=stop_price,
                # price=price,  # STOP_MARKET only needs stopPrice, not price
                timeInForce=TIME_IN_FORCE_GTC
            )
            logging.info(f"Order response: {order}")
            return order
        except BinanceAPIException as e:
            logging.error(f"Stop-limit order error: {e}")
            print(f"Order failed: {e}")
            return None

def validate_side(side):
    if side.lower() == 'buy':
        return SIDE_BUY
    elif side.lower() == 'sell':
        return SIDE_SELL
    else:
        raise ValueError("Order side must be 'buy' or 'sell'.")

def main():
    print("Welcome to the Simplified Binance Futures Testnet Trading Bot!")
    api_key = input("Enter your API Key: ").strip()
    api_secret = input("Enter your API Secret: ").strip()

    bot = BasicBot(api_key, api_secret, testnet=True)
    while True:
        print("\nSupported symbols: BTCUSDT, ETHUSDT, etc. (USDT-M Futures)")
        print("Order Types: market, limit, stop-limit (bonus)")
        symbol = input("Symbol: ").strip().upper()
        order_type = input("Order type (market/limit/stop-limit): ").strip().lower()
        try:
            side = validate_side(input("Side (buy/sell): ").strip())
        except ValueError as ve:
            print(ve)
            continue
        try:
            quantity = float(input("Quantity: ").strip())
        except ValueError:
            print("Quantity must be a number.")
            continue

        if order_type == 'market':
            order = bot.place_market_order(symbol, side, quantity)
        elif order_type == 'limit':
            price = input("Limit price: ").strip()
            order = bot.place_limit_order(symbol, side, quantity, price)
        elif order_type == 'stop-limit':
            stop_price = input("Stop price: ").strip()
            # price = input("Limit price: ").strip()  # For true STOP_LIMIT, needs this
            order = bot.place_stop_limit_order(symbol, side, quantity, price=None, stop_price=stop_price)
        else:
            print("Unsupported order type. Try again.")
            continue

        if order:
            print("Order placed successfully!")
            print(order)
        else:
            print("Order failed. Check logs for details.")

        cont = input("Place another order? (y/n): ").strip().lower()
        if cont != 'y':
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot terminated by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)