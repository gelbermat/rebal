"""
Тесты для моделей всех модулей для улучшения покрытия
"""

import pytest
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any

# Импорты моделей
from app.modules.marketdata import models as marketdata_models
from app.modules.portfolio import models as portfolio_models
from app.modules.reporting import models as reporting_models
from app.modules.strategy import models as strategy_models


class TestMarketDataModels:
    """Тесты для моделей модуля marketdata"""
    
    def test_security_model_creation(self):
        """Тест создания модели Security"""
        security = marketdata_models.Security(
            secid="SBER",
            name="Сбер Банк",
            isin="RU0009029540"
        )
        
        assert security.secid == "SBER"
        assert security.name == "Сбер Банк"
        assert security.isin == "RU0009029540"
        assert security.is_active == True
        
    def test_security_model_validation(self):
        """Тест валидации модели Security"""
        # Тест с минимальными данными
        security = marketdata_models.Security(
            secid="TEST",
            name="Test Security"
        )
        
        assert security.secid == "TEST"
        assert security.name == "Test Security"
        assert security.isin is None
        assert security.is_active == True
        
    def test_security_model_equality(self):
        """Тест сравнения моделей Security"""
        security1 = marketdata_models.Security(secid="SBER", name="Сбер")
        security2 = marketdata_models.Security(secid="SBER", name="Сбер")
        security3 = marketdata_models.Security(secid="GAZP", name="Газпром")
        
        # Проверяем что объекты с одинаковыми данными равны
        assert security1.secid == security2.secid
        assert security1.name == security2.name
        assert security1.secid != security3.secid
        
    def test_quote_model_creation(self):
        """Тест создания модели Quote"""
        quote = marketdata_models.Quote(
            secid="SBER",
            timestamp=datetime.now(),
            price=Decimal("250.50"),
            volume=Decimal("1000")
        )
        
        assert quote.secid == "SBER"
        assert isinstance(quote.timestamp, datetime)
        assert quote.price == Decimal("250.50")
        assert quote.volume == Decimal("1000")
        
    def test_quote_model_decimal_handling(self):
        """Тест обработки Decimal в модели Quote"""
        # Создание с разными типами числовых данных
        quote1 = marketdata_models.Quote(
            secid="SBER", timestamp=datetime.now(),
            price=Decimal("100.50"), volume=Decimal("500")
        )
        
        quote2 = marketdata_models.Quote(
            secid="GAZP", timestamp=datetime.now(),
            price=Decimal("300.75"), volume=Decimal("1500")
        )
        
        assert isinstance(quote1.price, Decimal)
        assert isinstance(quote1.volume, Decimal)
        assert quote1.price != quote2.price
        assert quote1.volume != quote2.volume


class TestPortfolioModels:
    """Тесты для моделей модуля portfolio"""
    
    def test_portfolio_model_creation(self):
        """Тест создания модели Portfolio"""
        portfolio = portfolio_models.Portfolio(
            id=1,
            name="My Portfolio",
            description="Test portfolio for unit tests"
        )
        
        assert portfolio.id == 1
        assert portfolio.name == "My Portfolio"
        assert portfolio.description == "Test portfolio for unit tests"
        
    def test_portfolio_model_without_description(self):
        """Тест создания модели Portfolio без описания"""
        portfolio = portfolio_models.Portfolio(
            id=1,
            name="Simple Portfolio"
        )
        
        assert portfolio.id == 1
        assert portfolio.name == "Simple Portfolio"
        assert portfolio.description is None
        
    def test_position_model_creation(self):
        """Тест создания модели Position"""
        position = portfolio_models.Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=100
        )
        
        assert position.id == 1
        assert position.portfolio_id == 1
        assert position.secid == "SBER"
        assert position.quantity == 100
        
    def test_position_model_negative_quantity(self):
        """Тест создания модели Position с отрицательным количеством"""
        position = portfolio_models.Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=-50  # Короткая позиция
        )
        
        assert position.quantity == -50
        
    def test_position_model_zero_quantity(self):
        """Тест создания модели Position с нулевым количеством"""
        position = portfolio_models.Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=0
        )
        
        assert position.quantity == 0


class TestReportingModels:
    """Тесты для моделей модуля reporting"""
    
    def test_transaction_model_creation(self):
        """Тест создания модели Transaction"""
        transaction = reporting_models.Transaction(
            id=1,
            portfolio_id=1,
            secid="SBER",
            transaction_type="buy",
            quantity=Decimal("100"),
            price=Decimal("250.00"),
            timestamp=datetime.now()
        )
        
        assert transaction.id == 1
        assert transaction.portfolio_id == 1
        assert transaction.secid == "SBER"
        assert transaction.transaction_type == "buy"
        assert transaction.quantity == Decimal("100")
        assert transaction.price == Decimal("250.00")
        assert isinstance(transaction.timestamp, datetime)
        
    def test_transaction_sell_model(self):
        """Тест создания модели Transaction для продажи"""
        transaction = reporting_models.Transaction(
            id=2,
            portfolio_id=1,
            secid="GAZP",
            transaction_type="sell",
            quantity=Decimal("50"),
            price=Decimal("300.50"),
            timestamp=datetime.now()
        )
        
        assert transaction.transaction_type == "sell"
        assert transaction.quantity == Decimal("50")
        
    def test_transaction_model_calculations(self):
        """Тест вычислений в модели Transaction"""
        transaction = reporting_models.Transaction(
            id=1,
            portfolio_id=1,
            secid="SBER",
            transaction_type="buy",
            quantity=Decimal("100"),
            price=Decimal("250.00"),
            timestamp=datetime.now()
        )
        
        # Проверяем что можем вычислить общую сумму
        total_amount = transaction.quantity * transaction.price
        assert total_amount == Decimal("25000.00")


class TestStrategyModels:
    """Тесты для моделей модуля strategy"""
    
    def test_strategy_config_model_creation(self):
        """Тест создания модели StrategyConfig"""
        config = strategy_models.StrategyConfig(
            strategy_type=strategy_models.StrategyType.LAZY_INDEX_TRACKING,
            parameters={"target_weights": {"SBER": 0.6, "GAZP": 0.4}},
            min_transaction_amount=Decimal("1000"),
            max_weight_deviation=Decimal("0.05")
        )
        
        assert config.strategy_type == strategy_models.StrategyType.LAZY_INDEX_TRACKING
        assert "target_weights" in config.parameters
        assert config.min_transaction_amount == Decimal("1000")
        assert config.max_weight_deviation == Decimal("0.05")
        
    def test_strategy_config_validation(self):
        """Тест валидации модели StrategyConfig"""
        # Проверяем что веса в сумме дают 1.0
        weights = {"SBER": 0.5, "GAZP": 0.3, "LKOH": 0.2}
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001
        
        config = strategy_models.StrategyConfig(
            strategy_type=strategy_models.StrategyType.LAZY_INDEX_TRACKING,
            parameters={"target_weights": weights},
            rebalance_threshold=Decimal("0.02")
        )
        
        assert len(config.parameters["target_weights"]) == 3
        
    def test_rebalance_result_model_creation(self):
        """Тест создания модели RebalanceResult"""
        result = strategy_models.RebalanceResult(
            portfolio_id=1,
            strategy_type=strategy_models.StrategyType.LAZY_INDEX_TRACKING,
            current_total_value=Decimal("100000"),
            target_total_value=Decimal("105000"),
            cash_required=Decimal("5000"),
            recommendations=[],
            total_transactions=0,
            estimated_total_cost=Decimal("0")
        )
        
        assert result.portfolio_id == 1
        assert result.strategy_type == strategy_models.StrategyType.LAZY_INDEX_TRACKING
        assert result.current_total_value == Decimal("100000")
        assert result.total_transactions == 0


class TestModelsIntegration:
    """Интеграционные тесты моделей"""
    
    def test_models_with_relationships(self):
        """Тест моделей с связями"""
        # Создаем связанные объекты
        security = marketdata_models.Security(
            id=1, secid="SBER", name="Сбер Банк"
        )
        
        portfolio = portfolio_models.Portfolio(
            id=1, name="Test Portfolio"
        )
        
        position = portfolio_models.Position(
            id=1,
            portfolio_id=portfolio.id,
            secid=security.secid,
            quantity=100
        )
        
        # Проверяем связи
        assert position.portfolio_id == portfolio.id
        assert position.secid == security.secid
        
    def test_models_data_consistency(self):
        """Тест консистентности данных между моделями"""
        # Создаем транзакцию и позицию для одного портфеля
        transaction = reporting_models.Transaction(
            id=1,
            portfolio_id=1,
            secid="SBER",
            transaction_type="buy",
            quantity=Decimal("100"),
            price=Decimal("250.00"),
            timestamp=datetime.now()
        )
        
        position = portfolio_models.Position(
            id=1,
            portfolio_id=1,
            secid="SBER", 
            quantity=100
        )
        
        # Проверяем консистентность
        assert transaction.portfolio_id == position.portfolio_id
        assert transaction.secid == position.secid
        assert float(transaction.quantity) == position.quantity


class TestModelsValidation:
    """Тесты валидации моделей"""
    
    def test_security_required_fields(self):
        """Тест обязательных полей Security"""
        # Минимальный набор полей
        security = marketdata_models.Security(
            secid="TEST",
            name="Test"
        )
        
        assert security.secid is not None
        assert security.name is not None
        assert security.is_active == True
        
    def test_portfolio_required_fields(self):
        """Тест обязательных полей Portfolio"""
        portfolio = portfolio_models.Portfolio(
            id=1,
            name="Required Name"
        )
        
        assert portfolio.id is not None
        assert portfolio.name is not None
        
    def test_position_required_fields(self):
        """Тест обязательных полей Position"""
        position = portfolio_models.Position(
            id=1,
            portfolio_id=1,
            secid="SBER",
            quantity=0
        )
        
        assert position.id is not None
        assert position.portfolio_id is not None
        assert position.secid is not None
        assert position.quantity is not None
        
    def test_transaction_required_fields(self):
        """Тест обязательных полей Transaction"""
        transaction = reporting_models.Transaction(
            id=1,
            portfolio_id=1,
            secid="SBER",
            transaction_type="buy",
            quantity=Decimal("100"),
            price=Decimal("250.00"),
            timestamp=datetime.now()
        )
        
        assert transaction.id is not None
        assert transaction.portfolio_id is not None
        assert transaction.secid is not None
        assert transaction.transaction_type is not None
        assert transaction.quantity is not None
        assert transaction.price is not None
        assert transaction.timestamp is not None


class TestModelsEdgeCases:
    """Тесты граничных случаев для моделей"""
    
    def test_large_numbers(self):
        """Тест с большими числами"""
        large_quantity = Decimal("999999999.99")
        large_price = Decimal("1000000.00")
        
        transaction = reporting_models.Transaction(
            id=1,
            portfolio_id=1,
            secid="EXPENSIVE",
            transaction_type="buy",
            quantity=large_quantity,
            price=large_price,
            timestamp=datetime.now()
        )
        
        assert transaction.quantity == large_quantity
        assert transaction.price == large_price
        
    def test_very_small_numbers(self):
        """Тест с очень маленькими числами"""
        small_quantity = Decimal("0.000001")
        small_price = Decimal("0.01")
        
        transaction = reporting_models.Transaction(
            id=1,
            portfolio_id=1,
            secid="MICRO",
            transaction_type="buy",
            quantity=small_quantity,
            price=small_price,
            timestamp=datetime.now()
        )
        
        assert transaction.quantity == small_quantity
        assert transaction.price == small_price
        
    def test_unicode_strings(self):
        """Тест с Unicode строками"""
        security = marketdata_models.Security(
            id=1,
            secid="SBER",
            name="Сбербанк России 🏦",
            isin="RU0009029540"
        )
        
        assert "🏦" in security.name
        assert security.name == "Сбербанк России 🏦"
        
    def test_long_strings(self):
        """Тест с длинными строками"""
        long_description = "A" * 1000  # 1000 символов
        
        portfolio = portfolio_models.Portfolio(
            id=1,
            name="Portfolio with long description",
            description=long_description
        )
        
        assert len(portfolio.description) == 1000
        assert portfolio.description == long_description


class TestModelsStringRepresentation:
    """Тесты строкового представления моделей"""
    
    def test_security_str(self):
        """Тест строкового представления Security"""
        security = marketdata_models.Security(
            id=1, secid="SBER", name="Сбербанк"
        )
        
        # Проверяем что можем получить строковое представление
        str_repr = str(security)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0
        
    def test_portfolio_str(self):
        """Тест строкового представления Portfolio"""
        portfolio = portfolio_models.Portfolio(
            id=1, name="My Portfolio"
        )
        
        str_repr = str(portfolio)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0
        
    def test_position_str(self):
        """Тест строкового представления Position"""
        position = portfolio_models.Position(
            id=1, portfolio_id=1, secid="SBER", quantity=100
        )
        
        str_repr = str(position)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0