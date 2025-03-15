from typing import List, Tuple

from dotenv import load_dotenv
import os
from loguru import logger

from config import SUCCESS_BID_START_RATE
from exchange.Exchange import Exchange
from pybit.unified_trading import HTTP as BybitClient

load_dotenv()  # Загружаем переменные из .env

# Настройка логирования
logger.add("trade.log", rotation="1 MB")


# Реализация для Bybit
class BybitExchange(Exchange):
    def __init__(self):
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")
        if not api_key or not api_secret:
            logger.error("API ключи для Bybit не найдены в .env")
            raise ValueError("API keys not provided")
        self.client = BybitClient(testnet=False, api_key=api_key, api_secret=api_secret)

    def create_symbol(self, assert_in: str, assert_out: str) -> str:
        return assert_in + assert_out

    def get_balance(self, asset: str, auto_transfer: bool = False) -> float:
        try:
            result = self.client.get_wallet_balance(accountType="UNIFIED")
            for coin in result['result']['list'][0]['coin']:
                if coin['coin'] == asset:
                    logger.debug(f"Найден баланс для {asset}: {coin['walletBalance']}")
                    return float(coin['walletBalance'])
            logger.debug(f"Баланс для {asset} не найден, возвращаем 0")
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return 0.0

    def get_open_orders(self, symbol: str) -> list:
        try:
            result = self.client.get_open_orders(category="spot", symbol=symbol)
            orders = result['result']['list']
            logger.debug(f"Получены открытые ордера для {symbol}: {len(orders)} шт.")
            return orders
        except Exception as e:
            logger.error(f"Ошибка при получении ордеров: {e}")
            return []

    def calculate_sell_orders(self, symbol: str, quantity: float) -> List[Tuple[float, float]]:
        try:
            order_book = self.client.get_orderbook(category="spot", symbol=symbol, limit=10)
            bids = order_book['result']['b']  # Bybit возвращает bids как 'b'
            bids = bids[1:]  # Пропускаем первый ордер
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
                    logger.debug(f"Добавлен последний ордер: цена {bid_price}, объём {remaining_qty}")
                    return orders

                orders.append((bid_price, sell_qty))
                logger.debug(f"Добавлен ордер: цена {bid_price}, объём {sell_qty}")
                remaining_qty -= sell_qty
                success_rate += 0.05

            if remaining_qty > 0 and bids:
                last_price = float(bids[-1][0])
                orders.append((last_price, remaining_qty))
                logger.debug(f"Добавлен остаточный ордер: цена {last_price}, объём {remaining_qty}")
            logger.info(f"Итоговый список ордеров: {orders}")
            return orders
        except Exception as e:
            logger.error(f"Ошибка при вычислении ордеров: {e}")
            return []

    def place_sell_order(self, symbol: str, quantity: float, price: float) -> str:
        try:
            result = self.client.place_order(
                category="spot",
                symbol=symbol,
                side="Sell",
                orderType="Limit",
                qty=str(quantity),
                price=str(price)
            )
            if result['retCode'] == 0:
                order_id = result['result']['orderId']
                logger.debug(f"Ордер успешно выставлен: {order_id}")
                return order_id
            else:
                logger.error(f"Ошибка выставления ордера: {result['retMsg']}")
                return ""
        except Exception as e:
            logger.error(f"Ошибка при выставлении ордера: {e}")
            return ""

    def cancel_order(self, order_id: str, symbol: str):
        try:
            self.client.cancel_order(category="spot", symbol=symbol, orderId=order_id)
            logger.debug(f"Ордер {order_id} отменён")
        except Exception as e:
            logger.error(f"Ошибка при отмене ордера: {e}")

    def check_order_status(self, order_id: str, symbol: str) -> bool:
        try:
            result = self.client.get_order_history(category="spot", symbol=symbol, orderId=order_id)
            status = result['result']['list'][0]['orderStatus'] == 'Filled'
            logger.debug(f"Статус ордера {order_id}: {'Filled' if status else 'Not Filled'}")
            return status
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса ордера: {e}")
            return False
