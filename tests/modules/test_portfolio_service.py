import pytest
from decimal import Decimal

from app.storage import DataManager
from app.modules.portfolio.service import PortfolioService
from app.modules.portfolio.schemas import PortfolioCreate, PositionCreate
from app.modules.portfolio.models import Portfolio, Position


class TestPortfolioServiceIntegration:
    "Integration tests for PortfolioService with DataManager"

    @pytest.fixture
    def data_manager(self):
        "Create a fresh DataManager instance for each test"
        return DataManager()

    @pytest.fixture
    def portfolio_service(self, data_manager):
        "Create PortfolioService with injected DataManager"
        return PortfolioService(data_manager)

    @pytest.mark.asyncio
    async def test_create_portfolio(self, portfolio_service):
        "Test portfolio creation without global variables"
        portfolio_data = PortfolioCreate(
            name="Test Portfolio", description="Test Description"
        )

        portfolio = await portfolio_service.create_portfolio(portfolio_data)

        assert portfolio.id == 1
        assert portfolio.name == "Test Portfolio"
        assert portfolio.description == "Test Description"

    @pytest.mark.asyncio
    async def test_create_multiple_portfolios(self, portfolio_service):
        "Test that ID generation works correctly without globals"
        portfolio1_data = PortfolioCreate(name="Portfolio 1")
        portfolio2_data = PortfolioCreate(name="Portfolio 2")

        portfolio1 = await portfolio_service.create_portfolio(portfolio1_data)
        portfolio2 = await portfolio_service.create_portfolio(portfolio2_data)

        assert portfolio1.id == 1
        assert portfolio2.id == 2
        assert portfolio1.name == "Portfolio 1"
        assert portfolio2.name == "Portfolio 2"

    @pytest.mark.asyncio
    async def test_get_portfolio(self, portfolio_service):
        "Test retrieving a portfolio by ID"
        portfolio_data = PortfolioCreate(name="Test Portfolio")
        created_portfolio = await portfolio_service.create_portfolio(portfolio_data)

        retrieved_portfolio = await portfolio_service.get_portfolio(
            created_portfolio.id
        )

        assert retrieved_portfolio is not None
        assert retrieved_portfolio.id == created_portfolio.id
        assert retrieved_portfolio.name == created_portfolio.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_portfolio(self, portfolio_service):
        "Test retrieving a non-existent portfolio"
        portfolio = await portfolio_service.get_portfolio(999)
        assert portfolio is None

    @pytest.mark.asyncio
    async def test_get_portfolios(self, portfolio_service):
        "Test retrieving all portfolios"
        portfolio_data1 = PortfolioCreate(name="Portfolio 1")
        portfolio_data2 = PortfolioCreate(name="Portfolio 2")

        await portfolio_service.create_portfolio(portfolio_data1)
        await portfolio_service.create_portfolio(portfolio_data2)

        portfolios = await portfolio_service.get_portfolios()

        assert len(portfolios) == 2
        assert portfolios[0].name == "Portfolio 1"
        assert portfolios[1].name == "Portfolio 2"

    @pytest.mark.asyncio
    async def test_create_position(self, portfolio_service):
        "Test position creation without global variables"
        # First create a portfolio
        portfolio_data = PortfolioCreate(name="Test Portfolio")
        portfolio = await portfolio_service.create_portfolio(portfolio_data)

        # Then create a position
        position_data = PositionCreate(
            portfolio_id=portfolio.id,
            secid="SBER",
            quantity=100,
            target_weight=Decimal("0.25"),
        )

        position = await portfolio_service.create_position(position_data)

        assert position.id == 1
        assert position.portfolio_id == portfolio.id
        assert position.secid == "SBER"
        assert position.quantity == 100
        assert position.target_weight == Decimal("0.25")

    @pytest.mark.asyncio
    async def test_create_multiple_positions(self, portfolio_service):
        "Test that position ID generation works correctly"
        portfolio_data = PortfolioCreate(name="Test Portfolio")
        portfolio = await portfolio_service.create_portfolio(portfolio_data)

        position1_data = PositionCreate(
            portfolio_id=portfolio.id, secid="SBER", quantity=100
        )
        position2_data = PositionCreate(
            portfolio_id=portfolio.id, secid="GAZP", quantity=50
        )

        position1 = await portfolio_service.create_position(position1_data)
        position2 = await portfolio_service.create_position(position2_data)

        assert position1.id == 1
        assert position2.id == 2
        assert position1.secid == "SBER"
        assert position2.secid == "GAZP"

    @pytest.mark.asyncio
    async def test_get_portfolio_positions(self, portfolio_service):
        "Test retrieving positions for a portfolio"
        portfolio_data = PortfolioCreate(name="Test Portfolio")
        portfolio = await portfolio_service.create_portfolio(portfolio_data)

        position1_data = PositionCreate(
            portfolio_id=portfolio.id, secid="SBER", quantity=100
        )
        position2_data = PositionCreate(
            portfolio_id=portfolio.id, secid="GAZP", quantity=50
        )

        await portfolio_service.create_position(position1_data)
        await portfolio_service.create_position(position2_data)

        positions = await portfolio_service.get_portfolio_positions(portfolio.id)

        assert len(positions) == 2
        assert positions[0].secid in ["SBER", "GAZP"]
        assert positions[1].secid in ["SBER", "GAZP"]

    @pytest.mark.asyncio
    async def test_update_position_market_data(self, portfolio_service):
        "Test updating position market data"
        portfolio_data = PortfolioCreate(name="Test Portfolio")
        portfolio = await portfolio_service.create_portfolio(portfolio_data)

        position_data = PositionCreate(
            portfolio_id=portfolio.id, secid="SBER", quantity=100
        )
        position = await portfolio_service.create_position(position_data)

        # Update with market data
        market_price = Decimal("250.00")
        updated_position = await portfolio_service.update_position_market_data(
            position.id, market_price
        )

        assert updated_position is not None
        assert updated_position.market_price == market_price
        assert updated_position.market_value == Decimal("25000.00")  # 100 * 250

    @pytest.mark.asyncio
    async def test_get_portfolio_summary(self, portfolio_service):
        "Test getting portfolio summary"
        portfolio_data = PortfolioCreate(name="Test Portfolio")
        portfolio = await portfolio_service.create_portfolio(portfolio_data)

        position_data = PositionCreate(
            portfolio_id=portfolio.id, secid="SBER", quantity=100
        )
        await portfolio_service.create_position(position_data)

        summary = await portfolio_service.get_portfolio_summary(portfolio.id)

        assert summary is not None
        assert summary.portfolio.id == portfolio.id
        assert summary.positions_count == 1
        assert len(summary.positions) == 1
        assert summary.positions[0].secid == "SBER"


class TestDataManagerIsolation:
    "Test that DataManager instances are properly isolated"

    def test_separate_instances_are_isolated(self):
        "Test that separate DataManager instances don't share state"
        dm1 = DataManager()
        dm2 = DataManager()

        # Create data in first instance
        from app.modules.portfolio.models import Portfolio

        portfolio1 = Portfolio(id=1, name="Portfolio 1")
        dm1.add_portfolio(portfolio1)

        # Second instance should not have this data
        retrieved = dm2.get_portfolio(1)
        assert retrieved is None

        # But first instance should still have it
        retrieved = dm1.get_portfolio(1)
        assert retrieved is not None
        assert retrieved.name == "Portfolio 1"

    def test_id_counters_are_independent(self):
        "Test that ID counters are independent between instances"
        dm1 = DataManager()
        dm2 = DataManager()

        # Get IDs from both instances
        id1_dm1 = dm1.get_next_portfolio_id()
        id1_dm2 = dm2.get_next_portfolio_id()

        # Both should start at 1
        assert id1_dm1 == 1
        assert id1_dm2 == 1

        # Next IDs should be independent
        id2_dm1 = dm1.get_next_portfolio_id()
        id2_dm2 = dm2.get_next_portfolio_id()

        assert id2_dm1 == 2
        assert id2_dm2 == 2
