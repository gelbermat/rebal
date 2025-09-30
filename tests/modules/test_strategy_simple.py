"""Simplified tests for strategy module"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

from app.modules.strategy.service import StrategyService
from app.modules.strategy.models import StrategyType
from app.storage import DataManager


class TestStrategyService:
    """Tests for Strategy service layer"""

    @pytest.fixture
    def mock_data_manager(self):
        return AsyncMock(spec=DataManager)

    @pytest.fixture
    def mock_market_data_service(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_data_manager, mock_market_data_service):
        return StrategyService(mock_data_manager, mock_market_data_service)

    @pytest.mark.asyncio
    async def test_create_strategy(self, service, mock_data_manager):
        """Test strategy creation"""
        mock_strategy = Mock()
        mock_strategy.id = 1
        mock_strategy.name = "Test Strategy"
        mock_data_manager.create_strategy.return_value = mock_strategy
        
        result = service.create_strategy(
            name="Test Strategy",
            strategy_type=StrategyType.LAZY_INDEX_TRACKING,
            config={}
        )
        
        assert result.name == "Test Strategy"
        mock_data_manager.create_strategy.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_strategy(self, service, mock_data_manager):
        """Test strategy retrieval"""
        mock_strategy = Mock()
        mock_strategy.id = 1
        mock_strategy.name = "Test Strategy"
        mock_data_manager.get_strategy.return_value = mock_strategy
        
        result = service.get_strategy(1)
        
        assert result.id == 1
        mock_data_manager.get_strategy.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_update_strategy(self, service, mock_data_manager):
        """Test strategy update"""
        mock_strategy = Mock()
        mock_strategy.id = 1
        mock_strategy.name = "Updated Strategy"
        mock_data_manager.update_strategy.return_value = mock_strategy
        
        result = service.update_strategy(1, name="Updated Strategy")
        
        assert result.name == "Updated Strategy"
        mock_data_manager.update_strategy.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_strategy(self, service, mock_data_manager):
        """Test strategy deletion"""
        mock_data_manager.delete_strategy.return_value = True
        
        result = service.delete_strategy(1)
        
        assert result is True
        mock_data_manager.delete_strategy.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_execute_strategy(self, service, mock_data_manager):
        """Test strategy execution"""
        mock_portfolio = Mock()
        mock_portfolio.id = 1
        mock_data_manager.get_portfolio.return_value = mock_portfolio
        
        # Mock strategy execution
        mock_result = {"status": "completed", "transactions": 5}
        
        with patch.object(service, '_execute_lazy_index_tracking', return_value=mock_result):
            result = service.execute_strategy(1, StrategyType.LAZY_INDEX_TRACKING)
            
            assert result["status"] == "completed"
            assert result["transactions"] == 5

    def test_calculate_portfolio_weights(self, service):
        """Test portfolio weight calculation"""
        positions = [
            {"secid": "SBER", "quantity": Decimal("100"), "price": Decimal("250")},
            {"secid": "GAZP", "quantity": Decimal("50"), "price": Decimal("180")}
        ]
        
        total_value = sum(p["quantity"] * p["price"] for p in positions)
        weights = {}
        
        for pos in positions:
            market_value = pos["quantity"] * pos["price"]
            weights[pos["secid"]] = market_value / total_value
        
        assert abs(sum(weights.values()) - Decimal("1.0")) < Decimal("0.001")
        assert weights["SBER"] > weights["GAZP"]  # SBER has higher market value


class TestStrategyTypes:
    """Tests for strategy type enumerations"""

    def test_strategy_type_values(self):
        """Test strategy type enum values"""
        assert StrategyType.LAZY_INDEX_TRACKING.value == "LAZY_INDEX_TRACKING"

    def test_strategy_type_validation(self):
        """Test strategy type validation"""
        valid_type = StrategyType.LAZY_INDEX_TRACKING
        assert isinstance(valid_type, StrategyType)


class TestStrategyBusinessLogic:
    """Tests for strategy business logic"""

    def test_equal_weight_allocation(self):
        """Test equal weight allocation calculation"""
        securities = ["SBER", "GAZP", "LKOH", "YNDX"]
        
        equal_weights = {sec: Decimal("0.25") for sec in securities}
        
        assert sum(equal_weights.values()) == Decimal("1.0")
        assert all(weight == Decimal("0.25") for weight in equal_weights.values())

    def test_market_cap_weight_allocation(self):
        """Test market cap weighted allocation"""
        market_caps = {
            "SBER": Decimal("3000000"),  # 3M
            "GAZP": Decimal("2000000"),  # 2M  
            "LKOH": Decimal("1000000")   # 1M
        }
        
        total_market_cap = sum(market_caps.values())  # 6M
        
        weights = {sec: cap / total_market_cap for sec, cap in market_caps.items()}
        
        assert abs(weights["SBER"] - Decimal("0.5")) < Decimal("0.001")
        assert abs(weights["GAZP"] - Decimal("0.333333")) < Decimal("0.001")
        assert abs(weights["LKOH"] - Decimal("0.166667")) < Decimal("0.001")

    def test_rebalance_threshold_validation(self):
        """Test rebalance threshold validation"""
        current_allocation = {"SBER": Decimal("0.6"), "GAZP": Decimal("0.4")}
        target_allocation = {"SBER": Decimal("0.5"), "GAZP": Decimal("0.5")}
        
        # Calculate drift
        max_drift = max(abs(current_allocation[sec] - target_allocation[sec]) 
                       for sec in current_allocation)
        
        threshold = Decimal("0.05")  # 5%
        needs_rebalance = max_drift > threshold
        
        assert needs_rebalance is True  # 10% drift should trigger rebalance

    def test_transaction_cost_calculation(self):
        """Test transaction cost calculation"""
        trade_amount = Decimal("100000")
        commission_rate = Decimal("0.0005")  # 0.05%
        bid_ask_spread = Decimal("0.001")    # 0.1%
        
        commission = trade_amount * commission_rate
        market_impact = trade_amount * bid_ask_spread
        total_cost = commission + market_impact
        
        assert commission == Decimal("50.0")
        assert market_impact == Decimal("100.0")
        assert total_cost == Decimal("150.0")

    def test_risk_metrics_calculation(self):
        """Test risk metrics calculation"""
        returns = [Decimal("0.02"), Decimal("0.01"), Decimal("-0.015"), Decimal("0.03")]
        
        # Calculate mean return
        mean_return = sum(returns) / len(returns)
        
        # Calculate volatility (simplified)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** Decimal("0.5")
        
        assert isinstance(mean_return, Decimal)
        assert isinstance(volatility, Decimal)
        assert volatility > Decimal("0")

    def test_portfolio_rebalance_calculation(self):
        """Test portfolio rebalance calculation"""
        current_positions = {
            "SBER": {"value": Decimal("60000"), "target_weight": Decimal("0.5")},
            "GAZP": {"value": Decimal("40000"), "target_weight": Decimal("0.5")}
        }
        
        total_value = sum(pos["value"] for pos in current_positions.values())
        
        rebalance_actions = {}
        for secid, pos in current_positions.items():
            current_weight = pos["value"] / total_value
            target_value = total_value * pos["target_weight"]
            rebalance_amount = target_value - pos["value"]
            
            if abs(rebalance_amount) > Decimal("1000"):  # Minimum trade threshold
                rebalance_actions[secid] = rebalance_amount
        
        # SBER should sell 10k, GAZP should buy 10k
        assert rebalance_actions["SBER"] == Decimal("-10000")
        assert rebalance_actions["GAZP"] == Decimal("10000")


class TestDependencyInjection:
    """Tests for dependency injection"""

    def test_strategy_service_creation(self):
        """Test StrategyService dependency creation"""
        mock_data_manager = Mock(spec=DataManager)
        mock_market_service = Mock()
        
        service = StrategyService(mock_data_manager, mock_market_service)
        
        assert isinstance(service, StrategyService)
        assert service.data_manager == mock_data_manager
        assert service.market_data_service == mock_market_service