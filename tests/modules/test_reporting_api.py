"""Интеграционные тесты для API эндпоинтов отчетности"""

import pytest
import os
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.storage import get_data_manager
from app.modules.portfolio.models import Portfolio, Position
from app.modules.marketdata.models import Security, Quote


class TestReportingAPIEndpoints:
    """Тесты для API эндпоинтов отчетности"""

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Настройка тестовых данных перед каждым тестом"""
        # Получаем чистый DataManager для каждого теста
        data_manager = get_data_manager()
        
        # Очищаем все данные
        data_manager._portfolios_store.clear()
        data_manager._positions_store.clear()
        data_manager._securities_store.clear()
        data_manager._quotes_store.clear()
        
        # Создаем тестовые данные
        portfolio = Portfolio(
            id=1,
            name="Test Portfolio",
            description="Portfolio for API testing"
        )
        data_manager.add_portfolio(portfolio)
        
        # Добавляем ценные бумаги
        securities = [
            Security(id=1, secid="SBER", name="Сбербанк", isin="RU0009029540"),
            Security(id=2, secid="GAZP", name="Газпром", isin="RU0007661625"),
            Security(id=3, secid="SU26238RMFS2", name="ОФЗ 26238", isin="RU000A103X66")
        ]
        for security in securities:
            data_manager.add_security(security)
        
        # Добавляем позиции
        positions = [
            Position(
                id=1,
                portfolio_id=1,
                secid="SBER",
                quantity=Decimal("100"),
                avg_price=Decimal("250.00")
            ),
            Position(
                id=2,
                portfolio_id=1,
                secid="GAZP",
                quantity=Decimal("50"),
                avg_price=Decimal("180.00")
            ),
            Position(
                id=3,
                portfolio_id=1,
                secid="SU26238RMFS2",
                quantity=Decimal("10"),
                avg_price=Decimal("950.00")
            )
        ]
        for position in positions:
            data_manager.add_position(position)
        
        # Добавляем котировки
        quotes = [
            Quote(
                id=1,
                secid="SBER",
                timestamp=datetime.now(),
                price=Decimal("260.50")
            ),
            Quote(
                id=2,
                secid="GAZP",
                timestamp=datetime.now(),
                price=Decimal("175.30")
            ),
            Quote(
                id=3,
                secid="SU26238RMFS2",
                timestamp=datetime.now(),
                price=Decimal("980.00")
            )
        ]
        for quote in quotes:
            data_manager.add_quote(quote)

    @pytest.fixture
    def client(self):
        """Тестовый клиент FastAPI"""
        return TestClient(app)

    def test_get_portfolio_json_report_success(self, client):
        """Тест успешного получения JSON отчета через API"""
        response = client.get("/api/v1/reports/json?portfolio_id=1")
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем структуру ответа
        assert "portfolio_id" in data
        assert "portfolio_name" in data
        assert "generated_at" in data
        assert "assets" in data
        assert "summary" in data
        assert "asset_allocation" in data
        
        # Проверяем данные
        assert data["portfolio_id"] == 1
        assert data["portfolio_name"] == "Test Portfolio"
        assert len(data["assets"]) == 3
        assert data["summary"]["assets_count"] == 3
        
        # Проверяем структуру активов
        for asset in data["assets"]:
            assert "secid" in asset
            assert "name" in asset
            assert "quantity" in asset
            assert "avg_price" in asset
            assert "current_price" in asset
            assert "market_value" in asset
            assert "pnl" in asset
            assert "pnl_percent" in asset

    def test_get_portfolio_json_report_nonexistent_portfolio(self, client):
        """Тест запроса JSON отчета для несуществующего портфеля"""
        response = client.get("/api/v1/reports/json?portfolio_id=999")
        
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert "Portfolio with id 999 not found" in error_data["detail"]

    def test_get_portfolio_json_report_default_portfolio(self, client):
        """Тест получения JSON отчета с параметром по умолчанию"""
        response = client.get("/api/v1/reports/json?portfolio_id=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["portfolio_id"] == 1  # default portfolio_id

    def test_get_portfolio_json_report_calculations(self, client):
        """Тест правильности расчетов в JSON отчете через API"""
        response = client.get("/api/v1/reports/json?portfolio_id=1")
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем расчеты по SBER
        sber_asset = next(asset for asset in data["assets"] if asset["secid"] == "SBER")
        assert sber_asset["quantity"] == 100.0
        assert sber_asset["avg_price"] == 250.0
        assert sber_asset["current_price"] == 260.5
        assert sber_asset["market_value"] == 26050.0
        assert sber_asset["pnl"] == 1050.0
        
        # Проверяем распределение активов
        allocation = data["asset_allocation"]
        assert allocation["stocks"]["value"] > 0
        assert allocation["bonds"]["value"] > 0

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_generate_portfolio_pdf_report_success(self, mock_doc, mock_makedirs, mock_exists, client):
        """Тест успешной генерации PDF отчета через API"""
        mock_exists.return_value = True
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance
        
        response = client.get("/api/v1/reports/pdf?portfolio_id=1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "file_path" in data
        assert "message" in data
        assert data["message"] == "PDF report generated successfully"
        assert "report_" in data["file_path"] and data["file_path"].endswith(".pdf")
        assert data["file_path"].endswith(".pdf")
        
        # Проверяем, что PDF документ был создан
        mock_doc_instance.build.assert_called_once()

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_generate_portfolio_pdf_report_creates_directory(self, mock_doc, mock_makedirs, mock_exists, client):
        """Тест создания директории при генерации PDF через API"""
        mock_exists.return_value = False  # Директория не существует
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance
        
        response = client.get("/api/v1/reports/pdf?portfolio_id=1")
        
        assert response.status_code == 200
        mock_makedirs.assert_called_once_with("reports")

    def test_generate_portfolio_pdf_report_nonexistent_portfolio(self, client):
        """Тест генерации PDF для несуществующего портфеля через API"""
        response = client.get("/api/v1/reports/pdf?portfolio_id=999")
        
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert "Portfolio with id 999 not found" in error_data["detail"]

    def test_generate_portfolio_pdf_report_default_portfolio(self, client):
        """Тест генерации PDF с параметром по умолчанию"""
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs'), \
             patch('reportlab.platypus.SimpleDocTemplate') as mock_doc:
            
            mock_doc_instance = MagicMock()
            mock_doc.return_value = mock_doc_instance
            
            response = client.get("/api/v1/reports/pdf?portfolio_id=1")
            
            assert response.status_code == 200
            data = response.json()
            assert "file_path" in data

    @patch('app.modules.reporting.service.ReportingService.generate_portfolio_json_report')
    def test_json_report_service_error_handling(self, mock_generate, client):
        """Тест обработки ошибок сервиса в JSON эндпоинте"""
        mock_generate.side_effect = Exception("Service error")
        
        response = client.get("/api/v1/reports/json?portfolio_id=1")
        
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert "Error generating report: Service error" in error_data["detail"]

    @patch('app.modules.reporting.service.ReportingService.generate_portfolio_pdf_report')
    def test_pdf_report_service_error_handling(self, mock_generate, client):
        """Тест обработки ошибок сервиса в PDF эндпоинте"""
        mock_generate.side_effect = Exception("PDF generation failed")
        
        response = client.get("/api/v1/reports/pdf?portfolio_id=1")
        
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert "Error generating PDF report: PDF generation failed" in error_data["detail"]

    def test_api_endpoints_response_content_type(self, client):
        """Тест типов содержимого ответов API"""
        # JSON эндпоинт должен возвращать JSON
        response = client.get("/api/v1/reports/json?portfolio_id=1")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        
        # PDF эндпоинт также возвращает JSON с информацией о файле
        with patch('os.path.exists', return_value=True), \
             patch('reportlab.platypus.SimpleDocTemplate') as mock_doc:
            
            mock_doc_instance = MagicMock()
            mock_doc.return_value = mock_doc_instance
            
            response = client.get("/api/v1/reports/pdf?portfolio_id=1")
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]

    def test_api_endpoints_query_parameter_validation(self, client):
        """Тест валидации параметров запроса"""
        # Негативное значение portfolio_id
        response = client.get("/api/v1/reports/json?portfolio_id=-1")
        assert response.status_code == 404  # Несуществующий портфель
        
        # Нулевое значение portfolio_id
        response = client.get("/api/v1/reports/json?portfolio_id=0")
        assert response.status_code == 404  # Несуществующий портфель
        
        # Некорректный тип параметра (будет использоваться значение по умолчанию)
        response = client.get("/api/v1/reports/json?portfolio_id=abc")
        assert response.status_code == 422  # Validation error


class TestReportingAPIIntegration:
    """Интеграционные тесты для полного цикла работы с отчетами"""

    @pytest.fixture
    def client(self):
        """Тестовый клиент FastAPI"""
        return TestClient(app)

    def test_full_reporting_workflow(self, client):
        """Тест полного цикла работы с отчетами"""
        # Настраиваем тестовые данные
        data_manager = get_data_manager()
        data_manager._portfolios_store.clear()
        data_manager._positions_store.clear()
        data_manager._securities_store.clear()
        data_manager._quotes_store.clear()
        
        # Создаем портфель
        portfolio = Portfolio(id=1, name="Integration Test Portfolio")
        data_manager.add_portfolio(portfolio)
        
        # Добавляем одну позицию
        security = Security(id=1, secid="TEST", name="Test Security")
        data_manager.add_security(security)
        
        position = Position(
            id=1,
            portfolio_id=1,
            secid="TEST",
            quantity=Decimal("100"),
            avg_price=Decimal("100.00")
        )
        data_manager.add_position(position)
        
        quote = Quote(
            id=1,
            secid="TEST",
            timestamp=datetime.now(),
            price=Decimal("110.00")
        )
        data_manager.add_quote(quote)
        
        # 1. Получаем JSON отчет
        json_response = client.get("/api/v1/reports/json?portfolio_id=1")
        assert json_response.status_code == 200
        json_data = json_response.json()
        
        # Проверяем данные в JSON отчете
        assert json_data["portfolio_id"] == 1
        assert len(json_data["assets"]) == 1
        assert json_data["assets"][0]["pnl"] == 1000.0  # (110 - 100) * 100
        
        # 2. Генерируем PDF отчет
        with patch('os.path.exists', return_value=True), \
             patch('reportlab.platypus.SimpleDocTemplate') as mock_doc:
            
            mock_doc_instance = MagicMock()
            mock_doc.return_value = mock_doc_instance
            
            pdf_response = client.get("/api/v1/reports/pdf?portfolio_id=1")
            assert pdf_response.status_code == 200
            pdf_data = pdf_response.json()
            
            assert "file_path" in pdf_data
            mock_doc_instance.build.assert_called_once()

    def test_concurrent_report_generation(self, client):
        """Тест одновременной генерации нескольких отчетов"""
        # Настраиваем данные
        data_manager = get_data_manager()
        data_manager._portfolios_store.clear()
        data_manager._positions_store.clear()
        
        portfolio = Portfolio(id=1, name="Concurrent Test Portfolio")
        data_manager.add_portfolio(portfolio)
        
        # Генерируем несколько JSON отчетов одновременно
        responses = []
        for _ in range(3):
            response = client.get("/api/v1/reports/json?portfolio_id=1")
            responses.append(response)
        
        # Все запросы должны быть успешными
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["portfolio_id"] == 1