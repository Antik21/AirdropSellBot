# Реализация для OKX
import time
from datetime import timedelta, datetime
from typing import List, Tuple
from dotenv import load_dotenv
import os
from loguru import logger

from exchange.Exchange import Exchange
from okx.MarketData import MarketAPI  # Проверяем правильность импорта
from okx.Trade import TradeAPI  # Проверяем правильность импорта
from okx.Account import AccountAPI  # Добавлен для баланса
from okx.Funding import FundingAPI
from config import REQUEST_TIMEOUT, DELAY_BETWEEN_RETRIES

load_dotenv()  # Загружаем переменные из .env

# Настройка логирования
logger.add("trade.log", rotation="1 MB")


class OKXExchange(Exchange):
    def __init__(self):
        api_key = os.getenv("OKX_API_KEY")
        api_secret = os.getenv("OKX_API_SECRET")
        passphrase = os.getenv("OKX_PASSPHRASE")
        self.trade_api = TradeAPI(api_key, api_secret, passphrase, flag="0", debug=False)
        self.market_api = MarketAPI(api_key, api_secret, passphrase, flag="0", debug=False)
        self.account_api = AccountAPI(api_key, api_secret, passphrase, flag="0", debug=False)
        self.funding_api = FundingAPI(api_key, api_secret, passphrase, flag="0", debug=False)

    def create_symbol(self, assert_in: str, assert_out: str) -> str:
        return assert_in + "-" + assert_out

    def get_balance(self, asset: str, auto_transfer: bool = False) -> float:
        try:
            if auto_transfer:
                # Шаг 1: Проверяем баланс на Funding аккаунте
                funding_result = self.funding_api.get_balances(ccy=asset)
                if funding_result['code'] != '0':
                    logger.error(f"Ошибка получения баланса Funding: {funding_result['msg']}")
                else:
                    funding_bal = 0.0
                    for balance in funding_result['data']:
                        if balance['ccy'] == asset:
                            funding_bal = float(balance['availBal'])
                            logger.debug(f"Найден баланс Funding для {asset}: {funding_bal}")
                            break
                    else:
                        logger.debug(f"Баланс Funding для {asset} не найден")

                    # Если на Funding есть средства, переводим их на Trading
                    if funding_bal > 0:
                        logger.info(f"Обнаружен баланс {funding_bal} {asset} на Funding, переводим на Trading")
                        transfer_result = self.funding_api.funds_transfer(
                            ccy=asset,
                            amt=funding_bal,
                            from_="6",  # Funding аккаунт (код 6)
                            to="18"  # Trading аккаунт (код 18)
                        )
                        if transfer_result['code'] != '0':
                            logger.error(f"Ошибка перевода средств: {transfer_result['msg']}")
                        else:
                            logger.info(f"Успешно переведено {funding_bal} {asset} с Funding на Trading")
                            time.sleep(0.5)  # Ждём 0.5 секунды после перевода

            # Шаг 2: Проверяем баланс на Trading аккаунте
            trading_result = self.account_api.get_account_balance(ccy=asset)
            if trading_result['code'] != '0':
                logger.error(f"Ошибка получения баланса Trading: {trading_result['msg']}")
                return 0.0
            for balance in trading_result['data'][0]['details']:
                if balance['ccy'] == asset:
                    avail_bal = float(balance['availBal'])
                    logger.debug(f"Найден баланс Trading для {asset}: {avail_bal}")
                    return avail_bal
            logger.debug(f"Баланс Trading для {asset} не найден, возвращаем 0")
            return 0.0

        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return 0.0

    def get_open_orders(self, symbol: str) -> list:
        try:
            result = self.trade_api.get_order_list(instId=symbol)
            if result['code'] != '0':
                logger.error(f"Ошибка получения ордеров: {result['msg']}")
                return []
            orders = result['data']
            logger.debug(f"Получены открытые ордера для {symbol}: {len(orders)} шт.")
            return orders
        except Exception as e:
            logger.error(f"Ошибка при получении ордеров: {e}")
            return []

    def calculate_sell_orders(self, symbol: str, quantity: float) -> List[Tuple[float, float]]:
        try:
            order_book = self.market_api.get_orderbook(instId=symbol, sz=50)
            if order_book['code'] != '0':
                logger.error(f"Ошибка получения книги ордеров: {order_book['msg']}")
                return []
            bids = order_book['data'][0]['bids']
            logger.info(f"Получены биды для {symbol}: {[(float(price), float(qty)) for price, qty, *_ in bids]}")

            if len(bids) > 1:
                bids = bids[1:]
            else:
                logger.warning(f"Получен только один бид для {symbol}, недостаточно данных для расчёта")
                return []

            if not bids:
                logger.warning(f"Список бидов для {symbol} пуст после пропуска первого ордера")
                return []

            orders = []
            remaining_qty = quantity
            success_rate = 0.10

            for bid_price, bid_qty, *_ in bids:
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
            result = self.trade_api.place_order(
                instId=symbol,
                tdMode="cash",
                side="sell",
                ordType="limit",
                sz=str(quantity),
                px=str(price)
            )
            if result['code'] == '0':
                order_id = result['data'][0]['ordId']
                logger.debug(f"Ордер успешно выставлен: {order_id}")
                return order_id
            else:
                logger.error(f"Ошибка выставления ордера: {result['msg']}")
                return ""
        except Exception as e:
            logger.error(f"Ошибка при выставлении ордера: {e}")
            return ""

    def cancel_order(self, order_id: str, symbol: str):
        try:
            result = self.trade_api.cancel_order(instId=symbol, ordId=order_id)
            if result['code'] == '0':
                logger.debug(f"Ордер {order_id} отменён")
            else:
                logger.error(f"Ошибка отмены ордера: {result['msg']}")
        except Exception as e:
            logger.error(f"Ошибка при отмене ордера: {e}")

    def check_order_status(self, order_id: str, symbol: str) -> bool:
        try:
            result = self.trade_api.get_order(instId=symbol, ordId=order_id)
            if result['code'] != '0':
                logger.error(f"Ошибка проверки статуса ордера: {result['msg']}")
                return False
            status = result['data'][0]['state'] == 'filled'
            logger.debug(f"Статус ордера {order_id}: {'filled' if status else 'not filled'}")
            return status
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса ордера: {e}")
            return False
