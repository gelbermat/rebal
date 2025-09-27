"""Модели для отчетности и аналитики"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum


class ReportType(str, Enum):
    """Типы отчетов"""

    PORTFOLIO = "portfolio"
    TRANSACTIONS = "transactions"
    PNL = "pnl"


class TransactionType(str, Enum):
    """Типы сделок"""

    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    MERGER = "merger"


@dataclass
class Transaction:
    """Модель сделки/транзакции"""

    id: int
    portfolio_id: int
    secid: str
    transaction_type: TransactionType
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    commission: Optional[Decimal] = None
    notes: Optional[str] = None

    @property
    def total_amount(self) -> Decimal:
        """Общая сумма сделки без комиссии"""
        return self.quantity * self.price

    @property
    def total_cost(self) -> Decimal:
        """Общая стоимость с учетом комиссии"""
        commission = self.commission or Decimal("0")
        if self.transaction_type == TransactionType.BUY:
            return self.total_amount + commission
        else:
            return self.total_amount - commission


@dataclass
class PortfolioSnapshot:
    """Снимок портфеля на конкретную дату"""

    portfolio_id: int
    date: date
    secid: str
    security_name: str
    quantity: Decimal
    avg_cost: Decimal
    current_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    weight_percent: Optional[Decimal] = None


@dataclass
class PortfolioReport:
    """Отчет по портфелю"""

    report_id: str
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    generated_at: datetime

    # Основные показатели
    positions: List[PortfolioSnapshot] = field(default_factory=list)
    total_value: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    total_unrealized_pnl: Decimal = Decimal("0")
    total_realized_pnl: Decimal = Decimal("0")

    # Дополнительная аналитика
    asset_allocation: Dict[str, Decimal] = field(default_factory=dict)
    top_holdings: List[PortfolioSnapshot] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransactionSummary:
    """Сводка по сделкам"""

    secid: str
    security_name: str
    total_buy_quantity: Decimal
    total_sell_quantity: Decimal
    total_buy_amount: Decimal
    total_sell_amount: Decimal
    net_quantity: Decimal
    total_commission: Decimal
    transaction_count: int


@dataclass
class TransactionReport:
    """Отчет по сделкам"""

    report_id: str
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    generated_at: datetime

    # Детальные сделки
    transactions: List[Transaction] = field(default_factory=list)

    # Сводная информация
    summary_by_security: List[TransactionSummary] = field(default_factory=list)
    total_transactions: int = 0
    total_buy_amount: Decimal = Decimal("0")
    total_sell_amount: Decimal = Decimal("0")
    total_commission: Decimal = Decimal("0")
    net_cash_flow: Decimal = Decimal("0")


@dataclass
class PnLEntry:
    """Запись о прибыли/убытке"""

    secid: str
    security_name: str
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    quantity_held: Decimal
    avg_cost: Decimal
    current_price: Optional[Decimal] = None
    dividend_income: Decimal = Decimal("0")


@dataclass
class PnLReport:
    """Отчет о прибыли и убытках"""

    report_id: str
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    generated_at: datetime

    # P&L по инструментам
    pnl_entries: List[PnLEntry] = field(default_factory=list)

    # Итоговые показатели
    total_realized_pnl: Decimal = Decimal("0")
    total_unrealized_pnl: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")
    total_dividend_income: Decimal = Decimal("0")

    # Дополнительные метрики
    best_performers: List[PnLEntry] = field(default_factory=list)
    worst_performers: List[PnLEntry] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportRequest:
    """Запрос на создание отчета"""

    report_type: ReportType
    portfolio_id: int
    start_date: date
    end_date: date
    parameters: Dict[str, Any] = field(default_factory=dict)
