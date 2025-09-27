import pytest
from datetime import datetime
from decimal import Decimal

from app.modules.portfolio.schemas import PositionBase, PositionCreate, Position


class TestPositionSchemas:

    def test_position_base_valid(self):
        position = PositionBase(
            secid="SBER", quantity=Decimal("100"), target_weight=Decimal("0.25")
        )
        assert position.secid == "SBER"
        assert position.quantity == Decimal("100")
        assert position.target_weight == Decimal("0.25")

    def test_position_create(self):
        position = PositionCreate(secid="GAZP", quantity=Decimal("50"), portfolio_id=1)
        assert position.secid == "GAZP"
        assert position.quantity == Decimal("50")
        assert position.portfolio_id == 1

    @pytest.fixture
    def sample_position(self):
        return Position(
            id=1,
            secid="SBER",
            quantity=100,
            avg_price=Decimal("250.00"),
            portfolio_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def test_position_complete(self, sample_position):
        assert sample_position.id == 1
        assert sample_position.secid == "SBER"
        assert sample_position.quantity == 100
        assert isinstance(sample_position.created_at, datetime)

    def test_position_calculations(self):
        # Используем Position вместо PositionBase для расчетов с avg_price
        position = Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=Decimal("100"),
            avg_price=Decimal("250.00"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        total_value = position.quantity * position.avg_price
        assert total_value == Decimal("25000.00")

    def test_position_negative_quantity(self):
        position = PositionBase(secid="SBER", quantity=Decimal("-50"))
        assert position.quantity == Decimal("-50")


class TestPortfolioCalculations:

    def test_portfolio_total_value(self):
        positions = [
            Position(
                id=1,
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                avg_price=Decimal("250.00"),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Position(
                id=2,
                portfolio_id=1,
                secid="GAZP",
                quantity=Decimal("50"),
                avg_price=Decimal("180.00"),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        total_value = sum(pos.quantity * pos.avg_price for pos in positions)
        assert total_value == Decimal("34000.00")

    def test_portfolio_weighted_average(self):
        positions = [
            Position(
                id=1,
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                avg_price=Decimal("250.00"),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Position(
                id=2,
                portfolio_id=1,
                secid="GAZP",
                quantity=Decimal("200"),
                avg_price=Decimal("180.00"),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        total_quantity = sum(pos.quantity for pos in positions)
        weighted_avg = (
            sum(pos.quantity * pos.avg_price for pos in positions) / total_quantity
        )

        assert total_quantity == Decimal("300")
        # Проверяем округленный результат для избежания проблем с точностью
        assert abs(weighted_avg - Decimal("203.33333333")) < Decimal("0.00001")
