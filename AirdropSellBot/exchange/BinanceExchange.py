from typing import List, Tuple

from dotenv import load_dotenv
import os
from loguru import logger
from binance.client import Client as BinanceClient

from config import SUCCESS_BID_START_RATE
from exchange.Exchange import Exchange

load_dotenv()  # Загружаем переменные из .env

# Настройка логирования
logger.add("trade.log", rotation="1 MB")


# Реализация для Binance
class BinanceExchange(Exchange):
    def __init__(self):
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        if not api_key or not api_secret:
            logger.error("API ключи для Binance не найдены в .env")
            raise ValueError("API keys not provided")
        self.client = BinanceClient(api_key, api_secret)

    def create_symbol(self, assert_in: str, assert_out: str) -> str:
        return assert_in + assert_out

    def get_balance(self, asset: str, auto_transfer: bool = False) -> float:
        try:
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except Exception as e:
            print(f"Ошибка при получении баланса: {e}")
            return 0.0

    def get_open_orders(self, symbol: str) -> list:
        try:
            return self.client.get_open_orders(symbol=symbol)
        except Exception as e:
            print(f"Ошибка при получении ордеров: {e}")
            return []

    def calculate_sell_orders(self, symbol: str, quantity: float) -> List[Tuple[float, float]]:
        try:
            order_book = self.client.get_order_book(symbol=symbol)
            bids = order_book['bids'][1:]  # Пропускаем первый ордер
            logger.info(f"Получены биды для {symbol}: {[(float(price), float(qty)) for price, qty in bids]}")

            if not bids:
                logger.warning(f"Список бидов для {symbol} пуст")
                return []

            orders = []
            remaining_qty = quantity
            success_rate = SUCCESS_BID_START_RATE

            for bid_price, bid_qty in bids:
                bid_price = float(bid_price)
                bid_qty = float(bid_qty)
                sell_qty = bid_qty * success_rate

                if sell_qty >= remaining_qty:
                    orders.append((bid_price, remaining_qty))
                    return orders

                orders.append((bid_price, sell_qty))
                remaining_qty -= sell_qty
                success_rate += 0.05

            if remaining_qty > 0 and bids:
                last_price = float(bids[-1][0])
                orders.append((last_price, remaining_qty))
            return orders
        except Exception as e:
            print(f"Ошибка при вычислении ордеров: {e}")
            return []

    def place_sell_order(self, symbol: str, quantity: float, price: float) -> str:
        try:
            order = self.client.order_limit_sell(symbol=symbol, quantity=quantity, price=price)
            return order['orderId']
        except Exception as e:
            print(f"Ошибка при выставлении ордера: {e}")
            return ""

    def cancel_order(self, order_id: str, symbol: str):
        try:
            self.client.cancel_order(symbol=symbol, orderId=order_id)
        except Exception as e:
            print(f"Ошибка при отмене ордера: {e}")

    def check_order_status(self, order_id: str, symbol: str) -> bool:
        try:
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            return order['status'] == 'FILLED'
        except Exception as e:
            print(f"Ошибка при проверке статуса ордера: {e}")
            return False