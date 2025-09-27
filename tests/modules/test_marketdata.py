import pytest
from datetime import datetime
from decimal import Decimal

from app.modules.marketdata.schemas import (
    SecurityBase,
    SecurityCreate,
    Security,
    QuoteBase,
    QuoteCreate,
    Quote,
)


class TestSecuritySchemas:

    def test_security_base_valid(self):
        security = SecurityBase(
            secid="SBER",
            name="Сбербанк",
            isin="RU0009029540",
            engine="stock",
            market="shares",
            board="TQBR",
        )
        assert security.secid == "SBER"
        assert security.name == "Сбербанк"
        assert security.isin == "RU0009029540"

    def test_security_base_minimal(self):
        security = SecurityBase(secid="SBER", name="Сбербанк")
        assert security.secid == "SBER"
        assert security.name == "Сбербанк"
        assert security.isin is None

    def test_security_create(self):
        security = SecurityCreate(secid="GAZP", name="Газпром")
        assert security.secid == "GAZP"
        assert security.name == "Газпром"

    @pytest.fixture
    def sample_security(self):
        return Security(
            id=1,
            secid="SBER",
            name="Сбербанк",
            isin="RU0009029540",
            engine="stock",
            market="shares",
            board="TQBR",
            is_active="Y",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def test_security_complete(self, sample_security):
        assert sample_security.id == 1
        assert sample_security.secid == "SBER"
        assert sample_security.is_active == "Y"
        assert isinstance(sample_security.created_at, datetime)


class TestQuoteSchemas:

    def test_quote_base_valid(self):
        quote = QuoteBase(
            secid="SBER",
            timestamp=datetime.now(),
            close_price=Decimal("250.50"),
            volume=Decimal("1000"),
        )
        assert quote.secid == "SBER"
        assert quote.close_price == Decimal("250.50")
        assert quote.volume == Decimal("1000")

    def test_quote_create(self):
        quote = QuoteCreate(
            secid="GAZP",
            timestamp=datetime.now(),
            close_price=Decimal("180.25"),
            volume=Decimal("500"),
        )
        assert quote.secid == "GAZP"
        assert quote.close_price == Decimal("180.25")
        assert isinstance(quote.timestamp, datetime)
