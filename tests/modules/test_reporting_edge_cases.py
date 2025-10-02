"""Тесты негативных сценариев и обработки ошибок для reporting модуля"""

import pytest
import os
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.storage import get_data_manager, DataManager
from app.modules.reporting.service import ReportingService
from app.modules.portfolio.models import Portfolio, Position
from app.modules.marketdata.models import Security, Quote


class TestReportingErrorHandling:
    """Тесты для обработки ошибочных ситуаций"""

    @pytest.fixture
    def empty_data_manager(self):
        """Пустой DataManager для тестов"""
        dm = DataManager()
        return dm

    @pytest.fixture
    def reporting_service(self, empty_data_manager):
        """ReportingService с пустым DataManager"""
        return ReportingService(empty_data_manager)

    @pytest.mark.asyncio
    async def test_json_report_no_portfolio(self, reporting_service):
        """Тест JSON отчета для несуществующего портфеля"""
        result = await reporting_service.generate_portfolio_json_report(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_pdf_report_no_portfolio(self, reporting_service):
        """Тест PDF отчета для несуществующего портфеля"""
        result = await reporting_service.generate_portfolio_pdf_report(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_json_report_empty_portfolio(self, empty_data_manager):
        """Тест JSON отчета для пустого портфеля"""
        # Создаем портфель без позиций
        portfolio = Portfolio(id=1, name="Empty Portfolio")
        empty_data_manager.add_portfolio(portfolio)
        
        reporting_service = ReportingService(empty_data_manager)
        result = await reporting_service.generate_portfolio_json_report(1)
        
        assert result is not None
        assert result["summary"]["assets_count"] == 0
        assert result["summary"]["total_portfolio_value"] == 0.0
        assert result["summary"]["total_pnl"] == 0.0
        assert len(result["assets"]) == 0

    @pytest.mark.asyncio
    async def test_json_report_positions_without_quotes(self, empty_data_manager):
        """Тест JSON отчета для позиций без котировок"""
        # Создаем портфель и позицию, но без котировок
        portfolio = Portfolio(id=1, name="Test Portfolio")
        empty_data_manager.add_portfolio(portfolio)
        
        security = Security(id=1, secid="TEST", name="Test Security")
        empty_data_manager.add_security(security)
        
        position = Position(
            id=1,
            portfolio_id=1,
            secid="TEST",
            quantity=Decimal("100"),
            avg_price=Decimal("100.00")
        )
        empty_data_manager.add_position(position)
        
        reporting_service = ReportingService(empty_data_manager)
        result = await reporting_service.generate_portfolio_json_report(1)
        
        assert result is not None
        assert len(result["assets"]) == 1
        # Без котировок должна использоваться средняя цена
        assert result["assets"][0]["current_price"] == 100.0

    @pytest.mark.asyncio
    async def test_pdf_generation_permission_error(self, empty_data_manager):
        """Тест обработки ошибки прав доступа при создании PDF"""
        portfolio = Portfolio(id=1, name="Test Portfolio")
        empty_data_manager.add_portfolio(portfolio)
        
        reporting_service = ReportingService(empty_data_manager)
        
        with patch('os.path.exists', return_value=False), \
             patch('os.makedirs', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                await reporting_service.generate_portfolio_pdf_report(1)


class TestReportingAPIErrorHandling:
    """Тесты обработки ошибок в API эндпоинтах"""

    @pytest.fixture
    def client(self):
        """Тестовый клиент FastAPI"""
        return TestClient(app)

    def test_json_api_invalid_portfolio_id_type(self, client):
        """Тест API с некорректным типом portfolio_id"""
        response = client.get("/api/v1/reports/json?portfolio_id=abc")
        assert response.status_code == 422  # Validation error

    def test_pdf_api_invalid_portfolio_id_type(self, client):
        """Тест API с некорректным типом portfolio_id для PDF"""
        response = client.get("/api/v1/reports/pdf?portfolio_id=abc")
        assert response.status_code == 422  # Validation error

    def test_json_api_negative_portfolio_id(self, client):
        """Тест API с отрицательным portfolio_id"""
        response = client.get("/api/v1/reports/json?portfolio_id=-1")
        assert response.status_code == 404  # Portfolio not found

    def test_pdf_api_negative_portfolio_id(self, client):
        """Тест API с отрицательным portfolio_id для PDF"""
        response = client.get("/api/v1/reports/pdf?portfolio_id=-1")
        assert response.status_code == 404  # Portfolio not found

    @patch('app.modules.reporting.service.ReportingService.generate_portfolio_json_report')
    def test_json_api_internal_server_error(self, mock_generate, client):
        """Тест обработки внутренней ошибки сервера в JSON API"""
        mock_generate.side_effect = RuntimeError("Internal error")
        
        response = client.get("/api/v1/reports/json?portfolio_id=1")
        assert response.status_code == 500
        error_data = response.json()
        assert "Internal error" in error_data["detail"]

    @patch('app.modules.reporting.service.ReportingService.generate_portfolio_pdf_report')
    def test_pdf_api_internal_server_error(self, mock_generate, client):
        """Тест обработки внутренней ошибки сервера в PDF API"""
        mock_generate.side_effect = RuntimeError("PDF error")
        
        response = client.get("/api/v1/reports/pdf?portfolio_id=1")
        assert response.status_code == 500
        error_data = response.json()
        assert "PDF error" in error_data["detail"]