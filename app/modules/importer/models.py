from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal


@dataclass
class SecurityPosition:
    """Позиция ценной бумаги из брокерского отчета"""

    issuer: str  # Эмитент
    security_type: str  # Тип ценной бумаги
    trading_code: str  # Торговый код
    isin: str  # ISIN код
    currency: Optional[str]  # Валюта (может быть пустой)
    quantity: int  # Количество (шт.)

    @property
    def is_bond(self) -> bool:
        """Проверяет, является ли позиция облигацией"""
        return "облигац" in self.security_type.lower()

    @property
    def is_stock(self) -> bool:
        """Проверяет, является ли позиция акцией"""
        return "акц" in self.security_type.lower()

    @property
    def is_etf(self) -> bool:
        """Проверяет, является ли позиция ETF"""
        return self.security_type.lower() == "пиф"


@dataclass
class BrokerStatement:
    """Брокерский отчет с позициями портфеля"""

    account_number: str  # Номер счета
    positions: List[SecurityPosition]  # Список позиций
    statement_date: Optional[str] = None  # Дата отчета

    @property
    def bonds(self) -> List[SecurityPosition]:
        """Возвращает только облигации"""
        return [pos for pos in self.positions if pos.is_bond]

    @property
    def stocks(self) -> List[SecurityPosition]:
        """Возвращает только акции"""
        return [pos for pos in self.positions if pos.is_stock]

    @property
    def etfs(self) -> List[SecurityPosition]:
        """Возвращает только ETF"""
        return [pos for pos in self.positions if pos.is_etf]

    @property
    def total_positions(self) -> int:
        """Общее количество позиций"""
        return len(self.positions)
