"""
Comprehensive tests for storage.py
"""

import pytest
from datetime import datetime, date
from decimal import Decimal

from app.storage import DataManager, get_data_manager
from app.modules.marketdata.models import Security, Quote
from app.modules.portfolio.models import Portfolio, Position


class TestDataManager:
    """Tests for DataManager class"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        self.manager = DataManager()
        
    def test_data_manager_initialization(self):
        """Test DataManager initialization"""
        manager = DataManager()
        
        # Check that all stores are initialized as empty
        assert len(manager.get_all_securities()) == 0
        assert len(manager.get_all_portfolios()) == 0
        assert len(manager.get_all_positions()) == 0
        assert len(manager.get_all_transactions()) == 0
        
        # Check initial ID counters
        assert manager.get_next_security_id() == 1
        assert manager.get_next_quote_id() == 1
        assert manager.get_next_portfolio_id() == 1
        assert manager.get_next_position_id() == 1
        assert manager.get_next_transaction_id() == 1
        
    def test_id_counter_increments(self):
        """Test that ID counters increment properly"""
        # Security IDs
        assert self.manager.get_next_security_id() == 1
        assert self.manager.get_next_security_id() == 2
        assert self.manager.get_next_security_id() == 3
        
        # Quote IDs
        assert self.manager.get_next_quote_id() == 1
        assert self.manager.get_next_quote_id() == 2
        
        # Portfolio IDs
        assert self.manager.get_next_portfolio_id() == 1
        assert self.manager.get_next_portfolio_id() == 2
        
        # Position IDs
        assert self.manager.get_next_position_id() == 1
        assert self.manager.get_next_position_id() == 2
        
        # Transaction IDs
        assert self.manager.get_next_transaction_id() == 1
        assert self.manager.get_next_transaction_id() == 2


class TestSecurityOperations:
    """Tests for security-related operations"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        self.manager = DataManager()
        
    def test_add_and_get_security(self):
        """Test adding and retrieving security"""
        security = Security(
            secid="SBER",
            name="ПАО Сбербанк",
            isin="RU0009029540",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        
        # Add security
        self.manager.add_security(security)
        
        # Retrieve security
        retrieved = self.manager.get_security("SBER")
        assert retrieved is not None
        assert retrieved.secid == "SBER"
        assert retrieved.name == "ПАО Сбербанк"
        
    def test_get_nonexistent_security(self):
        """Test retrieving non-existent security"""
        result = self.manager.get_security("NONEXISTENT")
        assert result is None
        
    def test_security_exists(self):
        """Test checking if security exists"""
        security = Security(
            secid="GAZP",
            name="ПАО Газпром",
            isin="RU0009024277",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        
        # Should not exist initially
        assert not self.manager.security_exists("GAZP")
        
        # Add security
        self.manager.add_security(security)
        
        # Should exist now
        assert self.manager.security_exists("GAZP")
        
    def test_get_all_securities(self):
        """Test getting all securities"""
        # Initially empty
        assert len(self.manager.get_all_securities()) == 0
        
        # Add securities
        security1 = Security(
            secid="SBER",
            name="ПАО Сбербанк",
            isin="RU0009029540",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        security2 = Security(
            secid="GAZP",
            name="ПАО Газпром",
            isin="RU0009024277",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        
        self.manager.add_security(security1)
        self.manager.add_security(security2)
        
        # Check all securities
        all_securities = self.manager.get_all_securities()
        assert len(all_securities) == 2
        
        secids = [s.secid for s in all_securities]
        assert "SBER" in secids
        assert "GAZP" in secids
        
    def test_update_existing_security(self):
        """Test updating existing security"""
        security1 = Security(
            secid="SBER",
            name="ПАО Сбербанк",
            isin="RU0009029540",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        
        security2 = Security(
            secid="SBER",
            name="ПАО Сбербанк (обновлен)",
            isin="RU0009029540",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        
        # Add first version
        self.manager.add_security(security1)
        assert self.manager.get_security("SBER").name == "ПАО Сбербанк"
        
        # Update with second version
        self.manager.add_security(security2)
        assert self.manager.get_security("SBER").name == "ПАО Сбербанк (обновлен)"
        
        # Should still be only one security
        assert len(self.manager.get_all_securities()) == 1


class TestQuoteOperations:
    """Tests for quote-related operations"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        self.manager = DataManager()
        
    def test_add_and_get_quotes(self):
        """Test adding and retrieving quotes"""
        from datetime import datetime
        
        quote1 = Quote(
            secid="SBER",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            price=Decimal("252.0"),
            volume=Decimal("1000000"),
            bid=Decimal("251.5"),
            ask=Decimal("252.5")
        )
        
        quote2 = Quote(
            secid="SBER",
            timestamp=datetime(2024, 1, 16, 10, 0, 0),
            price=Decimal("257.0"),
            volume=Decimal("1200000"),
            bid=Decimal("256.5"),
            ask=Decimal("257.5")
        )
        
        # Add quotes
        self.manager.add_quote(quote1)
        self.manager.add_quote(quote2)
        
        # Retrieve quotes
        quotes = self.manager.get_quotes("SBER")
        assert len(quotes) == 2
        assert quotes[0].timestamp == datetime(2024, 1, 15, 10, 0, 0)
        assert quotes[1].timestamp == datetime(2024, 1, 16, 10, 0, 0)
        
    def test_get_quotes_nonexistent_security(self):
        """Test getting quotes for non-existent security"""
        quotes = self.manager.get_quotes("NONEXISTENT")
        assert quotes == []
        
    def test_get_latest_quote(self):
        """Test getting latest quote"""
        from datetime import datetime
        
        # No quotes initially
        assert self.manager.get_latest_quote("SBER") is None
        
        quote1 = Quote(
            secid="SBER",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            price=Decimal("252.0"),
            volume=Decimal("1000000"),
            bid=Decimal("251.5"),
            ask=Decimal("252.5")
        )
        
        quote2 = Quote(
            secid="SBER",
            timestamp=datetime(2024, 1, 16, 10, 0, 0),
            price=Decimal("257.0"),
            volume=Decimal("1200000"),
            bid=Decimal("256.5"),
            ask=Decimal("257.5")
        )
        
        # Add quotes
        self.manager.add_quote(quote1)
        self.manager.add_quote(quote2)
        
        # Get latest quote
        latest = self.manager.get_latest_quote("SBER")
        assert latest is not None
        assert latest.timestamp == datetime(2024, 1, 16, 10, 0, 0)
        assert latest.price == Decimal("257.0")
        
    def test_quotes_different_securities(self):
        """Test quotes for different securities"""
        from datetime import datetime
        
        quote_sber = Quote(
            secid="SBER",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            price=Decimal("252.0"),
            volume=Decimal("1000000"),
            bid=Decimal("251.5"),
            ask=Decimal("252.5")
        )
        
        quote_gazp = Quote(
            secid="GAZP",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            price=Decimal("152.0"),
            volume=Decimal("2000000"),
            bid=Decimal("151.5"),
            ask=Decimal("152.5")
        )
        
        # Add quotes
        self.manager.add_quote(quote_sber)
        self.manager.add_quote(quote_gazp)
        
        # Check separate security quotes
        sber_quotes = self.manager.get_quotes("SBER")
        gazp_quotes = self.manager.get_quotes("GAZP")
        
        assert len(sber_quotes) == 1
        assert len(gazp_quotes) == 1
        assert sber_quotes[0].secid == "SBER"
        assert gazp_quotes[0].secid == "GAZP"


class TestPortfolioOperations:
    """Tests for portfolio-related operations"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        self.manager = DataManager()
        
    def test_add_and_get_portfolio(self):
        """Test adding and retrieving portfolio"""
        portfolio = Portfolio(
            id=1,
            name="Test Portfolio",
            description="Test portfolio description",
            total_value=Decimal("100000"),
            cash_balance=Decimal("10000"),
            is_active=True
        )
        
        # Add portfolio
        self.manager.add_portfolio(portfolio)
        
        # Retrieve portfolio
        retrieved = self.manager.get_portfolio(1)
        assert retrieved is not None
        assert retrieved.id == 1
        assert retrieved.name == "Test Portfolio"
        assert retrieved.total_value == Decimal("100000")
        
    def test_get_nonexistent_portfolio(self):
        """Test retrieving non-existent portfolio"""
        result = self.manager.get_portfolio(999)
        assert result is None
        
    def test_get_all_portfolios(self):
        """Test getting all portfolios"""
        # Initially empty
        assert len(self.manager.get_all_portfolios()) == 0
        
        # Add portfolios
        portfolio1 = Portfolio(
            id=1,
            name="Portfolio 1",
            description="First portfolio",
            total_value=Decimal("100000"),
            cash_balance=Decimal("10000"),
            is_active=True
        )
        portfolio2 = Portfolio(
            id=2,
            name="Portfolio 2",
            description="Second portfolio",
            total_value=Decimal("200000"),
            cash_balance=Decimal("20000"),
            is_active=True
        )
        
        self.manager.add_portfolio(portfolio1)
        self.manager.add_portfolio(portfolio2)
        
        # Check all portfolios
        all_portfolios = self.manager.get_all_portfolios()
        assert len(all_portfolios) == 2
        
        portfolio_ids = [p.id for p in all_portfolios]
        assert 1 in portfolio_ids
        assert 2 in portfolio_ids
        
    def test_portfolios_property(self):
        """Test portfolios property access"""
        portfolio = Portfolio(
            id=1,
            name="Test Portfolio",
            description="Test portfolio description",
            total_value=Decimal("100000"),
            cash_balance=Decimal("10000"),
            is_active=True
        )
        
        self.manager.add_portfolio(portfolio)
        
        # Access via property
        portfolios_store = self.manager.portfolios
        assert 1 in portfolios_store
        assert portfolios_store[1].name == "Test Portfolio"


class TestPositionOperations:
    """Tests for position-related operations"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        self.manager = DataManager()
        
    def test_add_and_get_position(self):
        """Test adding and retrieving position"""
        position = Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=Decimal("100"),
            avg_price=Decimal("250.0"),
            market_price=Decimal("260.0")
        )
        
        # Add position
        self.manager.add_position(position)
        
        # Retrieve position
        retrieved = self.manager.get_position(1)
        assert retrieved is not None
        assert retrieved.id == 1
        assert retrieved.portfolio_id == 1
        assert retrieved.secid == "SBER"
        assert retrieved.quantity == Decimal("100")
        
    def test_get_nonexistent_position(self):
        """Test retrieving non-existent position"""
        result = self.manager.get_position(999)
        assert result is None
        
    def test_get_positions_for_portfolio(self):
        """Test getting positions for specific portfolio"""
        position1 = Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=Decimal("100"),
            avg_price=Decimal("250.0"),
            market_price=Decimal("260.0")
        )
        
        position2 = Position(
            id=2,
            portfolio_id=1,
            secid="GAZP",
            quantity=Decimal("200"),
            avg_price=Decimal("150.0"),
            market_price=Decimal("155.0")
        )
        
        position3 = Position(
            id=3,
            portfolio_id=2,
            secid="SBER",
            quantity=Decimal("50"),
            avg_price=Decimal("255.0"),
            market_price=Decimal("260.0")
        )
        
        # Add positions
        self.manager.add_position(position1)
        self.manager.add_position(position2)
        self.manager.add_position(position3)
        
        # Get positions for portfolio 1
        portfolio1_positions = self.manager.get_positions_for_portfolio(1)
        assert len(portfolio1_positions) == 2
        
        secids = [p.secid for p in portfolio1_positions]
        assert "SBER" in secids
        assert "GAZP" in secids
        
        # Get positions for portfolio 2
        portfolio2_positions = self.manager.get_positions_for_portfolio(2)
        assert len(portfolio2_positions) == 1
        assert portfolio2_positions[0].secid == "SBER"
        
        # Get positions for non-existent portfolio
        empty_positions = self.manager.get_positions_for_portfolio(999)
        assert len(empty_positions) == 0
        
    def test_get_all_positions(self):
        """Test getting all positions"""
        # Initially empty
        assert len(self.manager.get_all_positions()) == 0
        
        # Add positions
        position1 = Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=Decimal("100"),
            avg_price=Decimal("250.0"),
            market_price=Decimal("260.0")
        )
        
        position2 = Position(
            id=2,
            portfolio_id=2,
            secid="GAZP",
            quantity=Decimal("200"),
            avg_price=Decimal("150.0"),
            market_price=Decimal("155.0")
        )
        
        self.manager.add_position(position1)
        self.manager.add_position(position2)
        
        # Check all positions
        all_positions = self.manager.get_all_positions()
        assert len(all_positions) == 2
        
        position_ids = [p.id for p in all_positions]
        assert 1 in position_ids
        assert 2 in position_ids


class TestTransactionOperations:
    """Tests for transaction-related operations (using mock Transaction)"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        self.manager = DataManager()
        
    def create_mock_transaction(self, tx_id: int, portfolio_id: int, secid: str = "SBER"):
        """Create a mock transaction object"""
        class MockTransaction:
            def __init__(self, id: int, portfolio_id: int, secid: str):
                self.id = id
                self.portfolio_id = portfolio_id
                self.secid = secid
                
        return MockTransaction(tx_id, portfolio_id, secid)
        
    def test_add_and_get_transaction(self):
        """Test adding and retrieving transaction"""
        transaction = self.create_mock_transaction(1, 1, "SBER")
        
        # Add transaction
        self.manager.add_transaction(transaction)
        
        # Retrieve transaction
        retrieved = self.manager.get_transaction(1)
        assert retrieved is not None
        assert retrieved.id == 1
        assert retrieved.portfolio_id == 1
        assert retrieved.secid == "SBER"
        
    def test_get_nonexistent_transaction(self):
        """Test retrieving non-existent transaction"""
        result = self.manager.get_transaction(999)
        assert result is None
        
    def test_get_transactions_for_portfolio(self):
        """Test getting transactions for specific portfolio"""
        transaction1 = self.create_mock_transaction(1, 1, "SBER")
        transaction2 = self.create_mock_transaction(2, 1, "GAZP")
        transaction3 = self.create_mock_transaction(3, 2, "SBER")
        
        # Add transactions
        self.manager.add_transaction(transaction1)
        self.manager.add_transaction(transaction2)
        self.manager.add_transaction(transaction3)
        
        # Get transactions for portfolio 1
        portfolio1_transactions = self.manager.get_transactions_for_portfolio(1)
        assert len(portfolio1_transactions) == 2
        
        secids = [t.secid for t in portfolio1_transactions]
        assert "SBER" in secids
        assert "GAZP" in secids
        
        # Get transactions for portfolio 2
        portfolio2_transactions = self.manager.get_transactions_for_portfolio(2)
        assert len(portfolio2_transactions) == 1
        assert portfolio2_transactions[0].secid == "SBER"
        
        # Get transactions for non-existent portfolio
        empty_transactions = self.manager.get_transactions_for_portfolio(999)
        assert len(empty_transactions) == 0
        
    def test_get_all_transactions(self):
        """Test getting all transactions"""
        # Initially empty
        assert len(self.manager.get_all_transactions()) == 0
        
        # Add transactions
        transaction1 = self.create_mock_transaction(1, 1, "SBER")
        transaction2 = self.create_mock_transaction(2, 2, "GAZP")
        
        self.manager.add_transaction(transaction1)
        self.manager.add_transaction(transaction2)
        
        # Check all transactions
        all_transactions = self.manager.get_all_transactions()
        assert len(all_transactions) == 2
        
        transaction_ids = [t.id for t in all_transactions]
        assert 1 in transaction_ids
        assert 2 in transaction_ids


class TestStrategyStores:
    """Tests for strategy-related stores"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        self.manager = DataManager()
        
    def test_strategies_property_access(self):
        """Test accessing strategies store"""
        strategies_store = self.manager.strategies
        assert isinstance(strategies_store, dict)
        assert len(strategies_store) == 0
        
        # Can modify the store
        strategies_store[1] = "mock_strategy"
        assert 1 in self.manager.strategies
        
    def test_portfolio_strategies_property_access(self):
        """Test accessing portfolio strategies store"""
        portfolio_strategies_store = self.manager.portfolio_strategies
        assert isinstance(portfolio_strategies_store, dict)
        assert len(portfolio_strategies_store) == 0
        
        # Can modify the store
        portfolio_strategies_store[1] = "mock_portfolio_strategy"
        assert 1 in self.manager.portfolio_strategies


class TestClearAll:
    """Tests for clear_all functionality"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        self.manager = DataManager()
        
    def test_clear_all_functionality(self):
        """Test clearing all data"""
        from datetime import datetime
        
        # Add some data
        security = Security(
            secid="SBER",
            name="ПАО Сбербанк",
            isin="RU0009029540",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        
        portfolio = Portfolio(
            id=1,
            name="Test Portfolio",
            description="Test",
            total_value=Decimal("100000"),
            cash_balance=Decimal("10000"),
            is_active=True
        )
        
        position = Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=Decimal("100"),
            avg_price=Decimal("250.0"),
            market_price=Decimal("260.0")
        )
        
        quote = Quote(
            secid="SBER",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            price=Decimal("252.0"),
            volume=Decimal("1000000"),
            bid=Decimal("251.5"),
            ask=Decimal("252.5")
        )
        
        # Add data to manager
        self.manager.add_security(security)
        self.manager.add_portfolio(portfolio)
        self.manager.add_position(position)
        self.manager.add_quote(quote)
        
        # Increment some ID counters
        self.manager.get_next_security_id()  # Should be 1
        self.manager.get_next_portfolio_id()  # Should be 1
        
        # Verify data exists
        assert len(self.manager.get_all_securities()) == 1
        assert len(self.manager.get_all_portfolios()) == 1
        assert len(self.manager.get_all_positions()) == 1
        assert len(self.manager.get_quotes("SBER")) == 1
        assert self.manager.get_next_security_id() == 2  # Should be 2 now
        assert self.manager.get_next_portfolio_id() == 2  # Should be 2 now
        
        # Clear all data
        self.manager.clear_all()
        
        # Verify everything is cleared
        assert len(self.manager.get_all_securities()) == 0
        assert len(self.manager.get_all_portfolios()) == 0
        assert len(self.manager.get_all_positions()) == 0
        assert len(self.manager.get_all_transactions()) == 0
        assert len(self.manager.get_quotes("SBER")) == 0
        
        # Verify ID counters are reset
        assert self.manager.get_next_security_id() == 1
        assert self.manager.get_next_quote_id() == 1
        assert self.manager.get_next_portfolio_id() == 1
        assert self.manager.get_next_position_id() == 1
        assert self.manager.get_next_transaction_id() == 1
        
        # Verify strategy stores are cleared
        assert len(self.manager.strategies) == 0
        assert len(self.manager.portfolio_strategies) == 0


class TestDataManagerFactory:
    """Tests for data manager factory function"""
    
    def test_get_data_manager_singleton(self):
        """Test that get_data_manager returns the same instance"""
        manager1 = get_data_manager()
        manager2 = get_data_manager()
        
        # Should be the same instance
        assert manager1 is manager2
        
        # Add some data to one instance
        security = Security(
            secid="SBER",
            name="ПАО Сбербанк",
            isin="RU0009029540",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        
        manager1.add_security(security)
        
        # Should be accessible from other reference
        assert manager2.security_exists("SBER")
        assert len(manager2.get_all_securities()) == 1
        
    def test_data_manager_type(self):
        """Test that factory returns DataManager instance"""
        manager = get_data_manager()
        assert isinstance(manager, DataManager)


class TestDataManagerIntegration:
    """Integration tests for DataManager"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        self.manager = DataManager()
        
    def test_complete_portfolio_workflow(self):
        """Test complete workflow with securities, quotes, portfolios, and positions"""
        from datetime import datetime
        
        # Add security
        security = Security(
            secid="SBER",
            name="ПАО Сбербанк",
            isin="RU0009029540",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        self.manager.add_security(security)
        
        # Add quotes
        quote1 = Quote(
            secid="SBER",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            price=Decimal("252.0"),
            volume=Decimal("1000000"),
            bid=Decimal("251.5"),
            ask=Decimal("252.5")
        )
        
        quote2 = Quote(
            secid="SBER",
            timestamp=datetime(2024, 1, 16, 10, 0, 0),
            price=Decimal("257.0"),
            volume=Decimal("1200000"),
            bid=Decimal("256.5"),
            ask=Decimal("257.5")
        )
        
        self.manager.add_quote(quote1)
        self.manager.add_quote(quote2)
        
        # Add portfolio
        portfolio = Portfolio(
            id=1,
            name="Test Portfolio",
            description="Test portfolio",
            total_value=Decimal("100000"),
            cash_balance=Decimal("10000"),
            is_active=True
        )
        self.manager.add_portfolio(portfolio)
        
        # Add position
        position = Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=Decimal("100"),
            avg_price=Decimal("250.0"),
            market_price=Decimal("257.0")  # Latest quote price
        )
        self.manager.add_position(position)
        
        # Verify the complete workflow
        assert self.manager.security_exists("SBER")
        assert len(self.manager.get_quotes("SBER")) == 2
        assert self.manager.get_latest_quote("SBER").price == Decimal("257.0")
        assert len(self.manager.get_all_portfolios()) == 1
        assert len(self.manager.get_positions_for_portfolio(1)) == 1
        
        # Check position details
        portfolio_positions = self.manager.get_positions_for_portfolio(1)
        position = portfolio_positions[0]
        assert position.secid == "SBER"
        assert position.quantity == Decimal("100")
        assert position.market_price == Decimal("257.0")
        
    def test_multiple_portfolios_and_positions(self):
        """Test managing multiple portfolios with different positions"""
        # Add securities
        sber = Security(
            secid="SBER",
            name="ПАО Сбербанк",
            isin="RU0009029540",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        
        gazp = Security(
            secid="GAZP",
            name="ПАО Газпром",
            isin="RU0009024277",
            engine="stock",
            market="shares",
            board="TQBR"
        )
        
        self.manager.add_security(sber)
        self.manager.add_security(gazp)
        
        # Add portfolios
        portfolio1 = Portfolio(
            id=1,
            name="Conservative Portfolio",
            description="Conservative investment strategy",
            total_value=Decimal("100000"),
            cash_balance=Decimal("10000"),
            is_active=True
        )
        
        portfolio2 = Portfolio(
            id=2,
            name="Aggressive Portfolio",
            description="Aggressive investment strategy",
            total_value=Decimal("200000"),
            cash_balance=Decimal("20000"),
            is_active=True
        )
        
        self.manager.add_portfolio(portfolio1)
        self.manager.add_portfolio(portfolio2)
        
        # Add positions
        positions = [
            Position(
                id=1,
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                avg_price=Decimal("250.0"),
                market_price=Decimal("257.0")
            ),
            Position(
                id=2,
                portfolio_id=1,
                secid="GAZP",
                quantity=Decimal("200"),
                avg_price=Decimal("150.0"),
                market_price=Decimal("155.0")
            ),
            Position(
                id=3,
                portfolio_id=2,
                secid="SBER",
                quantity=Decimal("500"),
                avg_price=Decimal("255.0"),
                market_price=Decimal("257.0")
            )
        ]
        
        for position in positions:
            self.manager.add_position(position)
            
        # Verify portfolios and their positions
        portfolio1_positions = self.manager.get_positions_for_portfolio(1)
        portfolio2_positions = self.manager.get_positions_for_portfolio(2)
        
        assert len(portfolio1_positions) == 2  # SBER + GAZP
        assert len(portfolio2_positions) == 1  # SBER only
        
        # Check specific position quantities
        portfolio1_secids = [p.secid for p in portfolio1_positions]
        assert "SBER" in portfolio1_secids
        assert "GAZP" in portfolio1_secids
        
        portfolio2_secids = [p.secid for p in portfolio2_positions]
        assert "SBER" in portfolio2_secids
        assert "GAZP" not in portfolio2_secids
        
        # Verify total positions across all portfolios
        all_positions = self.manager.get_all_positions()
        assert len(all_positions) == 3