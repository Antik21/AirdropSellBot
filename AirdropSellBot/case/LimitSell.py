import time
from typing import List, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from config import ROUNDING_PRECISION, ASSERT_OUT


# Настройка глобального HTTP-клиента
def setup_requests_retries(max_retries=3, backoff_factor=1, timeout=10):
    session = requests.Session()
    retries = Retry(
        total=max_retries,  # Максимальное количество повторов
        backoff_factor=backoff_factor,  # Задержка между повторами (1 сек, 2 сек, 4 сек и т.д.)
        status_forcelist=[500, 502, 503, 504],  # Коды ошибок для повтора
        allowed_methods=["GET", "POST"]  # Методы, для которых применяются повторы
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.timeout = timeout  # Устанавливаем таймаут для всех запросов
    # Привязываем настроенную сессию к requests
    requests.sessions.HTTPAdapter = lambda self, *args, **kwargs: adapter
    return session


"""
    Основная функция для лимитной продажи токенов.
    
    Args:
        exchange: Инстанс биржи (например, BinanceExchange)
        sell_percentage: Процент от баланса для продажи (0.0 - 1.0)
        asset: Символ токена (например, "BTC")
    """


def limit_sell(exchange, sell_percentage: float, asset: str) -> None:
    if not 0 <= sell_percentage <= 1:
        print(f"Ошибка: Процент должен быть между 0 и 1, получено {sell_percentage}")
        return

    # Настраиваем requests перед инициализацией API
    setup_requests_retries(max_retries=3, backoff_factor=1, timeout=3)

    symbol = exchange.create_symbol(asset, ASSERT_OUT)

    print(f"Запуск лимитной продажи {sell_percentage * 100}% токенов {asset} на {symbol}")

    while True:
        # Шаг 1: Проверка баланса
        balance = exchange.get_balance(asset, True)
        print(f"Текущий баланс {asset}: {balance}")

        if balance <= 0:
            print(f"Баланс {asset} равен 0, ждём 1 секунду...")
            time.sleep(1)
            continue

        # Шаг 2: Расчёт количества токенов для продажи
        sell_quantity = balance * sell_percentage
        sell_quantity = round(sell_quantity / ROUNDING_PRECISION) * ROUNDING_PRECISION  # Округление
        print(f"Количество для продажи: {sell_quantity} {asset}")

        # Шаг 3: Основной цикл продажи
        remaining_to_sell = sell_quantity

        while remaining_to_sell >= ROUNDING_PRECISION:
            # 3.1: Расчёт ордеров
            sell_orders = exchange.calculate_sell_orders(symbol, remaining_to_sell)
            if not sell_orders:
                print("Не удалось рассчитать ордера, ждём 1 секунду")
                time.sleep(1)
                continue

            # 3.2: Выставление ордеров
            active_orders: List[Tuple[str, float, float]] = []  # (order_id, price, qty)
            for price, qty in sell_orders:
                order_id = exchange.place_sell_order(symbol, qty, price)
                if order_id:
                    print(f"Ордер выставлен: {order_id}, цена: {price}, объём: {qty}")
                    active_orders.append((order_id, price, qty))
                else:
                    print(f"Не удалось выставить ордер для цены {price}, объёма {qty}")

            if not active_orders:
                print("Все ордера провалились, повторяем")
                time.sleep(1)
                continue

            # 3.3: Ожидание 1500 мс
            time.sleep(1.5)

            # 3.4: Проверка статуса ордеров
            for order_id, price, qty in active_orders[:]:  # Копируем список для изменения во время итерации
                if exchange.check_order_status(order_id, symbol):
                    print(f"Ордер {order_id} выполнен, удаляем из списка")
                    active_orders.remove((order_id, price, qty))
                    remaining_to_sell -= qty
                else:
                    print(f"Ордер {order_id} не выполнен, отменяем")
                    exchange.cancel_order(order_id, symbol)
                    # Проверяем ещё раз после отмены
                    if exchange.check_order_status(order_id, symbol):
                        print(f"Ордер {order_id} всё-таки выполнен после отмены")
                        active_orders.remove((order_id, price, qty))
                        remaining_to_sell -= qty
                    else:
                        active_orders.remove((order_id, price, qty))

            # 3.5: Проверка результата
            current_balance = exchange.get_balance(asset, False)
            sold_amount = balance - current_balance
            print(f"Продано: {sold_amount}, осталось продать: {remaining_to_sell}")

            if remaining_to_sell <= 0:
                print("Все токены успешно проданы!")
                usdt_balance = exchange.get_balance(ASSERT_OUT, False)
                print(f"Текущий баланс {ASSERT_OUT}: {usdt_balance}")
                return
            else:
                print(f"Осталось продать {remaining_to_sell} {asset}, пересчитываем")
                balance = current_balance  # Обновляем баланс для следующей итерации
