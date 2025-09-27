from app.storage import DataManager
from app.modules.portfolio.models import Portfolio, Position
from app.modules.marketdata.models import Security, Quote
from decimal import Decimal
from datetime import datetime


class TestDataManager:

    def test_data_manager_initialization(self):
        dm = DataManager()

        # Check initial state
        assert len(dm.get_all_portfolios()) == 0
        assert len(dm.get_all_positions()) == 0
        assert len(dm.get_all_securities()) == 0

        # Check initial ID counters
        assert dm.get_next_portfolio_id() == 1
        assert dm.get_next_position_id() == 1
        assert dm.get_next_security_id() == 1
        assert dm.get_next_quote_id() == 1

    def test_portfolio_operations(self):
        dm = DataManager()

        # Create portfolio
        portfolio = Portfolio(
            id=1, name="Test Portfolio", description="Test Description"
        )
        dm.add_portfolio(portfolio)

        # Retrieve portfolio
        retrieved = dm.get_portfolio(1)
        assert retrieved is not None
        assert retrieved.id == 1
        assert retrieved.name == "Test Portfolio"
        assert retrieved.description == "Test Description"

        # Get all portfolios
        all_portfolios = dm.get_all_portfolios()
        assert len(all_portfolios) == 1
        assert all_portfolios[0].id == 1

        # Get non-existent portfolio
        non_existent = dm.get_portfolio(999)
        assert non_existent is None

    def test_position_operations(self):
        dm = DataManager()

        # Create position
        position = Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=100,
            target_weight=Decimal("0.25"),
        )
        dm.add_position(position)

        # Retrieve position
        retrieved = dm.get_position(1)
        assert retrieved is not None
        assert retrieved.id == 1
        assert retrieved.portfolio_id == 1
        assert retrieved.secid == "SBER"
        assert retrieved.quantity == 100

        # Get all positions
        all_positions = dm.get_all_positions()
        assert len(all_positions) == 1
        assert all_positions[0].id == 1

        # Get positions for portfolio
        portfolio_positions = dm.get_positions_for_portfolio(1)
        assert len(portfolio_positions) == 1
        assert portfolio_positions[0].portfolio_id == 1

        # Get positions for non-existent portfolio
        empty_positions = dm.get_positions_for_portfolio(999)
        assert len(empty_positions) == 0

    def test_security_operations(self):
        dm = DataManager()

        # Create security
        security = Security(secid="SBER", name="Сбербанк", isin="RU0009029540")
        dm.add_security(security)

        # Retrieve security
        retrieved = dm.get_security("SBER")
        assert retrieved is not None
        assert retrieved.secid == "SBER"
        assert retrieved.name == "Сбербанк"
        assert retrieved.isin == "RU0009029540"

        # Check security exists
        assert dm.security_exists("SBER") is True
        assert dm.security_exists("NONEXISTENT") is False

        # Get all securities
        all_securities = dm.get_all_securities()
        assert len(all_securities) == 1
        assert all_securities[0].secid == "SBER"

        # Get non-existent security
        non_existent = dm.get_security("NONEXISTENT")
        assert non_existent is None

    def test_quote_operations(self):
        dm = DataManager()

        # Create quote
        quote = Quote(
            secid="SBER",
            timestamp=datetime.now(),
            price=Decimal("250.00"),
            volume=Decimal("1000"),
        )
        dm.add_quote(quote)

        # Get quotes for security
        quotes = dm.get_quotes("SBER")
        assert len(quotes) == 1
        assert quotes[0].secid == "SBER"
        assert quotes[0].price == Decimal("250.00")

        # Get latest quote
        latest = dm.get_latest_quote("SBER")
        assert latest is not None
        assert latest.secid == "SBER"
        assert latest.price == Decimal("250.00")

        # Add another quote
        quote2 = Quote(
            secid="SBER",
            timestamp=datetime.now(),
            price=Decimal("260.00"),
            volume=Decimal("1500"),
        )
        dm.add_quote(quote2)

        # Check that latest quote is updated
        quotes = dm.get_quotes("SBER")
        assert len(quotes) == 2

        latest = dm.get_latest_quote("SBER")
        assert latest.price == Decimal("260.00")

        # Get quotes for non-existent security
        empty_quotes = dm.get_quotes("NONEXISTENT")
        assert len(empty_quotes) == 0

        no_quote = dm.get_latest_quote("NONEXISTENT")
        assert no_quote is None

    def test_id_counters(self):
        dm = DataManager()

        # Test portfolio ID counter
        assert dm.get_next_portfolio_id() == 1
        assert dm.get_next_portfolio_id() == 2
        assert dm.get_next_portfolio_id() == 3

        # Test position ID counter
        assert dm.get_next_position_id() == 1
        assert dm.get_next_position_id() == 2

        # Test security ID counter
        assert dm.get_next_security_id() == 1
        assert dm.get_next_security_id() == 2

        # Test quote ID counter
        assert dm.get_next_quote_id() == 1
        assert dm.get_next_quote_id() == 2

    def test_clear_all(self):
        dm = DataManager()

        # Add some data
        portfolio = Portfolio(id=1, name="Test Portfolio")
        position = Position(id=1, portfolio_id=1, secid="SBER", quantity=100)
        security = Security(secid="SBER", name="Сбербанк")
        quote = Quote(
            secid="SBER",
            timestamp=datetime.now(),
            price=Decimal("250.00"),
            volume=Decimal("1000"),
        )

        dm.add_portfolio(portfolio)
        dm.add_position(position)
        dm.add_security(security)
        dm.add_quote(quote)

        # Advance ID counters
        dm.get_next_portfolio_id()
        dm.get_next_position_id()

        # Verify data exists
        assert len(dm.get_all_portfolios()) == 1
        assert len(dm.get_all_positions()) == 1
        assert len(dm.get_all_securities()) == 1
        assert len(dm.get_quotes("SBER")) == 1

        # Clear all
        dm.clear_all()

        # Verify everything is cleared
        assert len(dm.get_all_portfolios()) == 0
        assert len(dm.get_all_positions()) == 0
        assert len(dm.get_all_securities()) == 0
        assert len(dm.get_quotes("SBER")) == 0

        # Verify ID counters are reset
        assert dm.get_next_portfolio_id() == 1
        assert dm.get_next_position_id() == 1
        assert dm.get_next_security_id() == 1
        assert dm.get_next_quote_id() == 1

    def test_multiple_portfolios_and_positions(self):
        dm = DataManager()

        # Create portfolios
        portfolio1 = Portfolio(id=1, name="Portfolio 1")
        portfolio2 = Portfolio(id=2, name="Portfolio 2")
        dm.add_portfolio(portfolio1)
        dm.add_portfolio(portfolio2)

        # Create positions for different portfolios
        pos1 = Position(id=1, portfolio_id=1, secid="SBER", quantity=100)
        pos2 = Position(id=2, portfolio_id=1, secid="GAZP", quantity=50)
        pos3 = Position(id=3, portfolio_id=2, secid="SBER", quantity=200)

        dm.add_position(pos1)
        dm.add_position(pos2)
        dm.add_position(pos3)

        # Test portfolio-specific position retrieval
        portfolio1_positions = dm.get_positions_for_portfolio(1)
        portfolio2_positions = dm.get_positions_for_portfolio(2)

        assert len(portfolio1_positions) == 2
        assert len(portfolio2_positions) == 1

        # Check specific positions
        portfolio1_secids = [pos.secid for pos in portfolio1_positions]
        assert "SBER" in portfolio1_secids
        assert "GAZP" in portfolio1_secids

        assert portfolio2_positions[0].secid == "SBER"
        assert portfolio2_positions[0].quantity == 200
