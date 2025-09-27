from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel


class PortfolioBase(BaseModel):

    name: str
    description: Optional[str] = None


class PortfolioCreate(PortfolioBase):

    pass


class Portfolio(PortfolioBase):

    id: int
    total_value: Decimal
    cash_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PositionBase(BaseModel):

    secid: str
    quantity: Decimal
    target_weight: Optional[Decimal] = None


class PositionCreate(PositionBase):

    portfolio_id: int


class Position(PositionBase):

    id: int
    portfolio_id: int
    avg_price: Optional[Decimal] = None
    market_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    actual_weight: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):

    portfolio: Portfolio
    positions: List[Position]
    total_unrealized_pnl: Decimal
    positions_count: int
