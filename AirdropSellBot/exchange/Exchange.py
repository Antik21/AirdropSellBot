from abc import ABC, abstractmethod
from typing import List, Tuple


# Абстрактный базовый класс для бирж
class Exchange(ABC):
    @abstractmethod
    def create_symbol(self, assert_in: str, assert_out: str) -> str:
        """Создать идентификатор торговой пары"""
        pass

    @abstractmethod
    def get_balance(self, asset: str, auto_transfer: bool) -> float:
        """Получить баланс конкретного актива."""
        pass

    @abstractmethod
    def get_open_orders(self, symbol: str) -> list:
        """Получить открытые ордера."""
        pass

    @abstractmethod
    def calculate_sell_orders(self, symbol: str, quantity: float) -> List[Tuple[float, float]]:
        """Вычислить список ордеров на продажу (новая логика)."""
        pass

    @abstractmethod
    def place_sell_order(self, symbol: str, quantity: float, price: float) -> str:
        """Выставить ордер на продажу."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str):
        """Отменить ордер."""
        pass

    @abstractmethod
    def check_order_status(self, order_id: str, symbol: str) -> bool:
        """Проверить статус ордера."""
        pass
