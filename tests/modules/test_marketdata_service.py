import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from decimal import Decimal

from app.storage import DataManager
from app.modules.marketdata.service import MarketDataService
from app.modules.marketdata.schemas import SecurityCreate
from app.modules.marketdata.models import Security, Quote


class TestMarketDataServiceIntegration:
    "Integration tests for MarketDataService with DataManager"

    @pytest.fixture
    def data_manager(self):
        "Create a fresh DataManager instance for each test"
        return DataManager()

    @pytest.fixture
    def marketdata_service(self, data_manager):
        "Create MarketDataService with injected DataManager"
        return MarketDataService(data_manager)

    @pytest.mark.asyncio
    async def test_create_security(self, marketdata_service):
        "Test security creation without global variables"
        security_data = SecurityCreate(
            secid="SBER", name="Сбербанк", isin="RU0009029540"
        )

        security = await marketdata_service.create_security(security_data)

        assert security.secid == "SBER"
        assert security.name == "Сбербанк"
        assert security.isin == "RU0009029540"

    @pytest.mark.asyncio
    async def test_get_securities(self, marketdata_service):
        "Test retrieving securities"
        security_data1 = SecurityCreate(secid="SBER", name="Сбербанк")
        security_data2 = SecurityCreate(secid="GAZP", name="Газпром")

        await marketdata_service.create_security(security_data1)
        await marketdata_service.create_security(security_data2)

        securities = await marketdata_service.get_securities()

        assert len(securities) == 2
        secids = [sec.secid for sec in securities]
        assert "SBER" in secids
        assert "GAZP" in secids

    @pytest.mark.asyncio
    async def test_get_securities_pagination(self, marketdata_service):
        "Test securities pagination"
        # Create multiple securities
        for i in range(5):
            security_data = SecurityCreate(secid=f"SEC{i}", name=f"Security {i}")
            await marketdata_service.create_security(security_data)

        # Test pagination
        securities_page1 = await marketdata_service.get_securities(skip=0, limit=2)
        securities_page2 = await marketdata_service.get_securities(skip=2, limit=2)

        assert len(securities_page1) == 2
        assert len(securities_page2) == 2

        # Ensure different securities on different pages
        page1_secids = {sec.secid for sec in securities_page1}
        page2_secids = {sec.secid for sec in securities_page2}
        assert page1_secids.isdisjoint(page2_secids)

    @pytest.mark.asyncio
    async def test_get_latest_quote_nonexistent(self, marketdata_service):
        "Test getting latest quote for non-existent security"
        quote = await marketdata_service.get_latest_quote("NONEXISTENT")
        assert quote is None

    @pytest.mark.asyncio
    async def test_sync_securities_from_moex(self, marketdata_service):
        "Test syncing securities from MOEX API"
        # Mock the MOEX adapter response in correct dict format
        mock_securities_data = [
            {"secid": "SBER", "shortname": "Сбербанк", "isin": "RU0009029540"},
            {"secid": "GAZP", "shortname": "Газпром", "isin": "RU0007661625"},
            {"secid": "LKOH", "shortname": "ЛУКОЙЛ", "isin": "RU0009024277"},
        ]

        with patch.object(
            marketdata_service.moex_adapter, "get_securities", new_callable=AsyncMock
        ) as mock_get_securities:
            mock_get_securities.return_value = mock_securities_data

            count = await marketdata_service.sync_securities_from_moex()

            assert count == 3
            mock_get_securities.assert_called_once()

            # Verify securities were added to DataManager
            securities = await marketdata_service.get_securities()
            assert len(securities) == 3

            secids = [sec.secid for sec in securities]
            assert "SBER" in secids
            assert "GAZP" in secids
            assert "LKOH" in secids

    @pytest.mark.asyncio
    async def test_sync_securities_avoids_duplicates(self, marketdata_service):
        "Test that sync doesn't create duplicate securities"
        # First, add a security manually
        security_data = SecurityCreate(secid="SBER", name="Existing Sber")
        await marketdata_service.create_security(security_data)

        # Mock MOEX response including the existing security in dict format
        mock_securities_data = [
            {
                "secid": "SBER",
                "shortname": "Сбербанк",
            },  # This should not be added again
            {"secid": "GAZP", "shortname": "Газпром"},  # This should be added
        ]

        with patch.object(
            marketdata_service.moex_adapter, "get_securities", new_callable=AsyncMock
        ) as mock_get_securities:
            mock_get_securities.return_value = mock_securities_data

            count = await marketdata_service.sync_securities_from_moex()

            # Only GAZP should be added, SBER already exists
            assert count == 1

            # Total securities should be 2
            securities = await marketdata_service.get_securities()
            assert len(securities) == 2

    @pytest.mark.asyncio
    async def test_sync_securities_empty_response(self, marketdata_service):
        "Test sync with empty MOEX response"
        with patch.object(
            marketdata_service.moex_adapter, "get_securities", new_callable=AsyncMock
        ) as mock_get_securities:
            mock_get_securities.return_value = []

            count = await marketdata_service.sync_securities_from_moex()

            assert count == 0
            securities = await marketdata_service.get_securities()
            assert len(securities) == 0

    @pytest.mark.asyncio
    async def test_sync_securities_malformed_data(self, marketdata_service):
        "Test sync with malformed MOEX data"
        # Mock response with incomplete data
        mock_securities_data = [
            {"secid": "SBER"},  # Missing name
            {"secid": "GAZP", "shortname": "Газпром"},  # Complete
            {},  # Empty entry
        ]

        with patch.object(
            marketdata_service.moex_adapter, "get_securities", new_callable=AsyncMock
        ) as mock_get_securities:
            mock_get_securities.return_value = mock_securities_data

            count = await marketdata_service.sync_securities_from_moex()

            # Only GAZP should be added (has both secid and name)
            assert count == 1

            securities = await marketdata_service.get_securities()
            assert len(securities) == 1
            assert securities[0].secid == "GAZP"

    @pytest.mark.asyncio
    async def test_service_cleanup(self, marketdata_service):
        "Test that service properly closes its resources"
        # This test ensures the close method works
        await marketdata_service.close()
        # If this doesn't raise an exception, the test passes


class TestMarketDataServiceDataManagerIsolation:
    "Test MarketDataService isolation with different DataManager instances"

    @pytest.mark.asyncio
    async def test_separate_services_are_isolated(self):
        "Test that services with different DataManagers are isolated"
        dm1 = DataManager()
        dm2 = DataManager()

        service1 = MarketDataService(dm1)
        service2 = MarketDataService(dm2)

        try:
            # Add security to first service
            security_data = SecurityCreate(secid="SBER", name="Сбербанк")
            await service1.create_security(security_data)

            # Second service should not see this security
            securities2 = await service2.get_securities()
            assert len(securities2) == 0

            # First service should still see it
            securities1 = await service1.get_securities()
            assert len(securities1) == 1
            assert securities1[0].secid == "SBER"

        finally:
            await service1.close()
            await service2.close()
