"""Comprehensive tests for portfolio module"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.modules.portfolio.api import router, get_portfolio_service
from app.modules.portfolio.service import PortfolioService
from app.modules.portfolio.schemas import (
    Portfolio,
    PortfolioCreate,
    Position,
    PositionCreate,
    PortfolioSummary
)
from app.modules.portfolio.models import Portfolio as PortfolioModel, Position as PositionModel
from app.storage import DataManager


class TestPortfolioAPI:
    """Tests for Portfolio API endpoints"""

    @pytest.fixture
    def mock_service(self):
        service = AsyncMock(spec=PortfolioService)
        return service

    @pytest.fixture
    def client(self, mock_service):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api/portfolio")
        
        # Override dependency
        def get_mock_service():
            return mock_service
        
        app.dependency_overrides[get_portfolio_service] = get_mock_service
        return TestClient(app)

    def test_create_portfolio_success(self, client, mock_service):
        """Test successful portfolio creation"""
        portfolio_data = {
            "name": "Test Portfolio",
            "description": "Test portfolio description",
            "base_currency": "RUB"
        }
        
        mock_portfolio = Portfolio(
            id=1,
            name="Test Portfolio",
            description="Test portfolio description",
            base_currency="RUB",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_service.create_portfolio.return_value = mock_portfolio
        
        response = client.post("/api/portfolio/", json=portfolio_data)
        
        assert response.status_code == 200
        assert response.json()["name"] == "Test Portfolio"
        mock_service.create_portfolio.assert_called_once()

    def test_get_portfolios_success(self, client, mock_service):
        """Test successful portfolios retrieval"""
        mock_portfolios = [
            Portfolio(
                id=1,
                name="Portfolio 1",
                base_currency="RUB",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Portfolio(
                id=2,
                name="Portfolio 2",
                base_currency="USD",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        mock_service.get_portfolios.return_value = mock_portfolios
        
        response = client.get("/api/portfolio/?skip=0&limit=10")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_service.get_portfolios.assert_called_once_with(skip=0, limit=10)

    def test_get_portfolio_success(self, client, mock_service):
        """Test successful portfolio retrieval by ID"""
        mock_portfolio = Portfolio(
            id=1,
            name="Test Portfolio",
            base_currency="RUB",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_service.get_portfolio.return_value = mock_portfolio
        
        response = client.get("/api/portfolio/1")
        
        assert response.status_code == 200
        assert response.json()["id"] == 1
        mock_service.get_portfolio.assert_called_once_with(1)

    def test_get_portfolio_not_found(self, client, mock_service):
        """Test portfolio not found"""
        mock_service.get_portfolio.return_value = None
        
        response = client.get("/api/portfolio/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Portfolio not found"

    def test_get_portfolio_summary_success(self, client, mock_service):
        """Test successful portfolio summary retrieval"""
        mock_summary = PortfolioSummary(
            portfolio_id=1,
            total_value=Decimal("1000000.00"),
            total_cost=Decimal("950000.00"),
            total_pnl=Decimal("50000.00"),
            positions_count=10,
            currency="RUB"
        )
        mock_service.get_portfolio_summary.return_value = mock_summary
        
        response = client.get("/api/portfolio/1/summary")
        
        assert response.status_code == 200
        assert response.json()["total_value"] == "1000000.00"
        mock_service.get_portfolio_summary.assert_called_once_with(1)

    def test_get_portfolio_summary_not_found(self, client, mock_service):
        """Test portfolio summary not found"""
        mock_service.get_portfolio_summary.return_value = None
        
        response = client.get("/api/portfolio/999/summary")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Portfolio not found"

    def test_get_portfolio_positions_success(self, client, mock_service):
        """Test successful portfolio positions retrieval"""
        mock_positions = [
            Position(
                id=1,
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                avg_price=Decimal("250.50"),
                current_price=Decimal("255.00"),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        mock_service.get_portfolio_positions.return_value = mock_positions
        
        response = client.get("/api/portfolio/1/positions")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_service.get_portfolio_positions.assert_called_once_with(1)

    def test_create_position_success(self, client, mock_service):
        """Test successful position creation"""
        position_data = {
            "portfolio_id": 1,
            "secid": "SBER",
            "quantity": "100",
            "price": "250.50"
        }
        
        mock_position = Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=Decimal("100"),
            avg_price=Decimal("250.50"),
            current_price=Decimal("250.50"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_service.create_position.return_value = mock_position
        
        response = client.post("/api/portfolio/positions", json=position_data)
        
        assert response.status_code == 200
        assert response.json()["secid"] == "SBER"
        mock_service.create_position.assert_called_once()


class TestPortfolioService:
    """Tests for Portfolio service layer"""

    @pytest.fixture
    def mock_data_manager(self):
        return AsyncMock(spec=DataManager)

    @pytest.fixture
    def service(self, mock_data_manager):
        return PortfolioService(mock_data_manager)

    @pytest.mark.asyncio
    async def test_create_portfolio(self, service, mock_data_manager):
        """Test portfolio creation"""
        portfolio_data = PortfolioCreate(
            name="Test Portfolio",
            description="Test description",
            base_currency="RUB"
        )
        
        mock_portfolio = PortfolioModel(
            id=1,
            name="Test Portfolio",
            description="Test description",
            base_currency="RUB",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_data_manager.create_portfolio.return_value = mock_portfolio
        
        result = await service.create_portfolio(portfolio_data)
        
        assert result.name == "Test Portfolio"
        mock_data_manager.create_portfolio.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_portfolios(self, service, mock_data_manager):
        """Test portfolios retrieval"""
        mock_portfolios = [
            PortfolioModel(
                id=1,
                name="Portfolio 1",
                base_currency="RUB",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        mock_data_manager.get_portfolios.return_value = mock_portfolios
        
        result = await service.get_portfolios(skip=0, limit=10)
        
        assert len(result) == 1
        assert result[0].name == "Portfolio 1"
        mock_data_manager.get_portfolios.assert_called_once_with(skip=0, limit=10)

    @pytest.mark.asyncio
    async def test_get_portfolio(self, service, mock_data_manager):
        """Test single portfolio retrieval"""
        mock_portfolio = PortfolioModel(
            id=1,
            name="Test Portfolio",
            base_currency="RUB",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_data_manager.get_portfolio.return_value = mock_portfolio
        
        result = await service.get_portfolio(1)
        
        assert result.name == "Test Portfolio"
        mock_data_manager.get_portfolio.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_portfolio_summary(self, service, mock_data_manager):
        """Test portfolio summary calculation"""
        mock_summary_data = {
            "total_value": Decimal("1000000"),
            "total_cost": Decimal("950000"),
            "positions_count": 10
        }
        mock_data_manager.get_portfolio_summary.return_value = mock_summary_data
        
        result = await service.get_portfolio_summary(1)
        
        assert result.total_value == Decimal("1000000")
        assert result.total_pnl == Decimal("50000")  # total_value - total_cost
        mock_data_manager.get_portfolio_summary.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_portfolio_positions(self, service, mock_data_manager):
        """Test portfolio positions retrieval"""
        mock_positions = [
            PositionModel(
                id=1,
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                avg_price=Decimal("250.50"),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        mock_data_manager.get_portfolio_positions.return_value = mock_positions
        
        result = await service.get_portfolio_positions(1)
        
        assert len(result) == 1
        assert result[0].secid == "SBER"
        mock_data_manager.get_portfolio_positions.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_create_position(self, service, mock_data_manager):
        """Test position creation"""
        position_data = PositionCreate(
            portfolio_id=1,
            secid="SBER",
            quantity=Decimal("100"),
            price=Decimal("250.50")
        )
        
        mock_position = PositionModel(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=Decimal("100"),
            avg_price=Decimal("250.50"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_data_manager.create_position.return_value = mock_position
        
        result = await service.create_position(position_data)
        
        assert result.secid == "SBER"
        mock_data_manager.create_position.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_position_pnl(self, service):
        """Test position P&L calculation"""
        avg_price = Decimal("250.00")
        current_price = Decimal("275.00")
        quantity = Decimal("100")
        
        pnl = service._calculate_pnl(avg_price, current_price, quantity)
        
        assert pnl == Decimal("2500.00")  # (275 - 250) * 100

    @pytest.mark.asyncio
    async def test_calculate_position_pnl_negative(self, service):
        """Test negative position P&L calculation"""
        avg_price = Decimal("250.00")
        current_price = Decimal("225.00")
        quantity = Decimal("100")
        
        pnl = service._calculate_pnl(avg_price, current_price, quantity)
        
        assert pnl == Decimal("-2500.00")  # (225 - 250) * 100


class TestPortfolioSchemas:
    """Tests for Portfolio Pydantic schemas"""

    def test_portfolio_create_schema(self):
        """Test PortfolioCreate schema validation"""
        data = {
            "name": "Test Portfolio",
            "description": "Test description",
            "base_currency": "RUB"
        }
        
        portfolio = PortfolioCreate(**data)
        
        assert portfolio.name == "Test Portfolio"
        assert portfolio.base_currency == "RUB"

    def test_portfolio_schema_with_dates(self):
        """Test Portfolio schema with timestamps"""
        now = datetime.now()
        data = {
            "id": 1,
            "name": "Test Portfolio",
            "base_currency": "RUB",
            "created_at": now,
            "updated_at": now
        }
        
        portfolio = Portfolio(**data)
        
        assert portfolio.id == 1
        assert portfolio.created_at == now

    def test_position_create_schema(self):
        """Test PositionCreate schema validation"""
        data = {
            "portfolio_id": 1,
            "secid": "SBER",
            "quantity": Decimal("100"),
            "price": Decimal("250.50")
        }
        
        position = PositionCreate(**data)
        
        assert position.portfolio_id == 1
        assert position.secid == "SBER"
        assert position.quantity == Decimal("100")

    def test_position_schema_optional_fields(self):
        """Test Position schema with optional fields"""
        data = {
            "id": 1,
            "portfolio_id": 1,
            "secid": "SBER",
            "quantity": Decimal("100"),
            "avg_price": Decimal("250.50"),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        position = Position(**data)
        
        assert position.id == 1
        assert position.current_price is None
        assert position.market_value is None

    def test_portfolio_summary_schema(self):
        """Test PortfolioSummary schema validation"""
        data = {
            "portfolio_id": 1,
            "total_value": Decimal("1000000.00"),
            "total_cost": Decimal("950000.00"),
            "total_pnl": Decimal("50000.00"),
            "positions_count": 10,
            "currency": "RUB"
        }
        
        summary = PortfolioSummary(**data)
        
        assert summary.portfolio_id == 1
        assert summary.total_value == Decimal("1000000.00")
        assert summary.positions_count == 10

    def test_portfolio_summary_pnl_percentage(self):
        """Test portfolio summary P&L percentage calculation"""
        data = {
            "portfolio_id": 1,
            "total_value": Decimal("1050000.00"),
            "total_cost": Decimal("1000000.00"),
            "total_pnl": Decimal("50000.00"),
            "positions_count": 10,
            "currency": "RUB"
        }
        
        summary = PortfolioSummary(**data)
        
        # Calculate P&L percentage: (pnl / cost) * 100
        pnl_percentage = (summary.total_pnl / summary.total_cost) * Decimal("100")
        assert pnl_percentage == Decimal("5.00")


class TestDependencyInjection:
    """Tests for dependency injection"""

    def test_get_portfolio_service_dependency(self):
        """Test PortfolioService dependency creation"""
        mock_data_manager = Mock(spec=DataManager)
        
        service = get_portfolio_service(mock_data_manager)
        
        assert isinstance(service, PortfolioService)
        assert service.data_manager == mock_data_manager


class TestPortfolioBusinessLogic:
    """Tests for portfolio business logic"""

    @pytest.fixture
    def service(self):
        return PortfolioService(AsyncMock(spec=DataManager))

    def test_portfolio_validation_empty_name(self):
        """Test portfolio validation with empty name"""
        with pytest.raises(ValueError):
            PortfolioCreate(name="", base_currency="RUB")

    def test_position_validation_negative_quantity(self):
        """Test position validation with negative quantity"""
        with pytest.raises(ValueError):
            PositionCreate(
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("-100"),
                price=Decimal("250.50")
            )

    def test_position_validation_zero_price(self):
        """Test position validation with zero price"""
        with pytest.raises(ValueError):
            PositionCreate(
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                price=Decimal("0")
            )

    def test_currency_code_validation(self):
        """Test currency code validation"""
        valid_currencies = ["RUB", "USD", "EUR"]
        
        for currency in valid_currencies:
            portfolio = PortfolioCreate(
                name="Test Portfolio",
                base_currency=currency
            )
            assert portfolio.base_currency == currency

    def test_secid_format_validation(self):
        """Test security ID format validation"""
        valid_secids = ["SBER", "GAZP", "LKOH", "YNDX"]
        
        for secid in valid_secids:
            position = PositionCreate(
                portfolio_id=1,
                secid=secid,
                quantity=Decimal("100"),
                price=Decimal("250.50")
            )
            assert position.secid == secid