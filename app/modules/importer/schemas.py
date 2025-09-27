from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class SecurityPositionResponse(BaseModel):
    """Ответ с данными о позиции ценной бумаги"""

    issuer: str = Field(..., description="Наименование эмитента")
    security_type: str = Field(..., description="Тип ценной бумаги")
    trading_code: str = Field(..., description="Торговый код на бирже")
    isin: str = Field(..., description="ISIN код")
    currency: Optional[str] = Field(None, description="Валюта")
    quantity: int = Field(..., description="Количество штук")
    is_bond: bool = Field(..., description="Является ли облигацией")
    is_stock: bool = Field(..., description="Является ли акцией")
    is_etf: bool = Field(..., description="Является ли ETF")


class BrokerStatementResponse(BaseModel):
    """Ответ с данными брокерского отчета"""

    account_number: str = Field(..., description="Номер счета")
    statement_date: Optional[str] = Field(None, description="Дата отчета")
    total_positions: int = Field(..., description="Общее количество позиций")
    bonds_count: int = Field(..., description="Количество облигаций")
    stocks_count: int = Field(..., description="Количество акций")
    etfs_count: int = Field(..., description="Количество ETF")
    positions: list[SecurityPositionResponse] = Field(..., description="Список позиций")


class ImportStatisticsResponse(BaseModel):
    """Статистика импорта"""

    success: bool = Field(..., description="Успешность операции")
    processed_positions: int = Field(..., description="Количество обработанных позиций")
    imported_positions: int = Field(
        ..., description="Количество импортированных позиций"
    )
    skipped_positions: int = Field(..., description="Количество пропущенных позиций")
    errors: list[str] = Field(default_factory=list, description="Список ошибок")
    message: str = Field(..., description="Сообщение о результате")
