# Консольное приложение
from case.LimitSell import limit_sell
from exchange.BinanceExchange import BinanceExchange
from exchange.BybitExchange import BybitExchange
from exchange.GateIOExchange import GateIOExchange
from exchange.MEXCExchange import MEXCExchange
from exchange.OKXExchange import OKXExchange


def main():
    print("Выберите биржу:")
    print("1 - OKX")
    print("2 - Bybit")
    print("3 - Binance")
    print("4 - Gate.io")
    print("5 - MEXC")

    while True:
        try:
            choice = int(input("Введите номер биржи (1-5): "))
            if choice in [1, 2, 3, 4, 5]:
                break
            print("Пожалуйста, введите число от 1 до 5.")
        except ValueError:
            print("Некорректный ввод, введите число от 1 до 5.")

    asset = input("Введите символ монеты (например, BTC): ").upper()
    sell_percentage = float(input("Введите процент продаваемого актива (от 0.01 до 1): "))

    exchange = None
    if choice == 1:
        exchange = OKXExchange()
    elif choice == 2:  # Bybit
        exchange = BybitExchange()
    elif choice == 3:  # Binance
        exchange = BinanceExchange()
    elif choice == 4:
        exchange = GateIOExchange()
    elif choice == 5:  # MEXC
        exchange = MEXCExchange()

    limit_sell(exchange, sell_percentage, asset)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")