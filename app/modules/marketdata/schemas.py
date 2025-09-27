from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class SecurityBase(BaseModel):
    secid: str
    name: str
    isin: Optional[str] = None
    engine: Optional[str] = None
    market: Optional[str] = None
    board: Optional[str] = None


class SecurityCreate(SecurityBase):
    pass


class Security(SecurityBase):
    id: int
    is_active: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuoteBase(BaseModel):

    secid: str
    timestamp: datetime
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    value: Optional[Decimal] = None


class QuoteCreate(QuoteBase):

    pass


class Quote(QuoteBase):

    id: int
    created_at: datetime

    class Config:
        from_attributes = True
