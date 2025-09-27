from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class Security(BaseModel):
    secid: str
    name: str
    isin: Optional[str] = None
    engine: Optional[str] = None
    market: Optional[str] = None
    board: Optional[str] = None
    is_active: bool = True
    created_at: datetime = datetime.now()


class Quote(BaseModel):
    secid: str
    timestamp: datetime
    price: Decimal
    volume: Optional[Decimal] = None
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
