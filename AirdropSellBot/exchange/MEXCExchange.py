import time
import hmac
import hashlib
import requests
from typing import List, Tuple
from dotenv import load_dotenv
import os
from loguru import logger
from exchange.Exchange import Exchange

load_dotenv()
logger.add("trade.log", rotation="1 MB")

MEXC_API_URL = "https://api.mexc.com/api/v3"


class MEXCExchange(Exchange):
    def __init__(self):
        self.api_key = os.getenv("MEXC_API_KEY")
        self.api_secret = os.getenv("MEXC_API_SECRET")
        if not self.api_key or not self.api_secret:
            logger.error("API ключи для MEXC не найдены в .env")
            raise ValueError("API keys not provided")
        # Создаём сессию для изоляции запросов
        self.session = requests.Session()
        self.session.headers.update({
            "X-MEXC-APIKEY": self.api_key,
            "Content-Type": "application/json"
        })

    def _sign_request(self, params: dict) -> dict:
        timestamp = str(int(time.time() * 1000))
        params['timestamp'] = timestamp
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        logger.debug(f"Строка для подписи: {query_string}")
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        logger.debug(f"Сформированная подпись: {signature}")
        params['signature'] = signature
        return params

    def create_symbol(self, assert_in: str, assert_out: str) -> str:
        try:
            symbol = f"{assert_in}{assert_out}"
            logger.debug(f"Создан символ для MEXC: {symbol}")
            return symbol
        except Exception as e:
            logger.error(f"Ошибка при создании символа: {e}")
            return ""

    def get_balance(self, asset: str, auto_transfer: bool = False) -> float:
        try:
            params = {}
            signed_params = self._sign_request(params)
            # Используем сессию вместо прямого requests.get
            response = self.session.get(f"{MEXC_API_URL}/account", params=signed_params)
            result = response.json()
            if response.status_code == 200:
                if 'balances' in result:
                    for balance in result['balances']:
                        if balance['asset'] == asset:
                            avail_bal = float(balance['free'])
                            logger.debug(f"Найден баланс для {asset}: {avail_bal}")
                            return avail_bal
                else:
                    logger.debug(f"Ключ 'balances' не найден в ответе: {result}")
            else:
                logger.error(f"Ошибка API: {result}")
            logger.debug(f"Баланс для {asset} не найден, возвращаем 0")
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return 0.0

    def get_open_orders(self, symbol: str) -> list:
        try:
            params = {"symbol": symbol}
            signed_params = self._sign_request(params)
            response = self.session.get(f"{MEXC_API_URL}/openOrders", params=signed_params)
            result = response.json()
            if response.status_code == 200:
                logger.debug(f"Получены открытые ордера для {symbol}: {len(result)} шт.")
                return result
            logger.error(f"Ошибка получения ордеров: {result}")
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении ордеров: {e}")
            return []

    def calculate_sell_orders(self, symbol: str, quantity: float) -> List[Tuple[float, float]]:
        try:
            # Используем self.session.get вместо requests.get
            response = self.session.get(f"{MEXC_API_URL}/depth", params={"symbol": symbol, "limit": 10})
            result = response.json()
            if response.status_code == 200 and 'bids' in result:
                bids = result['bids'][1:]
                logger.info(f"Получены биды для {symbol}: {[(float(price), float(qty)) for price, qty in bids]}")

                if not bids:
                    logger.warning(f"Список бидов для {symbol} пуст")
                    return []

                orders = []
                remaining_qty = quantity
                success_rate = 0.10

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
            logger.error(f"Ошибка получения книги ордеров: {result}")
            return []
        except Exception as e:
            logger.error(f"Ошибка при вычислении ордеров: {e}")
            return []

    def place_sell_order(self, symbol: str, quantity: float, price: float) -> str:
        try:
            params = {
                "symbol": symbol,
                "side": "SELL",
                "type": "LIMIT",
                "quantity": str(quantity),
                "price": str(price)
            }
            signed_params = self._sign_request(params)
            # Отправляем параметры в теле запроса в формате URL-encoded
            response = self.session.post(f"{MEXC_API_URL}/order", data=signed_params)
            result = response.json()
            logger.debug(f"Ответ API: {result}")  # Добавляем отладочный вывод
            if response.status_code == 200 and 'orderId' in result:
                order_id = result['orderId']
                logger.debug(f"Ордер успешно выставлен: {order_id}")
                return order_id
            logger.error(f"Ошибка выставления ордера: {result}")
            return ""
        except Exception as e:
            logger.error(f"Ошибка при выставлении ордера: {e}")
            return ""

    def cancel_order(self, order_id: str, symbol: str):
        try:
            params = {"orderId": order_id, "symbol": symbol}
            signed_params = self._sign_request(params)
            response = self.session.delete(f"{MEXC_API_URL}/order", json=signed_params)
            if response.status_code == 200:
                logger.debug(f"Ордер {order_id} отменён")
            else:
                logger.error(f"Ошибка отмены ордера: {response.json()}")
        except Exception as e:
            logger.error(f"Ошибка при отмене ордера: {e}")

    def check_order_status(self, order_id: str, symbol: str) -> bool:
        try:
            params = {"orderId": order_id, "symbol": symbol}
            signed_params = self._sign_request(params)
            response = self.session.get(f"{MEXC_API_URL}/order", params=signed_params)
            result = response.json()
            if response.status_code == 200 and 'status' in result:
                status = result['status'] == 'FILLED'
                logger.debug(f"Статус ордера {order_id}: {'Filled' if status else 'Not Filled'}")
                return status
            logger.error(f"Ошибка проверки статуса ордера: {result}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса ордера: {e}")
            return False