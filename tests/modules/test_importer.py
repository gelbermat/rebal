"""Тесты для модуля importer"""

import pytest
from unittest.mock import Mock, patch

from app.modules.importer import models, schemas, service
from app.modules.importer.models import SecurityPosition, BrokerStatement


class TestSecurityPosition:
    """Тесты для модели SecurityPosition"""
    
    def test_security_position_creation(self):
        """Тест создания SecurityPosition"""
        position = SecurityPosition(
            issuer="Сбербанк",
            security_type="акция обыкновенная",
            trading_code="SBER",
            isin="RU0009029540",
            currency="RUB",
            quantity=100
        )
        
        assert position.issuer == "Сбербанк"
        assert position.security_type == "акция обыкновенная"
        assert position.trading_code == "SBER"
        assert position.isin == "RU0009029540"
        assert position.currency == "RUB"
        assert position.quantity == 100

    def test_is_stock_property(self):
        """Тест свойства is_stock"""
        stock_position = SecurityPosition(
            issuer="Сбербанк",
            security_type="акция обыкновенная",
            trading_code="SBER",
            isin="RU0009029540",
            currency="RUB",
            quantity=100
        )
        assert stock_position.is_stock is True
        
        bond_position = SecurityPosition(
            issuer="Россия",
            security_type="облигация федерального займа",
            trading_code="SU26238RMFS6",
            isin="RU000A1038V6",
            currency="RUB", 
            quantity=10
        )
        assert bond_position.is_stock is False

    def test_is_bond_property(self):
        """Тест свойства is_bond"""
        bond_position = SecurityPosition(
            issuer="Россия",
            security_type="облигация федерального займа",
            trading_code="SU26238RMFS6",
            isin="RU000A1038V6",
            currency="RUB",
            quantity=10
        )
        assert bond_position.is_bond is True
        
        stock_position = SecurityPosition(
            issuer="Сбербанк", 
            security_type="акция обыкновенная",
            trading_code="SBER",
            isin="RU0009029540",
            currency="RUB",
            quantity=100
        )
        assert stock_position.is_bond is False

    def test_is_etf_property(self):
        """Тест свойства is_etf"""
        etf_position = SecurityPosition(
            issuer="УК Сбербанк",
            security_type="пиф",
            trading_code="SBMX",
            isin="RU000A100XX0",
            currency="RUB",
            quantity=5
        )
        assert etf_position.is_etf is True
        
        stock_position = SecurityPosition(
            issuer="Сбербанк",
            security_type="акция обыкновенная", 
            trading_code="SBER",
            isin="RU0009029540",
            currency="RUB",
            quantity=100
        )
        assert stock_position.is_etf is False


class TestBrokerStatement:
    """Тесты для модели BrokerStatement"""
    
    def test_broker_statement_creation(self):
        """Тест создания BrokerStatement"""
        positions = [
            SecurityPosition("Сбербанк", "акция обыкновенная", "SBER", "RU0009029540", "RUB", 100),
            SecurityPosition("Россия", "облигация федерального займа", "SU26238RMFS6", "RU000A1038V6", "RUB", 10)
        ]
        
        statement = BrokerStatement(
            account_number="40702810123456789012",
            positions=positions,
            statement_date="2024-01-15"
        )
        
        assert statement.account_number == "40702810123456789012"
        assert len(statement.positions) == 2
        assert statement.statement_date == "2024-01-15"

    def test_bonds_property(self):
        """Тест свойства bonds"""
        positions = [
            SecurityPosition("Сбербанк", "акция обыкновенная", "SBER", "RU0009029540", "RUB", 100),
            SecurityPosition("Россия", "облигация федерального займа", "SU26238RMFS6", "RU000A1038V6", "RUB", 10),
            SecurityPosition("ВТБ", "облигация", "RU000A0JXPU3", "RU000A0JXPU3", "RUB", 5)
        ]
        
        statement = BrokerStatement("40702810123456789012", positions)
        bonds = statement.bonds
        
        assert len(bonds) == 2
        assert all(pos.is_bond for pos in bonds)

    def test_stocks_property(self):
        """Тест свойства stocks"""
        positions = [
            SecurityPosition("Сбербанк", "акция обыкновенная", "SBER", "RU0009029540", "RUB", 100),
            SecurityPosition("Газпром", "акция", "GAZP", "RU0007661625", "RUB", 50),
            SecurityPosition("Россия", "облигация федерального займа", "SU26238RMFS6", "RU000A1038V6", "RUB", 10)
        ]
        
        statement = BrokerStatement("40702810123456789012", positions)
        stocks = statement.stocks
        
        assert len(stocks) == 2
        assert all(pos.is_stock for pos in stocks)

    def test_etfs_property(self):
        """Тест свойства etfs"""
        positions = [
            SecurityPosition("УК Сбербанк", "пиф", "SBMX", "RU000A100XX0", "RUB", 5),
            SecurityPosition("Сбербанк", "акция обыкновенная", "SBER", "RU0009029540", "RUB", 100),
            SecurityPosition("УК ВТБ", "пиф", "VTBMX", "RU000A100YY0", "RUB", 3)
        ]
        
        statement = BrokerStatement("40702810123456789012", positions)
        etfs = statement.etfs
        
        assert len(etfs) == 2
        assert all(pos.is_etf for pos in etfs)

    def test_total_positions_property(self):
        """Тест свойства total_positions"""
        positions = [
            SecurityPosition("Сбербанк", "акция обыкновенная", "SBER", "RU0009029540", "RUB", 100),
            SecurityPosition("Россия", "облигация федерального займа", "SU26238RMFS6", "RU000A1038V6", "RUB", 10),
            SecurityPosition("УК Сбербанк", "пиф", "SBMX", "RU000A100XX0", "RUB", 5)
        ]
        
        statement = BrokerStatement("40702810123456789012", positions)
        assert statement.total_positions == 3

    def test_empty_statement(self):
        """Тест пустого отчета"""
        statement = BrokerStatement("40702810123456789012", [])
        
        assert statement.total_positions == 0
        assert len(statement.bonds) == 0
        assert len(statement.stocks) == 0  
        assert len(statement.etfs) == 0


class TestImporterSchemas:
    """Тесты для схем importer"""
    
    def test_import_schemas(self):
        """Тест что схемы можно импортировать"""
        assert hasattr(schemas, '__name__')
        
    def test_schemas_module_structure(self):
        """Тест структуры модуля schemas"""
        # Проверяем что модуль загружается без ошибок
        import app.modules.importer.schemas as schemas_module
        assert schemas_module is not None


class TestImporterService:
    """Тесты для сервиса importer"""
    
    def test_import_service(self):
        """Тест что сервис можно импортировать"""
        assert hasattr(service, '__name__')
        
    def test_service_module_structure(self):
        """Тест структуры модуля service"""
        # Проверяем что модуль загружается без ошибок
        import app.modules.importer.service as service_module
        assert service_module is not None


class TestImporterAPI:
    """Тесты для API importer"""
    
    def test_import_api(self):
        """Тест что API можно импортировать"""
        from app.modules.importer import api
        assert hasattr(api, '__name__')
        
    def test_api_module_structure(self):
        """Тест структуры модуля api"""
        # Проверяем что модуль загружается без ошибок
        import app.modules.importer.api as api_module
        assert api_module is not None