"""Comprehensive tests for marketdata module"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
import aiohttp

from app.modules.marketdata.api import router, get_marketdata_service
from app.modules.marketdata.service import MarketDataService, MOEXAdapter
from app.modules.marketdata.schemas import Security, SecurityCreate, Quote, QuoteCreate
from app.modules.marketdata.models import Security as SecurityModel, Quote as QuoteModel
from app.storage import DataManager


class TestMarketDataAPI:
    """Tests for MarketData API endpoints"""

    @pytest.fixture
    def mock_service(self):
        service = AsyncMock(spec=MarketDataService)
        service.close = AsyncMock()
        return service

    @pytest.fixture
    def client(self, mock_service):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api/marketdata")
        
        # Override dependency
        def get_mock_service():
            return mock_service
        
        app.dependency_overrides[get_marketdata_service] = get_mock_service
        return TestClient(app)

    def test_get_securities_success(self, client, mock_service):
        """Test successful securities retrieval"""
        mock_securities = [
            Security(
                id=1,
                secid="SBER",
                name="Сбербанк",
                isin="RU0009029540",
                is_active="Y",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        mock_service.get_securities.return_value = mock_securities
        
        response = client.get("/api/marketdata/securities?skip=0&limit=10")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_service.get_securities.assert_called_once_with(skip=0, limit=10)
        mock_service.close.assert_called_once()

    def test_sync_securities_success(self, client, mock_service):
        """Test successful securities sync"""
        mock_service.sync_securities_from_moex.return_value = 150
        
        response = client.post("/api/marketdata/securities/sync?engine=stock&market=shares")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Synchronized 150 securities from MOEX"}
        mock_service.sync_securities_from_moex.assert_called_once_with(
            engine="stock", market="shares"
        )
        mock_service.close.assert_called_once()

    def test_sync_securities_error(self, client, mock_service):
        """Test securities sync error handling"""
        mock_service.sync_securities_from_moex.side_effect = Exception("MOEX API error")
        
        response = client.post("/api/marketdata/securities/sync")
        
        assert response.status_code == 500
        assert "MOEX API error" in response.json()["detail"]
        mock_service.close.assert_called_once()

    def test_get_security_info_success(self, client, mock_service):
        """Test successful security info retrieval"""
        mock_info = {"secid": "SBER", "name": "Сбербанк", "price": Decimal("250.50")}
        mock_service.get_security_info.return_value = mock_info
        
        response = client.get("/api/marketdata/securities/SBER/info")
        
        assert response.status_code == 200
        assert response.json()["secid"] == "SBER"
        mock_service.get_security_info.assert_called_once_with("SBER")
        mock_service.close.assert_called_once()

    def test_get_security_info_not_found(self, client, mock_service):
        """Test security info not found"""
        mock_service.get_security_info.return_value = None
        
        response = client.get("/api/marketdata/securities/INVALID/info")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Security not found"
        mock_service.close.assert_called_once()

    def test_sync_quotes_valid_dates(self, client, mock_service):
        """Test quotes sync with valid dates"""
        mock_service.sync_quotes_for_security.return_value = 30
        
        response = client.post(
            "/api/marketdata/quotes/SBER/sync?from_date=2024-01-01&to_date=2024-01-31"
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Synchronized 30 quotes for SBER"}
        mock_service.close.assert_called_once()

    def test_sync_quotes_invalid_date_format(self, client, mock_service):
        """Test quotes sync with invalid date format"""
        response = client.post("/api/marketdata/quotes/SBER/sync?from_date=invalid-date")
        
        assert response.status_code == 400
        assert "Invalid from_date format" in response.json()["detail"]
        mock_service.close.assert_called_once()

    def test_update_current_prices(self, client, mock_service):
        """Test current prices update"""
        mock_service.update_current_prices.return_value = 5
        
        response = client.post(
            "/api/marketdata/quotes/current/update",
            json=["SBER", "GAZP", "LKOH"]
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Updated current prices for 5 securities"}
        mock_service.close.assert_called_once()

    def test_get_current_quotes(self, client, mock_service):
        """Test current quotes retrieval"""
        mock_quotes = [{"secid": "SBER", "price": 250.50}]
        mock_service.get_current_quotes.return_value = mock_quotes
        
        response = client.get("/api/marketdata/quotes/current?securities=SBER&securities=GAZP")
        
        assert response.status_code == 200
        assert response.json() == mock_quotes
        mock_service.close.assert_called_once()

    def test_get_latest_quote_success(self, client, mock_service):
        """Test latest quote retrieval"""
        mock_quote = Quote(
            id=1,
            secid="SBER",
            timestamp=datetime.now(),
            close_price=Decimal("250.50")
        )
        mock_service.get_latest_quote.return_value = mock_quote
        
        response = client.get("/api/marketdata/quotes/SBER/latest")
        
        assert response.status_code == 200
        assert response.json()["secid"] == "SBER"
        mock_service.close.assert_called_once()

    def test_get_latest_quote_not_found(self, client, mock_service):
        """Test latest quote not found"""
        mock_service.get_latest_quote.return_value = None
        
        response = client.get("/api/marketdata/quotes/INVALID/latest")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Quote not found"
        mock_service.close.assert_called_once()

    def test_get_quotes_history(self, client, mock_service):
        """Test quotes history retrieval"""
        mock_quotes = [
            Quote(id=1, secid="SBER", timestamp=datetime.now(), close_price=Decimal("250.50")),
            Quote(id=2, secid="SBER", timestamp=datetime.now(), close_price=Decimal("251.00"))
        ]
        mock_service.get_quotes_history.return_value = mock_quotes
        
        response = client.get("/api/marketdata/quotes/SBER/history")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_service.close.assert_called_once()


class TestMOEXAdapter:
    """Tests for MOEX API adapter"""

    @pytest.fixture
    def adapter(self):
        return MOEXAdapter()

    @pytest.mark.asyncio
    async def test_get_session_creates_new(self, adapter):
        """Test session creation"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session.closed = False
            mock_session_class.return_value = mock_session
            
            session = await adapter._get_session()
            
            assert session == mock_session
            mock_session_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self, adapter):
        """Test session reuse"""
        mock_session = Mock()
        mock_session.closed = False
        adapter.session = mock_session
        
        session = await adapter._get_session()
        
        assert session == mock_session

    @pytest.mark.asyncio
    async def test_get_securities_success(self, adapter):
        """Test successful securities retrieval from MOEX"""
        mock_session = AsyncMock()
        mock_securities_data = [
            {
                "SECID": "SBER",
                "SHORTNAME": "Сбербанк",
                "ISIN": "RU0009029540",
                "BOARDID": "TQBR",
                "DECIMALS": 2,
                "LOTSIZE": 10
            }
        ]
        
        with patch.object(adapter, '_get_session', return_value=mock_session), \
             patch('aiomoex.get_board_securities', return_value=mock_securities_data):
            
            result = await adapter.get_securities()
            
            assert len(result) == 1
            assert result[0]["secid"] == "SBER"
            assert result[0]["shortname"] == "Сбербанк"

    @pytest.mark.asyncio
    async def test_get_securities_handles_missing_fields(self, adapter):
        """Test securities retrieval with missing fields"""
        mock_session = AsyncMock()
        mock_securities_data = [{"SECID": "TEST"}]  # Missing other fields
        
        with patch.object(adapter, '_get_session', return_value=mock_session), \
             patch('aiomoex.get_board_securities', return_value=mock_securities_data):
            
            result = await adapter.get_securities()
            
            assert len(result) == 1
            assert result[0]["secid"] == "TEST"
            assert result[0]["shortname"] == ""
            assert result[0]["decimals"] == 0

    @pytest.mark.asyncio
    async def test_close_session(self, adapter):
        """Test session closing"""
        mock_session = Mock()
        mock_session.close = AsyncMock()
        adapter.session = mock_session
        
        await adapter.close()
        
        mock_session.close.assert_called_once()


class TestMarketDataService:
    """Tests for MarketData service layer"""

    @pytest.fixture
    def mock_data_manager(self):
        return AsyncMock(spec=DataManager)

    @pytest.fixture
    def service(self, mock_data_manager):
        return MarketDataService(mock_data_manager)

    @pytest.mark.asyncio
    async def test_get_securities(self, service, mock_data_manager):
        """Test securities retrieval from database"""
        mock_securities = [
            SecurityModel(
                id=1,
                secid="SBER",
                name="Сбербанк",
                is_active="Y",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        mock_data_manager.get_securities.return_value = mock_securities
        
        result = await service.get_securities(skip=0, limit=10)
        
        assert len(result) == 1
        assert result[0].secid == "SBER"
        mock_data_manager.get_securities.assert_called_once_with(skip=0, limit=10)

    @pytest.mark.asyncio
    async def test_sync_securities_from_moex(self, service, mock_data_manager):
        """Test securities sync from MOEX"""
        mock_moex_data = [
            {
                "secid": "SBER",
                "shortname": "Сбербанк",
                "isin": "RU0009029540",
                "boardid": "TQBR",
                "decimals": 2,
                "lotsize": 10
            }
        ]
        
        with patch.object(service.moex_adapter, 'get_securities', return_value=mock_moex_data):
            mock_data_manager.save_securities.return_value = 1
            
            count = await service.sync_securities_from_moex()
            
            assert count == 1
            mock_data_manager.save_securities.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_security_info(self, service, mock_data_manager):
        """Test security info retrieval"""
        mock_info = {"secid": "SBER", "name": "Сбербанк"}
        
        with patch.object(service.moex_adapter, 'get_security_info', return_value=mock_info):
            result = await service.get_security_info("SBER")
            
            assert result == mock_info

    @pytest.mark.asyncio
    async def test_get_latest_quote(self, service, mock_data_manager):
        """Test latest quote retrieval"""
        mock_quote = QuoteModel(
            id=1,
            secid="SBER",
            timestamp=datetime.now(),
            close_price=Decimal("250.50")
        )
        mock_data_manager.get_latest_quote.return_value = mock_quote
        
        result = await service.get_latest_quote("SBER")
        
        assert result.secid == "SBER"
        assert result.close_price == Decimal("250.50")
        mock_data_manager.get_latest_quote.assert_called_once_with("SBER")

    @pytest.mark.asyncio
    async def test_close_service(self, service):
        """Test service cleanup"""
        service.moex_adapter.close = AsyncMock()
        service.data_manager.close = AsyncMock()
        
        await service.close()
        
        service.moex_adapter.close.assert_called_once()
        service.data_manager.close.assert_called_once()


class TestMarketDataSchemas:
    """Tests for MarketData Pydantic schemas"""

    def test_security_base_schema(self):
        """Test SecurityBase schema validation"""
        data = {
            "secid": "SBER",
            "name": "Сбербанк",
            "isin": "RU0009029540"
        }
        
        security = SecurityCreate(**data)
        
        assert security.secid == "SBER"
        assert security.name == "Сбербанк"
        assert security.isin == "RU0009029540"

    def test_security_schema_optional_fields(self):
        """Test Security schema with optional fields"""
        data = {
            "id": 1,
            "secid": "SBER",
            "name": "Сбербанк",
            "is_active": "Y",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        security = Security(**data)
        
        assert security.id == 1
        assert security.secid == "SBER"
        assert security.isin is None

    def test_quote_base_schema(self):
        """Test QuoteBase schema validation"""
        data = {
            "secid": "SBER",
            "timestamp": datetime.now(),
            "close_price": Decimal("250.50"),
            "volume": Decimal("1000000")
        }
        
        quote = QuoteCreate(**data)
        
        assert quote.secid == "SBER"
        assert quote.close_price == Decimal("250.50")

    def test_quote_schema_optional_fields(self):
        """Test Quote schema with optional fields"""
        data = {
            "id": 1,
            "secid": "SBER",
            "timestamp": datetime.now()
        }
        
        quote = Quote(**data)
        
        assert quote.id == 1
        assert quote.open_price is None
        assert quote.volume is None


class TestDependencyInjection:
    """Tests for dependency injection"""

    def test_get_marketdata_service_dependency(self):
        """Test MarketDataService dependency creation"""
        mock_data_manager = Mock(spec=DataManager)
        
        service = get_marketdata_service(mock_data_manager)
        
        assert isinstance(service, MarketDataService)
        assert service.data_manager == mock_data_manager