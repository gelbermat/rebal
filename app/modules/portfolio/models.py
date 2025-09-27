from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class Portfolio(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    total_value: Decimal = Decimal("0")
    cash_balance: Decimal = Decimal("0")
    is_active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class Position(BaseModel):
    id: int
    portfolio_id: int
    secid: str
    quantity: Decimal = Decimal("0")
    avg_price: Optional[Decimal] = None
    market_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    target_weight: Optional[Decimal] = None
    actual_weight: Optional[Decimal] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
