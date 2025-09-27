"""Pydantic схемы для модуля отчетности"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from .models import ReportType, TransactionType


# Базовые схемы для запросов
class ReportRequestBase(BaseModel):
    """Базовая схема запроса отчета"""

    portfolio_id: int = Field(..., description="ID портфеля")
    start_date: date = Field(..., description="Начальная дата периода")
    end_date: date = Field(..., description="Конечная дата периода")

    @validator("end_date")
    def validate_date_range(cls, v, values):
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("Конечная дата должна быть больше начальной даты")
        return v


class PortfolioReportRequest(ReportRequestBase):
    """Запрос отчета по портфелю"""

    include_performance_metrics: bool = Field(
        default=True, description="Включить метрики производительности"
    )
    top_holdings_limit: int = Field(
        default=10, description="Количество топ позиций для отображения"
    )


class TransactionReportRequest(ReportRequestBase):
    """Запрос отчета по сделкам"""

    transaction_types: Optional[List[TransactionType]] = Field(
        default=None, description="Фильтр по типам сделок"
    )
    securities: Optional[List[str]] = Field(
        default=None, description="Фильтр по ценным бумагам"
    )


class PnLReportRequest(ReportRequestBase):
    """Запрос отчета P&L"""

    include_unrealized: bool = Field(
        default=True, description="Включить нереализованную прибыль"
    )
    include_dividends: bool = Field(default=True, description="Включить дивиденды")


# Схемы ответов
class TransactionResponse(BaseModel):
    """Ответ с данными сделки"""

    id: int
    portfolio_id: int
    secid: str
    transaction_type: TransactionType
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    commission: Optional[Decimal] = None
    notes: Optional[str] = None
    total_amount: Decimal
    total_cost: Decimal

    class Config:
        from_attributes = True


class PortfolioSnapshotResponse(BaseModel):
    """Ответ с данными позиции в портфеле"""

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

    class Config:
        from_attributes = True


class TransactionSummaryResponse(BaseModel):
    """Ответ со сводкой по сделкам"""

    secid: str
    security_name: str
    total_buy_quantity: Decimal
    total_sell_quantity: Decimal
    total_buy_amount: Decimal
    total_sell_amount: Decimal
    net_quantity: Decimal
    total_commission: Decimal
    transaction_count: int

    class Config:
        from_attributes = True


class PnLEntryResponse(BaseModel):
    """Ответ с данными P&L"""

    secid: str
    security_name: str
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    quantity_held: Decimal
    avg_cost: Decimal
    current_price: Optional[Decimal] = None
    dividend_income: Decimal = Decimal("0")

    class Config:
        from_attributes = True


class PortfolioReportResponse(BaseModel):
    """Ответ с отчетом по портфелю"""

    report_id: str
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    generated_at: datetime

    positions: List[PortfolioSnapshotResponse]
    total_value: Decimal
    total_cost: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal

    asset_allocation: Dict[str, Decimal]
    top_holdings: List[PortfolioSnapshotResponse]
    performance_metrics: Dict[str, Any]

    class Config:
        from_attributes = True


class TransactionReportResponse(BaseModel):
    """Ответ с отчетом по сделкам"""

    report_id: str
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    generated_at: datetime

    transactions: List[TransactionResponse]
    summary_by_security: List[TransactionSummaryResponse]
    total_transactions: int
    total_buy_amount: Decimal
    total_sell_amount: Decimal
    total_commission: Decimal
    net_cash_flow: Decimal

    class Config:
        from_attributes = True


class PnLReportResponse(BaseModel):
    """Ответ с отчетом P&L"""

    report_id: str
    portfolio_id: int
    portfolio_name: str
    start_date: date
    end_date: date
    generated_at: datetime

    pnl_entries: List[PnLEntryResponse]
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal
    total_pnl: Decimal
    total_dividend_income: Decimal

    best_performers: List[PnLEntryResponse]
    worst_performers: List[PnLEntryResponse]
    performance_metrics: Dict[str, Any]

    class Config:
        from_attributes = True


# Схемы для создания сделок
class TransactionCreate(BaseModel):
    """Схема создания сделки"""

    portfolio_id: int = Field(..., description="ID портфеля")
    secid: str = Field(..., description="Код ценной бумаги")
    transaction_type: TransactionType = Field(..., description="Тип сделки")
    quantity: Decimal = Field(..., gt=0, description="Количество")
    price: Decimal = Field(..., gt=0, description="Цена за единицу")
    timestamp: Optional[datetime] = Field(default=None, description="Время сделки")
    commission: Optional[Decimal] = Field(default=None, ge=0, description="Комиссия")
    notes: Optional[str] = Field(default=None, description="Примечания")


class TransactionUpdate(BaseModel):
    """Схема обновления сделки"""

    quantity: Optional[Decimal] = Field(default=None, gt=0)
    price: Optional[Decimal] = Field(default=None, gt=0)
    commission: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = None
