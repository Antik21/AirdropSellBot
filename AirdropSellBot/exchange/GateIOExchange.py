import time
from typing import List, Tuple
from gate_api import ApiClient, Configuration, SpotApi, Order
from gate_api.exceptions import GateApiException

from dotenv import load_dotenv
import os
from loguru import logger

from exchange.Exchange import Exchange

load_dotenv()  # Загружаем переменные из .env

# Настройка логирования
logger.add("trade.log", rotation="1 MB")


class GateIOExchange(Exchange):
    def __init__(self):
        api_key = os.getenv("GATE_API_KEY")
        api_secret = os.getenv("GATE_API_SECRET")
        if not api_key or not api_secret:
            logger.error("API ключи для Gate не найдены в .env")
            raise ValueError("API keys not provided")
        # Настройка конфигурации с увеличенным таймаутом
        config = Configuration(key=api_key, secret=api_secret)
        config.timeout = 10  # Устанавливаем таймаут 10 секунд
        self.client = ApiClient(config)
        self.spot_api = SpotApi(self.client)

    def create_symbol(self, assert_in: str, assert_out: str) -> str:
        """Создать идентификатор торговой пары для Gate.io (формат: ASSERT_IN_ASSERT_OUT)."""
        try:
            # Gate.io использует формат с подчёркиванием, например, BTC_USDT
            symbol = f"{assert_in}_{assert_out}"
            logger.debug(f"Создан символ для Gate.io: {symbol}")
            return symbol
        except Exception as e:
            logger.error(f"Ошибка при создании символа: {e}")
            return ""

    def get_balance(self, asset: str, auto_transfer: bool = True) -> float:
        """
        Получение доступного баланса для спотового аккаунта.
        Gate.io не требует перевода между Funding и Trading, поэтому auto_transfer игнорируется.
        """
        try:
            accounts = self.spot_api.list_spot_accounts(currency=asset)
            for account in accounts:
                if account.currency == asset:
                    avail_bal = float(account.available)
                    logger.debug(f"Найден баланс для {asset}: {avail_bal}")
                    return avail_bal
            logger.debug(f"Баланс для {asset} не найден, возвращаем 0")
            return 0.0
        except GateApiException as e:
            logger.error(f"Ошибка API Gate.io при получении баланса: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return 0.0

    def get_open_orders(self, symbol: str) -> list:
        """Получение списка открытых ордеров для торговой пары."""
        try:
            orders = self.spot_api.list_orders(symbol, status='open', page=1, limit=100)
            logger.debug(f"Получены открытые ордера для {symbol}: {len(orders)} шт.")
            return orders
        except GateApiException as e:
            logger.error(f"Ошибка API Gate.io при получении ордеров: {e}")
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении ордеров: {e}")
            return []

    def calculate_sell_orders(self, symbol: str, quantity: float) -> List[Tuple[float, float]]:
        """Расчёт лимитных ордеров на продажу на основе книги ордеров."""
        try:
            order_book = self.spot_api.list_order_book(currency_pair=symbol, limit=50)
            bids = order_book.bids  # Список [цена, объём]
            logger.info(f"Получены биды для {symbol}: {[(float(b[0]), float(b[1])) for b in bids]}")

            if len(bids) > 1:
                bids = bids[1:]  # Пропускаем первый бид
            else:
                logger.warning(f"Получен только один бид для {symbol}, недостаточно данных")
                return []

            if not bids:
                logger.warning(f"Список бидов для {symbol} пуст после пропуска первого")
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
        except GateApiException as e:
            logger.error(f"Ошибка API Gate.io при получении книги ордеров: {e}")
            return []
        except Exception as e:
            logger.error(f"Ошибка при вычислении ордеров: {e}")
            return []

    def place_sell_order(self, symbol: str, quantity: float, price: float) -> str:
        """Выставление лимитного ордера на продажу."""
        try:
            order = Order(
                currency_pair=symbol,
                side='sell',
                type='limit',
                amount=str(quantity),
                price=str(price)
            )
            created_order = self.spot_api.create_order(order)
            order_id = created_order.id
            logger.debug(f"Ордер успешно выставлен: {order_id}")
            return order_id
        except GateApiException as e:
            logger.error(f"Ошибка API Gate.io при выставлении ордера: {e}")
            return ""
        except Exception as e:
            logger.error(f"Ошибка при выставлении ордера: {e}")
            return ""

    def cancel_order(self, order_id: str, symbol: str):
        """Отмена ордера."""
        try:
            self.spot_api.cancel_order(order_id, symbol)
            logger.debug(f"Ордер {order_id} отменён")
        except GateApiException as e:
            logger.error(f"Ошибка API Gate.io при отмене ордера: {e}")
        except Exception as e:
            logger.error(f"Ошибка при отмене ордера: {e}")

    def check_order_status(self, order_id: str, symbol: str) -> bool:
        """Проверка статуса ордера."""
        try:
            order = self.spot_api.get_order(order_id, symbol)
            status = order.status == 'closed'  # 'closed' — выполнен, 'open' — активен
            logger.debug(f"Статус ордера {order_id}: {'filled' if status else 'not filled'}")
            return status
        except GateApiException as e:
            logger.error(f"Ошибка API Gate.io при проверке статуса ордера: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса ордера: {e}")
            return False
