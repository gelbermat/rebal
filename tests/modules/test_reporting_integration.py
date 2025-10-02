"""Финальные интеграционные тесты для модуля reporting"""

import pytest
import os
import json
import re
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from .conftest_reporting import TEST_CONSTANTS


class TestReportingFullIntegration:
    """Полные интеграционные тесты для модуля отчетности"""

    @pytest.fixture
    def client(self):
        """Тестовый клиент FastAPI"""
        return TestClient(app)

    def test_full_reporting_workflow_with_sample_data(self, client, sample_portfolio_data):
        """Тест полного цикла работы с отчетами на примере данных"""
        
        # 1. Проверяем JSON отчет
        json_response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/json?portfolio_id=1")
        assert json_response.status_code == 200
        
        json_data = json_response.json()
        
        # Валидируем структуру JSON отчета
        required_fields = ["portfolio_id", "portfolio_name", "generated_at", "assets", "summary", "asset_allocation"]
        for field in required_fields:
            assert field in json_data, f"Missing required field: {field}"
        
        # Проверяем корректность данных
        assert json_data["portfolio_id"] == 1
        assert json_data["portfolio_name"] == "Тестовый портфель"
        assert len(json_data["assets"]) == 4  # SBER, GAZP, SU26238RMFS2, LKOH
        
        # Проверяем summary
        summary = json_data["summary"]
        assert summary["assets_count"] == 4
        assert summary["total_portfolio_value"] > 0
        assert "total_pnl" in summary
        assert "total_pnl_percent" in summary
        
        # Проверяем asset_allocation
        allocation = json_data["asset_allocation"]
        assert "stocks" in allocation
        assert "bonds" in allocation
        
        # Сумма процентов должна быть близка к 100%
        total_percent = allocation["stocks"]["percent"] + allocation["bonds"]["percent"]
        assert abs(total_percent - 100.0) < 1.0
        
        # 2. Проверяем детали активов
        for asset in json_data["assets"]:
            required_asset_fields = ["secid", "name", "quantity", "avg_price", "current_price", "market_value", "pnl", "pnl_percent"]
            for field in required_asset_fields:
                assert field in asset, f"Missing asset field: {field}"
            
            # Проверяем корректность расчетов
            expected_market_value = asset["quantity"] * asset["current_price"]
            assert abs(asset["market_value"] - expected_market_value) < 0.01
            
            if asset["avg_price"] > 0:
                expected_pnl = (asset["current_price"] - asset["avg_price"]) * asset["quantity"]
                assert abs(asset["pnl"] - expected_pnl) < 0.01
        
        # 3. Генерируем PDF отчет
        with patch('os.path.exists', return_value=True), \
             patch('reportlab.platypus.SimpleDocTemplate') as mock_doc:
            
            mock_doc_instance = MagicMock()
            mock_doc.return_value = mock_doc_instance
            
            pdf_response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/pdf?portfolio_id=1")
            assert pdf_response.status_code == 200
            
            pdf_data = pdf_response.json()
            assert "file_path" in pdf_data
            assert "message" in pdf_data
            assert pdf_data["message"] == "PDF report generated successfully"
            
            # Проверяем формат имени файла
            file_path = pdf_data["file_path"]
            assert file_path.startswith(TEST_CONSTANTS["REPORTS_DIR"])
            assert file_path.endswith(".pdf")
            
            # Проверяем паттерн имени файла (report_YYYY-MM-DD.pdf)
            filename = os.path.basename(file_path)
            assert re.match(TEST_CONSTANTS["PDF_FILENAME_PATTERN"], filename)
            
            # Проверяем, что PDF был создан
            mock_doc_instance.build.assert_called_once()

    def test_multiple_portfolios_reporting(self, client, diversified_portfolio_data):
        """Тест отчетности для нескольких портфелей"""
        
        # Тестируем отчеты для разных портфелей
        portfolio_ids = [1, 2, 3]
        expected_names = ["Консервативный портфель", "Агрессивный портфель", "Сбалансированный портфель"]
        
        for portfolio_id, expected_name in zip(portfolio_ids, expected_names):
            response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/json?portfolio_id={portfolio_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["portfolio_id"] == portfolio_id
            assert data["portfolio_name"] == expected_name
            assert len(data["assets"]) > 0

    def test_edge_cases_reporting(self, client, edge_case_portfolio_data):
        """Тест отчетности для граничных случаев"""
        
        response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/json?portfolio_id=1")
        assert response.status_code == 200
        
        data = response.json()
        
        # Проверяем, что система корректно обрабатывает граничные случаи
        assert data["portfolio_id"] == 1
        assert len(data["assets"]) == 4  # Включая позицию с нулевым количеством
        
        # Проверяем обработку экстремальных значений
        for asset in data["assets"]:
            # Все числовые поля должны быть валидными
            assert isinstance(asset["quantity"], (int, float))
            assert isinstance(asset["avg_price"], (int, float))
            assert isinstance(asset["current_price"], (int, float))
            assert isinstance(asset["market_value"], (int, float))
            assert isinstance(asset["pnl"], (int, float))
            assert isinstance(asset["pnl_percent"], (int, float))

    def test_concurrent_requests(self, client, sample_portfolio_data):
        """Тест одновременных запросов отчетов"""
        import threading
        import time
        
        responses = []
        errors = []
        
        def make_request():
            try:
                response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/json?portfolio_id=1")
                responses.append(response)
            except Exception as e:
                errors.append(e)
        
        # Запускаем 10 одновременных запросов
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(responses) == 10
        
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["portfolio_id"] == 1

    @patch('app.modules.reporting.service.ReportingService.generate_portfolio_json_report')
    def test_error_recovery(self, mock_generate, client, sample_portfolio_data):
        """Тест восстановления после ошибок"""
        
        # Первый запрос завершается ошибкой
        mock_generate.side_effect = Exception("Temporary error")
        
        response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/json?portfolio_id=1")
        assert response.status_code == 500
        
        # Второй запрос должен работать нормально
        mock_generate.side_effect = None
        mock_generate.return_value = {
            "portfolio_id": 1,
            "portfolio_name": "Test",
            "generated_at": datetime.now().isoformat(),
            "assets": [],
            "summary": {"total_portfolio_value": 0, "total_pnl": 0, "assets_count": 0},
            "asset_allocation": {"stocks": {"value": 0, "percent": 0}, "bonds": {"value": 0, "percent": 0}}
        }
        
        response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/json?portfolio_id=1")
        assert response.status_code == 200

    def test_response_time_performance(self, client, sample_portfolio_data):
        """Тест производительности генерации отчетов"""
        import time
        
        # Замеряем время генерации JSON отчета
        start_time = time.time()
        response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/json?portfolio_id=1")
        json_time = time.time() - start_time
        
        assert response.status_code == 200
        assert json_time < 1.0, f"JSON report generation took too long: {json_time}s"
        
        # Замеряем время генерации PDF отчета (с моком)
        with patch('os.path.exists', return_value=True), \
             patch('reportlab.platypus.SimpleDocTemplate') as mock_doc:
            
            mock_doc_instance = MagicMock()
            mock_doc.return_value = mock_doc_instance
            
            start_time = time.time()
            response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/pdf?portfolio_id=1")
            pdf_time = time.time() - start_time
            
            assert response.status_code == 200
            assert pdf_time < 2.0, f"PDF report generation took too long: {pdf_time}s"

    def test_memory_usage(self, client, sample_portfolio_data):
        """Тест использования памяти при генерации отчетов"""
        import psutil
        import os
        
        # Получаем текущий процесс
        process = psutil.Process(os.getpid())
        
        # Замеряем использование памяти до
        memory_before = process.memory_info().rss
        
        # Генерируем несколько отчетов
        for _ in range(5):
            response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/json?portfolio_id=1")
            assert response.status_code == 200
        
        # Замеряем использование памяти после
        memory_after = process.memory_info().rss
        
        # Прирост памяти не должен быть значительным (менее 50MB)
        memory_growth = memory_after - memory_before
        assert memory_growth < 50 * 1024 * 1024, f"Memory growth too high: {memory_growth} bytes"

    def test_data_consistency(self, client, sample_portfolio_data):
        """Тест консистентности данных в отчетах"""
        
        # Генерируем несколько отчетов подряд
        responses = []
        for _ in range(3):
            response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/json?portfolio_id=1")
            assert response.status_code == 200
            responses.append(response.json())
        
        # Все отчеты должны содержать одинаковые данные
        first_report = responses[0]
        for report in responses[1:]:
            assert report["portfolio_id"] == first_report["portfolio_id"]
            assert report["portfolio_name"] == first_report["portfolio_name"]
            assert len(report["assets"]) == len(first_report["assets"])
            
            # Сравниваем данные активов
            for i, asset in enumerate(report["assets"]):
                first_asset = first_report["assets"][i]
                assert asset["secid"] == first_asset["secid"]
                assert abs(asset["market_value"] - first_asset["market_value"]) < 0.01
                assert abs(asset["pnl"] - first_asset["pnl"]) < 0.01

    def test_comprehensive_validation(self, client, sample_portfolio_data):
        """Комплексная валидация всех компонентов отчета"""
        
        response = client.get(f"{TEST_CONSTANTS['API_PREFIX']}/reports/json?portfolio_id=1")
        assert response.status_code == 200
        
        data = response.json()
        
        # 1. Валидация структуры
        assert isinstance(data, dict)
        assert isinstance(data["assets"], list)
        assert isinstance(data["summary"], dict)
        assert isinstance(data["asset_allocation"], dict)
        
        # 2. Валидация временных меток
        generated_at = datetime.fromisoformat(data["generated_at"].replace('Z', '+00:00'))
        assert isinstance(generated_at, datetime)
        
        # 3. Валидация математической корректности
        total_value_calculated = sum(asset["market_value"] for asset in data["assets"])
        assert abs(total_value_calculated - data["summary"]["total_portfolio_value"]) < 0.01
        
        total_pnl_calculated = sum(asset["pnl"] for asset in data["assets"])
        assert abs(total_pnl_calculated - data["summary"]["total_pnl"]) < 0.01
        
        # 4. Валидация распределения активов
        allocation = data["asset_allocation"]
        stocks_value = allocation["stocks"]["value"]
        bonds_value = allocation["bonds"]["value"]
        total_allocation_value = stocks_value + bonds_value
        
        assert abs(total_allocation_value - data["summary"]["total_portfolio_value"]) < 0.01
        
        # 5. Валидация процентов
        if data["summary"]["total_portfolio_value"] > 0:
            stocks_percent_calculated = (stocks_value / data["summary"]["total_portfolio_value"]) * 100
            bonds_percent_calculated = (bonds_value / data["summary"]["total_portfolio_value"]) * 100
            
            assert abs(stocks_percent_calculated - allocation["stocks"]["percent"]) < 0.1
            assert abs(bonds_percent_calculated - allocation["bonds"]["percent"]) < 0.1