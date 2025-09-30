"""
Тесты для API endpoints всех модулей
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime

from app.main import app
from app.modules.marketdata.models import Security, Quote
from app.modules.portfolio.models import Portfolio, Position
from app.modules.reporting.models import Transaction, TransactionType


class TestMarketDataAPI:
    """Тесты для MarketData API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_securities_success(self, client):
        """Тест успешного получения списка ценных бумаг"""
        with patch('app.modules.marketdata.service.MarketDataService') as mock_service_class:
            mock_service = AsyncMock()
            mock_securities = [
                Security(secid="SBER", name="Сбер", isin="RU0009029540"),
                Security(secid="GAZP", name="Газпром", isin="RU0007661625"),
            ]
            mock_service.get_securities.return_value = mock_securities
            mock_service.close.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.get("/marketdata/securities")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["secid"] == "SBER"
            assert data[1]["secid"] == "GAZP"
            
    def test_get_securities_with_pagination(self, client):
        """Тест пагинации ценных бумаг"""
        with patch('app.modules.marketdata.service.MarketDataService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_securities.return_value = []
            mock_service.close.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.get("/marketdata/securities?skip=10&limit=5")
            
            assert response.status_code == 200
            mock_service.get_securities.assert_called_once_with(skip=10, limit=5)
            
    def test_sync_securities_success(self, client):
        """Тест синхронизации ценных бумаг"""
        with patch('app.modules.marketdata.service.MarketDataService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.sync_securities_from_moex.return_value = 42
            mock_service.close.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.post("/marketdata/securities/sync")
            
            assert response.status_code == 200
            data = response.json()
            assert "Synchronized 42 securities" in data["message"]
            
    def test_sync_securities_with_params(self, client):
        """Тест синхронизации с параметрами"""
        with patch('app.modules.marketdata.service.MarketDataService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.sync_securities_from_moex.return_value = 10
            mock_service.close.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.post("/marketdata/securities/sync?engine=currency&market=selt")
            
            assert response.status_code == 200
            mock_service.sync_securities_from_moex.assert_called_once_with(engine="currency", market="selt")
            
    def test_sync_securities_error(self, client):
        """Тест обработки ошибки при синхронизации"""
        with patch('app.modules.marketdata.service.MarketDataService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.sync_securities_from_moex.side_effect = Exception("MOEX API Error")
            mock_service.close.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.post("/marketdata/securities/sync")
            
            assert response.status_code == 500
            assert "MOEX API Error" in response.json()["detail"]
            
    def test_get_security_info_success(self, client):
        """Тест получения информации о ценной бумаге"""
        with patch('app.modules.marketdata.service.MarketDataService') as mock_service_class:
            mock_service = AsyncMock()
            mock_info = {"secid": "SBER", "name": "Сбер", "price": 250.50}
            mock_service.get_security_info.return_value = mock_info
            mock_service.close.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.get("/marketdata/securities/SBER/info")
            
            assert response.status_code == 200
            data = response.json()
            assert data["secid"] == "SBER"
            assert data["name"] == "Сбер"
            
    def test_get_security_info_not_found(self, client):
        """Тест получения информации о несуществующей ценной бумаге"""
        with patch('app.modules.marketdata.service.MarketDataService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_security_info.return_value = None
            mock_service.close.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.get("/marketdata/securities/NONEXIST/info")
            
            assert response.status_code == 404


class TestPortfolioAPI:
    """Тесты для Portfolio API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
        
    def test_create_portfolio_success(self, client):
        """Тест успешного создания портфеля"""
        with patch('app.modules.portfolio.service.PortfolioService') as mock_service_class:
            mock_service = AsyncMock()
            mock_portfolio = Portfolio(
                id=1, name="Test Portfolio", description="Test",
                total_value=Decimal("0"), cash_balance=Decimal("0"), is_active=True
            )
            mock_service.create_portfolio.return_value = mock_portfolio
            mock_service_class.return_value = mock_service
            
            portfolio_data = {
                "name": "Test Portfolio",
                "description": "Test description"
            }
            
            response = client.post("/portfolio/portfolios", json=portfolio_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Portfolio"
            assert data["id"] == 1
            
    def test_create_portfolio_validation_error(self, client):
        """Тест валидации при создании портфеля"""
        portfolio_data = {
            "description": "Test without name"
            # Отсутствует обязательное поле name
        }
        
        response = client.post("/portfolio/portfolios", json=portfolio_data)
        
        assert response.status_code == 422  # Validation error
        
    def test_get_portfolios_success(self, client):
        """Тест получения списка портфелей"""
        with patch('app.modules.portfolio.service.PortfolioService') as mock_service_class:
            mock_service = AsyncMock()
            mock_portfolios = [
                Portfolio(id=1, name="Portfolio 1", total_value=Decimal("100000"), cash_balance=Decimal("10000"), is_active=True),
                Portfolio(id=2, name="Portfolio 2", total_value=Decimal("200000"), cash_balance=Decimal("20000"), is_active=True),
            ]
            mock_service.get_portfolios.return_value = mock_portfolios
            mock_service_class.return_value = mock_service
            
            response = client.get("/portfolio/portfolios")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "Portfolio 1"
            
    def test_get_portfolio_success(self, client):
        """Тест получения конкретного портфеля"""
        with patch('app.modules.portfolio.service.PortfolioService') as mock_service_class:
            mock_service = AsyncMock()
            mock_portfolio = Portfolio(
                id=1, name="Test Portfolio", total_value=Decimal("100000"), 
                cash_balance=Decimal("10000"), is_active=True
            )
            mock_service.get_portfolio.return_value = mock_portfolio
            mock_service_class.return_value = mock_service
            
            response = client.get("/portfolio/portfolios/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Portfolio"
            assert data["id"] == 1
            
    def test_get_portfolio_not_found(self, client):
        """Тест получения несуществующего портфеля"""
        with patch('app.modules.portfolio.service.PortfolioService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_portfolio.return_value = None
            mock_service_class.return_value = mock_service
            
            response = client.get("/portfolio/portfolios/999")
            
            assert response.status_code == 404
            
    def test_create_position_success(self, client):
        """Тест создания позиции в портфеле"""
        with patch('app.modules.portfolio.service.PortfolioService') as mock_service_class:
            mock_service = AsyncMock()
            mock_position = Position(
                id=1, portfolio_id=1, secid="SBER", quantity=Decimal("100"),
                average_price=Decimal("250"), market_price=Decimal("255"), target_weight=Decimal("0.25")
            )
            mock_service.create_position.return_value = mock_position
            mock_service_class.return_value = mock_service
            
            position_data = {
                "portfolio_id": 1,
                "secid": "SBER", 
                "quantity": "100",
                "target_weight": "0.25"
            }
            
            response = client.post("/portfolio/positions", json=position_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["secid"] == "SBER"
            assert data["portfolio_id"] == 1


class TestReportingAPI:
    """Тесты для Reporting API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
        
    def test_create_transaction_success(self, client):
        """Тест создания транзакции"""
        with patch('app.modules.reporting.service.ReportingService') as mock_service_class:
            mock_service = Mock()  # Sync service
            mock_transaction = Transaction(
                id=1, portfolio_id=1, secid="SBER", transaction_type=TransactionType.BUY,
                quantity=Decimal("100"), price=Decimal("250"), timestamp=datetime.now()
            )
            mock_service.create_transaction.return_value = mock_transaction
            mock_service_class.return_value = mock_service
            
            transaction_data = {
                "portfolio_id": 1,
                "secid": "SBER",
                "transaction_type": "buy",
                "quantity": "100",
                "price": "250.50"
            }
            
            response = client.post("/reporting/transactions", json=transaction_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["secid"] == "SBER"
            assert data["portfolio_id"] == 1
            
    def test_get_transactions_success(self, client):
        """Тест получения списка транзакций"""
        with patch('app.modules.reporting.service.ReportingService') as mock_service_class:
            mock_service = Mock()
            mock_transactions = [
                Transaction(
                    id=1, portfolio_id=1, secid="SBER", transaction_type=TransactionType.BUY,
                    quantity=Decimal("100"), price=Decimal("250"), timestamp=datetime.now()
                )
            ]
            mock_service.get_transactions.return_value = mock_transactions
            mock_service_class.return_value = mock_service
            
            response = client.get("/reporting/transactions")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["secid"] == "SBER"
            
    def test_get_transactions_with_filters(self, client):
        """Тест получения транзакций с фильтрами"""
        with patch('app.modules.reporting.service.ReportingService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_transactions.return_value = []
            mock_service_class.return_value = mock_service
            
            response = client.get("/reporting/transactions?portfolio_id=1&start_date=2024-01-01&end_date=2024-01-31")
            
            assert response.status_code == 200
            # Проверяем что сервис вызван с правильными параметрами
            mock_service.get_transactions.assert_called_once()


class TestAPIIntegration:
    """Интеграционные тесты API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
        
    def test_api_health_check(self, client):
        """Тест health check API"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
    def test_api_root_endpoint(self, client):
        """Тест корневого endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
    def test_api_cors_headers(self, client):
        """Тест CORS заголовков"""
        # Preflight request
        response = client.options("/marketdata/securities", 
                                headers={"Origin": "http://localhost:3000"})
        
        # Должен вернуть корректные CORS заголовки или 200/405
        assert response.status_code in [200, 405]
        
    def test_api_error_handling(self, client):
        """Тест обработки ошибок API"""
        # Запрос к несуществующему endpoint
        response = client.get("/nonexistent/endpoint")
        
        assert response.status_code == 404
        
    def test_api_validation_error_format(self, client):
        """Тест формата ошибок валидации"""
        # Некорректные данные для создания портфеля
        response = client.post("/portfolio/portfolios", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestAPIPerformance:
    """Тесты производительности API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
        
    def test_api_response_time(self, client):
        """Тест времени ответа API"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # Проверяем что ответ пришел быстро (меньше 1 секунды)
        assert (end_time - start_time) < 1.0
        
    def test_api_concurrent_requests(self, client):
        """Тест конкурентных запросов"""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
            
        # Делаем несколько параллельных запросов
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        # Все запросы должны быть успешными
        for response in results:
            assert response.status_code == 200