"""Общие фикстуры для тестов модуля reporting"""

import pytest
from decimal import Decimal
from datetime import datetime, date

from app.storage import DataManager
from app.modules.portfolio.models import Portfolio, Position
from app.modules.marketdata.models import Security, Quote
from app.modules.reporting.service import ReportingService


@pytest.fixture(scope="function")
def clean_data_manager():
    """Чистый DataManager для каждого теста"""
    dm = DataManager()
    # Очищаем все данные
    dm._portfolios_store.clear()
    dm._positions_store.clear()
    dm._securities_store.clear()
    dm._quotes_store.clear()
    dm._transactions_store.clear()
    
    # Сбрасываем счетчики ID
    dm._next_portfolio_id = 1
    dm._next_position_id = 1
    dm._next_security_id = 1
    dm._next_quote_id = 1
    dm._next_transaction_id = 1
    
    return dm


@pytest.fixture(scope="function")
def sample_portfolio_data(clean_data_manager):
    """Фикстура с базовыми тестовыми данными для портфеля"""
    dm = clean_data_manager
    
    # Создаем тестовый портфель
    portfolio = Portfolio(
        id=1,
        name="Тестовый портфель",
        description="Портфель для тестирования отчетности",
        total_value=Decimal("50000.00"),
        cash_balance=Decimal("5000.00")
    )
    dm.add_portfolio(portfolio)
    
    # Создаем тестовые ценные бумаги
    securities = [
        Security(
            id=1, 
            secid="SBER", 
            name="ПАО Сбербанк", 
            isin="RU0009029540",
            engine="stock",
            market="shares"
        ),
        Security(
            id=2, 
            secid="GAZP", 
            name="ПАО Газпром", 
            isin="RU0007661625",
            engine="stock",
            market="shares"
        ),
        Security(
            id=3, 
            secid="SU26238RMFS2", 
            name="ОФЗ 26238", 
            isin="RU000A103X66",
            engine="stock",
            market="bonds"
        ),
        Security(
            id=4, 
            secid="LKOH", 
            name="ЛУКОЙЛ", 
            isin="RU0009024277",
            engine="stock",
            market="shares"
        )
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
            avg_price=Decimal("250.00"),
            target_weight=Decimal("0.30")
        ),
        Position(
            id=2,
            portfolio_id=1,
            secid="GAZP",
            quantity=Decimal("50"),
            avg_price=Decimal("180.00"),
            target_weight=Decimal("0.20")
        ),
        Position(
            id=3,
            portfolio_id=1,
            secid="SU26238RMFS2",
            quantity=Decimal("10"),
            avg_price=Decimal("950.00"),
            target_weight=Decimal("0.25")
        ),
        Position(
            id=4,
            portfolio_id=1,
            secid="LKOH",
            quantity=Decimal("20"),
            avg_price=Decimal("6500.00"),
            target_weight=Decimal("0.25")
        )
    ]
    
    for position in positions:
        dm.add_position(position)
    
    # Создаем тестовые котировки
    base_time = datetime.now()
    quotes = [
        Quote(
            id=1,
            secid="SBER",
            timestamp=base_time,
            open_price=Decimal("258.00"),
            high_price=Decimal("265.00"),
            low_price=Decimal("255.00"),
            price=Decimal("260.50"),
            volume=Decimal("1000000")
        ),
        Quote(
            id=2,
            secid="GAZP",
            timestamp=base_time,
            open_price=Decimal("178.00"),
            high_price=Decimal("182.00"),
            low_price=Decimal("174.00"),
            price=Decimal("175.30"),
            volume=Decimal("500000")
        ),
        Quote(
            id=3,
            secid="SU26238RMFS2",
            timestamp=base_time,
            open_price=Decimal("975.00"),
            high_price=Decimal("985.00"),
            low_price=Decimal("970.00"),
            price=Decimal("980.00"),
            volume=Decimal("50000")
        ),
        Quote(
            id=4,
            secid="LKOH",
            timestamp=base_time,
            open_price=Decimal("6450.00"),
            high_price=Decimal("6550.00"),
            low_price=Decimal("6400.00"),
            price=Decimal("6520.00"),
            volume=Decimal("100000")
        )
    ]
    
    for quote in quotes:
        dm.add_quote(quote)
    
    return dm


@pytest.fixture(scope="function")
def diversified_portfolio_data(clean_data_manager):
    """Фикстура с разнообразными данными портфеля"""
    dm = clean_data_manager
    
    # Создаем несколько портфелей
    portfolios = [
        Portfolio(id=1, name="Консервативный портфель", description="Портфель с низким риском"),
        Portfolio(id=2, name="Агрессивный портфель", description="Портфель с высоким риском"),
        Portfolio(id=3, name="Сбалансированный портфель", description="Сбалансированный портфель")
    ]
    
    for portfolio in portfolios:
        dm.add_portfolio(portfolio)
    
    # Добавляем различные типы ценных бумаг
    securities = [
        # Акции российских компаний
        Security(id=1, secid="SBER", name="Сбербанк"),
        Security(id=2, secid="GAZP", name="Газпром"),
        Security(id=3, secid="YNDX", name="Яндекс"),
        Security(id=4, secid="MAIL", name="VK"),
        
        # Российские облигации
        Security(id=5, secid="SU26238RMFS2", name="ОФЗ 26238"),
        Security(id=6, secid="SU24019RMFS4", name="ОФЗ 24019"),
        Security(id=7, secid="RU000A0JX0J2", name="СБЕР Банк БО-001P"),
        
        # ETF
        Security(id=8, secid="TMOS", name="ТИНЬКОФФ iMOEX ETF"),
        Security(id=9, secid="SBMX", name="СБЕР - MOEX Russia Index ETF"),
    ]
    
    for security in securities:
        dm.add_security(security)
    
    # Добавляем позиции для разных портфелей
    positions = [
        # Консервативный портфель (больше облигаций)
        Position(id=1, portfolio_id=1, secid="SBER", quantity=Decimal("50"), avg_price=Decimal("250.00")),
        Position(id=2, portfolio_id=1, secid="SU26238RMFS2", quantity=Decimal("100"), avg_price=Decimal("950.00")),
        Position(id=3, portfolio_id=1, secid="SU24019RMFS4", quantity=Decimal("50"), avg_price=Decimal("1000.00")),
        
        # Агрессивный портфель (больше акций)
        Position(id=4, portfolio_id=2, secid="YNDX", quantity=Decimal("10"), avg_price=Decimal("3500.00")),
        Position(id=5, portfolio_id=2, secid="MAIL", quantity=Decimal("100"), avg_price=Decimal("800.00")),
        Position(id=6, portfolio_id=2, secid="GAZP", quantity=Decimal("200"), avg_price=Decimal("180.00")),
        
        # Сбалансированный портфель
        Position(id=7, portfolio_id=3, secid="TMOS", quantity=Decimal("1000"), avg_price=Decimal("150.00")),
        Position(id=8, portfolio_id=3, secid="SBMX", quantity=Decimal("500"), avg_price=Decimal("200.00")),
        Position(id=9, portfolio_id=3, secid="RU000A0JX0J2", quantity=Decimal("20"), avg_price=Decimal("1050.00")),
    ]
    
    for position in positions:
        dm.add_position(position)
    
    # Добавляем актуальные котировки
    current_time = datetime.now()
    quotes = [
        Quote(id=1, secid="SBER", timestamp=current_time, price=Decimal("255.75")),
        Quote(id=2, secid="GAZP", timestamp=current_time, price=Decimal("185.20")),
        Quote(id=3, secid="YNDX", timestamp=current_time, price=Decimal("3650.00")),
        Quote(id=4, secid="MAIL", timestamp=current_time, price=Decimal("750.50")),
        Quote(id=5, secid="SU26238RMFS2", timestamp=current_time, price=Decimal("975.50")),
        Quote(id=6, secid="SU24019RMFS4", timestamp=current_time, price=Decimal("1025.00")),
        Quote(id=7, secid="RU000A0JX0J2", timestamp=current_time, price=Decimal("1080.00")),
        Quote(id=8, secid="TMOS", timestamp=current_time, price=Decimal("148.75")),
        Quote(id=9, secid="SBMX", timestamp=current_time, price=Decimal("205.50")),
    ]
    
    for quote in quotes:
        dm.add_quote(quote)
    
    return dm


@pytest.fixture(scope="function")
def edge_case_portfolio_data(clean_data_manager):
    """Фикстура с граничными случаями данных"""
    dm = clean_data_manager
    
    # Портфель с экстремальными данными
    portfolio = Portfolio(id=1, name="Edge Case Portfolio")
    dm.add_portfolio(portfolio)
    
    # Ценные бумаги с различными характеристиками
    securities = [
        Security(id=1, secid="TEST1", name="Test Security 1"),  # Обычная
        Security(id=2, secid="VERYLONGSECID123456", name="Very Long Security Name That Exceeds Normal Length"),  # Длинное название
        Security(id=3, secid="X", name="X"),  # Короткое название
        Security(id=4, secid="ZERO", name="Zero Price Security"),  # Для тестирования нулевых цен
    ]
    
    for security in securities:
        dm.add_security(security)
    
    # Позиции с граничными значениями
    positions = [
        # Очень большое количество
        Position(id=1, portfolio_id=1, secid="TEST1", quantity=Decimal("999999999.99"), avg_price=Decimal("0.01")),
        
        # Очень маленькое количество
        Position(id=2, portfolio_id=1, secid="VERYLONGSECID123456", quantity=Decimal("0.001"), avg_price=Decimal("1000000.00")),
        
        # Нулевое количество
        Position(id=3, portfolio_id=1, secid="X", quantity=Decimal("0"), avg_price=Decimal("100.00")),
        
        # Отрицательное количество (короткая позиция)
        Position(id=4, portfolio_id=1, secid="ZERO", quantity=Decimal("-100"), avg_price=Decimal("50.00")),
    ]
    
    for position in positions:
        dm.add_position(position)
    
    # Котировки с граничными значениями
    quotes = [
        Quote(id=1, secid="TEST1", timestamp=datetime.now(), price=Decimal("1000000.00")),  # Очень высокая цена
        Quote(id=2, secid="VERYLONGSECID123456", timestamp=datetime.now(), price=Decimal("0.001")),  # Очень низкая цена
        Quote(id=3, secid="X", timestamp=datetime.now(), price=Decimal("100.00")),  # Обычная цена
        Quote(id=4, secid="ZERO", timestamp=datetime.now(), price=Decimal("45.00")),  # Цена для короткой позиции
    ]
    
    for quote in quotes:
        dm.add_quote(quote)
    
    return dm


@pytest.fixture(scope="function")
def reporting_service_with_sample_data(sample_portfolio_data):
    """ReportingService с базовыми тестовыми данными"""
    return ReportingService(sample_portfolio_data)


@pytest.fixture(scope="function")
def reporting_service_with_diversified_data(diversified_portfolio_data):
    """ReportingService с разнообразными тестовыми данными"""
    return ReportingService(diversified_portfolio_data)


@pytest.fixture(scope="function")
def reporting_service_with_edge_cases(edge_case_portfolio_data):
    """ReportingService с граничными случаями данных"""
    return ReportingService(edge_case_portfolio_data)


@pytest.fixture(scope="session")
def expected_calculations():
    """Ожидаемые результаты расчетов для валидации"""
    return {
        "portfolio_1": {
            "sber": {
                "market_value": Decimal("26050.00"),  # 100 * 260.50
                "pnl": Decimal("1050.00"),  # (260.50 - 250.00) * 100
                "pnl_percent": 4.2  # 1050 / 25000 * 100
            },
            "gazp": {
                "market_value": Decimal("8765.00"),  # 50 * 175.30
                "pnl": Decimal("-235.00"),  # (175.30 - 180.00) * 50
                "pnl_percent": -2.61  # -235 / 9000 * 100
            },
            "bond": {
                "market_value": Decimal("9800.00"),  # 10 * 980.00
                "pnl": Decimal("300.00"),  # (980.00 - 950.00) * 10
                "pnl_percent": 3.16  # 300 / 9500 * 100
            },
            "lkoh": {
                "market_value": Decimal("130400.00"),  # 20 * 6520.00
                "pnl": Decimal("400.00"),  # (6520.00 - 6500.00) * 20
                "pnl_percent": 0.31  # 400 / 130000 * 100
            },
            "total": {
                "market_value": Decimal("175015.00"),
                "total_pnl": Decimal("1515.00"),
                "assets_count": 4
            }
        }
    }


# Константы для тестов
TEST_CONSTANTS = {
    "DEFAULT_PORTFOLIO_ID": 1,
    "NONEXISTENT_PORTFOLIO_ID": 999,
    "REPORTS_DIR": "reports",
    "PDF_FILENAME_PATTERN": r"report_\d{4}-\d{2}-\d{2}\.pdf",
    "API_PREFIX": "/api/v1",
    "JSON_CONTENT_TYPE": "application/json"
}
