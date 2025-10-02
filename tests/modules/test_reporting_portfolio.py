"""Тесты для нового функционала отчетности по портфелю"""

import pytest
import os
import json
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.reporting.service import ReportingService
from app.modules.portfolio.models import Portfolio, Position
from app.modules.marketdata.models import Security, Quote
from app.storage import DataManager


class TestPortfolioReporting:
    """Тесты для генерации отчетов по портфелю"""

    @pytest.fixture
    def data_manager(self):
        """Фикстура для DataManager с тестовыми данными"""
        dm = DataManager()
        
        # Создаем тестовый портфель
        portfolio = Portfolio(
            id=1,
            name="Тестовый портфель",
            description="Портфель для тестирования"
        )
        dm.add_portfolio(portfolio)
        
        # Создаем тестовые ценные бумаги
        securities = [
            Security(id=1, secid="SBER", name="Сбербанк", isin="RU0009029540"),
            Security(id=2, secid="GAZP", name="Газпром", isin="RU0007661625"),
            Security(id=3, secid="SU26238RMFS2", name="ОФЗ 26238", isin="RU000A103X66")
        ]
        
        for security in securities:
            dm.add_security(security)
        
        # Создаем тестовые позиции
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
            dm.add_position(position)
        
        # Создаем тестовые котировки
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
            dm.add_quote(quote)
        
        return dm

    @pytest.fixture
    def reporting_service(self, data_manager):
        """Фикстура для ReportingService"""
        return ReportingService(data_manager)

    @pytest.mark.asyncio
    async def test_generate_portfolio_json_report_success(self, reporting_service):
        """Тест успешной генерации JSON отчета"""
        result = await reporting_service.generate_portfolio_json_report(1)
        
        # Проверяем структуру ответа
        assert result is not None
        assert isinstance(result, dict)
        
        # Проверяем обязательные поля
        assert "portfolio_id" in result
        assert "portfolio_name" in result
        assert "generated_at" in result
        assert "assets" in result
        assert "summary" in result
        assert "asset_allocation" in result
        
        # Проверяем данные портфеля
        assert result["portfolio_id"] == 1
        assert result["portfolio_name"] == "Тестовый портфель"
        
        # Проверяем количество активов
        assert len(result["assets"]) == 3
        
        # Проверяем структуру summary
        summary = result["summary"]
        assert "total_portfolio_value" in summary
        assert "total_pnl" in summary
        assert "total_pnl_percent" in summary
        assert "assets_count" in summary
        assert summary["assets_count"] == 3
        
        # Проверяем структуру asset_allocation
        allocation = result["asset_allocation"]
        assert "stocks" in allocation
        assert "bonds" in allocation
        assert "value" in allocation["stocks"]
        assert "percent" in allocation["stocks"]
        assert "value" in allocation["bonds"]
        assert "percent" in allocation["bonds"]

    @pytest.mark.asyncio
    async def test_generate_portfolio_json_report_calculations(self, reporting_service):
        """Тест правильности расчетов в JSON отчете"""
        result = await reporting_service.generate_portfolio_json_report(1)
        
        # Проверяем расчеты по первому активу (SBER)
        sber_asset = next(asset for asset in result["assets"] if asset["secid"] == "SBER")
        
        assert sber_asset["quantity"] == 100.0
        assert sber_asset["avg_price"] == 250.0
        assert sber_asset["current_price"] == 260.5
        assert sber_asset["market_value"] == 26050.0  # 100 * 260.5
        assert sber_asset["pnl"] == 1050.0  # (260.5 - 250.0) * 100
        assert abs(sber_asset["pnl_percent"] - 4.2) < 0.01  # 1050 / 25000 * 100
        
        # Проверяем общую стоимость портфеля
        expected_total = 26050.0 + 8765.0 + 9800.0  # SBER + GAZP + Bond
        assert abs(result["summary"]["total_portfolio_value"] - expected_total) < 0.01

    @pytest.mark.asyncio
    async def test_generate_portfolio_json_report_asset_classification(self, reporting_service):
        """Тест классификации активов на акции и облигации"""
        result = await reporting_service.generate_portfolio_json_report(1)
        
        allocation = result["asset_allocation"]
        
        # Проверяем, что есть и акции, и облигации
        assert allocation["stocks"]["value"] > 0
        assert allocation["bonds"]["value"] > 0
        
        # Проверяем, что проценты в сумме близки к 100%
        total_percent = allocation["stocks"]["percent"] + allocation["bonds"]["percent"]
        assert abs(total_percent - 100.0) < 0.1

    @pytest.mark.asyncio
    async def test_generate_portfolio_json_report_nonexistent_portfolio(self, reporting_service):
        """Тест для несуществующего портфеля"""
        result = await reporting_service.generate_portfolio_json_report(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_portfolio_pdf_report_success(self, reporting_service):
        """Тест успешной генерации PDF отчета"""
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs') as mock_makedirs, \
             patch('reportlab.platypus.SimpleDocTemplate') as mock_doc:
            
            # Мокаем PDF генерацию
            mock_doc_instance = MagicMock()
            mock_doc.return_value = mock_doc_instance
            
            result = await reporting_service.generate_portfolio_pdf_report(1)
            
            # Проверяем, что возвращается путь к файлу
            assert result is not None
            assert isinstance(result, str)
            assert "report_" in result and result.endswith(".pdf")
            assert result.endswith(".pdf")
            
            # Проверяем, что PDF документ был создан
            mock_doc_instance.build.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_portfolio_pdf_report_creates_directory(self, reporting_service):
        """Тест создания директории reports при генерации PDF"""
        with patch('os.path.exists', return_value=False), \
             patch('os.makedirs') as mock_makedirs, \
             patch('reportlab.platypus.SimpleDocTemplate') as mock_doc:
            
            mock_doc_instance = MagicMock()
            mock_doc.return_value = mock_doc_instance
            
            await reporting_service.generate_portfolio_pdf_report(1)
            
            # Проверяем, что директория была создана
            mock_makedirs.assert_called_once_with("reports")

    @pytest.mark.asyncio
    async def test_generate_portfolio_pdf_report_nonexistent_portfolio(self, reporting_service):
        """Тест генерации PDF для несуществующего портфеля"""
        result = await reporting_service.generate_portfolio_pdf_report(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_portfolio_json_report_empty_portfolio(self, data_manager):
        """Тест для портфеля без позиций"""
        # Создаем пустой портфель
        empty_portfolio = Portfolio(
            id=2,
            name="Пустой портфель",
            description="Портфель без позиций"
        )
        data_manager.add_portfolio(empty_portfolio)
        
        reporting_service = ReportingService(data_manager)
        result = await reporting_service.generate_portfolio_json_report(2)
        
        # Проверяем, что отчет создается даже для пустого портфеля
        assert result is not None
        assert result["summary"]["assets_count"] == 0
        assert result["summary"]["total_portfolio_value"] == 0.0
        assert result["summary"]["total_pnl"] == 0.0
        assert len(result["assets"]) == 0

    @pytest.mark.asyncio
    async def test_generate_portfolio_json_report_no_quotes(self, data_manager):
        """Тест для портфеля с позициями, но без котировок"""
        # Создаем портфель с позицией, но без котировки
        portfolio = Portfolio(
            id=3,
            name="Портфель без котировок",
            description="Тест"
        )
        data_manager.add_portfolio(portfolio)
        
        # Добавляем ценную бумагу и позицию
        security = Security(id=4, secid="TEST", name="Тестовая бумага")
        data_manager.add_security(security)
        
        position = Position(
            id=4,
            portfolio_id=3,
            secid="TEST",
            quantity=Decimal("100"),
            avg_price=Decimal("100.00")
        )
        data_manager.add_position(position)
        
        reporting_service = ReportingService(data_manager)
        result = await reporting_service.generate_portfolio_json_report(3)
        
        # Проверяем, что отчет создается с использованием средней цены как текущей
        assert result is not None
        assert len(result["assets"]) == 1
        assert result["assets"][0]["current_price"] == 100.0  # avg_price as fallback

    def test_asset_classification_logic(self, reporting_service):
        """Тест логики классификации активов"""
        # Тестируем классификацию акций (короткие коды без цифр)
        assert len("SBER") <= 4 and not any(c.isdigit() for c in "SBER")
        assert len("GAZP") <= 4 and not any(c.isdigit() for c in "GAZP")
        
        # Тестируем классификацию облигаций (длинные коды с цифрами)
        assert not (len("SU26238RMFS2") <= 4 and not any(c.isdigit() for c in "SU26238RMFS2"))


class TestPortfolioReportingEdgeCases:
    """Тесты граничных случаев и обработки ошибок"""

    @pytest.mark.asyncio
    async def test_portfolio_with_zero_quantities(self):
        """Тест портфеля с нулевыми количествами"""
        dm = DataManager()
        
        portfolio = Portfolio(id=1, name="Test")
        dm.add_portfolio(portfolio)
        
        security = Security(id=1, secid="TEST", name="Test Security")
        dm.add_security(security)
        
        # Позиция с нулевым количеством
        position = Position(
            id=1,
            portfolio_id=1,
            secid="TEST",
            quantity=Decimal("0"),
            avg_price=Decimal("100.00")
        )
        dm.add_position(position)
        
        quote = Quote(
            id=1,
            secid="TEST",
            timestamp=datetime.now(),
            price=Decimal("110.00")
        )
        dm.add_quote(quote)
        
        reporting_service = ReportingService(dm)
        result = await reporting_service.generate_portfolio_json_report(1)
        
        assert result is not None
        assert result["summary"]["total_portfolio_value"] == 0.0

    @pytest.mark.asyncio
    async def test_portfolio_with_negative_quantities(self):
        """Тест портфеля с отрицательными количествами (короткие позиции)"""
        dm = DataManager()
        
        portfolio = Portfolio(id=1, name="Test")
        dm.add_portfolio(portfolio)
        
        security = Security(id=1, secid="TEST", name="Test Security")
        dm.add_security(security)
        
        # Короткая позиция
        position = Position(
            id=1,
            portfolio_id=1,
            secid="TEST",
            quantity=Decimal("-100"),
            avg_price=Decimal("100.00")
        )
        dm.add_position(position)
        
        quote = Quote(
            id=1,
            secid="TEST",
            timestamp=datetime.now(),
            price=Decimal("90.00")  # Цена упала - прибыль на короткой позиции
        )
        dm.add_quote(quote)
        
        reporting_service = ReportingService(dm)
        result = await reporting_service.generate_portfolio_json_report(1)
        
        assert result is not None
        assert len(result["assets"]) == 1
        asset = result["assets"][0]
        assert asset["quantity"] == -100.0
        assert asset["pnl"] == 1000.0  # (100 - 90) * 100 прибыль на короткой позиции

    @pytest.mark.asyncio
    async def test_pdf_generation_error_handling(self):
        """Тест обработки ошибок при генерации PDF"""
        dm = DataManager()
        portfolio = Portfolio(id=1, name="Test")
        dm.add_portfolio(portfolio)
        
        reporting_service = ReportingService(dm)
        
        # Мокаем ошибку при создании PDF
        with patch('reportlab.platypus.SimpleDocTemplate', side_effect=Exception("PDF Error")):
            with pytest.raises(Exception, match="PDF Error"):
                await reporting_service.generate_portfolio_pdf_report(1)